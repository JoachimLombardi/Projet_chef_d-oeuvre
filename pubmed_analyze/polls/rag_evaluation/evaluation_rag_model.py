import json
import re
from elasticsearch_dsl import Search
from polls.models import Article
from polls.utils import text_processing
from polls.business_logic import model, rank_doc, reciprocal_rank_fusion
import ollama
from pathlib import Path
from django.conf import settings
from polls.es_config import INDEX_NAME


def create_eval_rag_json(query, expected_abstract):
    output_path = Path(settings.RAG_JSON_DIR + "/" + "eval_rag.json")
    evaluation_data = {
        'query': re.sub(r'\s+', ' ', query).replace('\n', ' '),
        'expected_abstract': re.sub(r'\s+', ' ', expected_abstract).replace('\n', ' '),
    }
    # If the file already exists, load its content
    if output_path.exists():
        with output_path.open('r', encoding='utf-8') as f:
            existing_data = json.load(f)
    else:
        existing_data = []
    # Add the new evaluation data
    existing_data.append(evaluation_data)
    # Write updated data to the file
    with output_path.open('w', encoding='utf-8') as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=4)
    print(f"Saved evaluation to {output_path}")


def search_articles_for_eval(query, research_type, number_of_results, number_of_articles, title_weight, abstract_weight, rank_scaling_factor):
    query_cleaned = text_processing(query)
    query_vector = model.encode(query_cleaned).tolist() 
    if research_type == 'hybrid' or research_type == 'neural':
        search_results_vector = Search(index=INDEX_NAME).query(
        "knn",
        field="title_abstract_vector",
        query_vector=query_vector,
        k=number_of_results,
        num_candidates=number_of_articles
        ).source(['title', 'abstract']) # Include the 'title' and 'abstract' fields in the response
        response_vector = search_results_vector.execute()
    if research_type == 'hybrid' or research_type == 'text':
        search_results_text = Search(index=INDEX_NAME).query(
        "multi_match",
        fields=[f'title^{title_weight}', f'abstract^{abstract_weight}'],
        query=query_cleaned,
        type="best_fields",
        ).source(['title', 'abstract']) 
        response_text = search_results_text[0:number_of_results].execute()
    if research_type == 'hybrid':
        # hybrid search
        retrieved_docs = reciprocal_rank_fusion(response_vector.hits, response_text.hits, k=rank_scaling_factor)
    elif research_type == 'neural':
        retrieved_docs = response_vector.hits
    elif research_type == 'text':
        retrieved_docs = response_text.hits
    # rerank
    response = rank_doc(query_cleaned, retrieved_docs, 3)
    # Prepare results for JSON response
    results = []
    article_ids = [res['id'] for res in response]  # Gather all article IDs for a single query
    articles = Article.objects.filter(id__in=article_ids).prefetch_related('authorships__author', 'authorships__affiliation')
    # Process the search hits and build the results list
    for res in response:
        article_id = int(res['id'])
        title = res['title']
        abstract = res['abstract']
        # Get the article from the pre-fetched queryset
        article = next((art for art in articles if art.id == article_id), None)
        if article:
            # Add article details to results
            results.append({
                'title': title,
                'abstract': abstract            
                })
    return results, query


def rag_articles_for_eval(query, research_type, number_of_results, model, number_of_articles=None, title_weight=None, abstract_weight=None, rank_scaling_factor=None):
    retrieved_documents, query = search_articles_for_eval(query, research_type, number_of_results, number_of_articles, title_weight, abstract_weight, rank_scaling_factor)
    context = ""
    for i, source in enumerate(retrieved_documents):
        context += f"Abstract n°{i+1}:" + source['title'] + "." + "\n\n" + source['abstract'] + "\n\n"
    template = """You are an expert in analysing medical abstract and your are talking to a pannel of medical experts. Your task is to use only provided context to answer at best the query.
    If you don't know or if the answer is not in the provided context just say: "I can't answer with the provide context".

        ## Instruction:\n
        1. Read carefully the query and look in all extract for the answer.
      
        ## Query:\n
        '"""+query+"""'

        ## Context:\n
        '"""+context+"""'

        All your responses must be structured and only based on the context given.
        """
    messages = [{"role":"user", "content":template}]
    chat_response = ollama.chat(model=model,
                                messages=messages,
                                options={"temperature": 0})
    return chat_response['message']['content'], retrieved_documents


def eval_retrieval(query, retrieved_documents, expected_abstracts):
    model = "mistral-small"
    template = """You are an expert in medical abstracts. 
    You will receive two medical abstracts and a query. Your task is to determine which of these abstracts contains the most pertinent information to answer the query.     
    You must return the number of the abstract containing the most relevant information. If the two abstracts contain the same information, return number 1.

    ## Query:\n
    '"""+query+"""'

    ## Abstract 1:\n
    '"""+retrieved_documents+"""'

    ## Abstract 2:\n
    '"""+expected_abstracts+"""'
     
    ## Expected output:\n
    {
    "number": int
    }
    Your must provide a valid JSON.
    """
    messages = [{"role":"user", "content":template}]
    chat_response = ollama.chat(model=model,
                                messages=messages,
                                options={"temperature": 0})
    output = chat_response['message']['content']
    pattern = r'\{+.*\}'
    match = re.findall(pattern, output, re.DOTALL)[0]
    number = json.loads(match)['number']
    return number


def eval_response(query, response):
    model = "mistral-small"
    template = """You are an expert in evaluating llm responses. 
    You will receive a query and a response generated by a language model. Your task is to compare query to the response and determine the quality of the response.
    Please provide a quality score on a scale from 0 to 1, where:
    0 means "not answer the query at all",
    1 means "answer perfectly relevant to the query".

    ## Query:\n
    '"""+query+"""'

    ## Response:\n
    '"""+response+"""'

    ## Expected output:\n
    {
    "score": score
    }
    Your must provide a valid JSON.
    """
    messages = [{"role":"user", "content":template}]
    chat_response = ollama.chat(model=model,
                                messages=messages,
                                options={"temperature": 0})
    output = chat_response['message']['content']
    pattern = r'\{+.*\}'
    match = re.findall(pattern, output, re.DOTALL)[0]
    score = json.loads(match)['score']
    return float(score)


    
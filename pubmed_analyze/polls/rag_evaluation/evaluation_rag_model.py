import json
import re
from elasticsearch_dsl import Search
from polls.models import Article
from polls.utils import query_processing, model, rank_doc
import ollama
from pathlib import Path
from django.conf import settings
from .file_eval_json import queries, expected_abstracts


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


def search_articles(query):
    # Process the query
    query_cleaned = query_processing(query)
    # Encode the search query into a vector
    query_vector = model.encode(query_cleaned).tolist() 
    search_results = Search(index="multiple_sclerosis_2024").query(
    "knn",
    field="title_abstract_vector",
    query_vector=query_vector,
    k=20,
    num_candidates=5000
    ).source(['title', 'abstract']) # Include the 'title' and 'abstract' fields in the response
    # Execute the search
    response = search_results.execute()
    # rerank
    retrieved_docs = [{"id":hit.meta.id, "title":hit.title, "abstract":hit.abstract} for hit in response.hits]
    response = rank_doc(query_cleaned, retrieved_docs, 5)
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


def rag_articles(query="How did the COVID-19 pandemic impact the care of people with multiple sclerosis (PwMS)?"):
    retrieved_documents, query = search_articles(query)
    context = ""
    for i, source in enumerate(retrieved_documents):
        context += f"Abstract n°{i+1}:" + source['title'] + "." + "\n\n" + source['abstract'] + "\n\n"
    model = "mistral"
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
    chat_response = ollama.chat(
    model=model,
    messages=messages)
    return chat_response['message']['content'], retrieved_documents


def eval_retrieval(query, retrieved_documents, expected_abstracts):
    model = "mistral"
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
    chat_response = ollama.chat(
    model=model,
    messages=messages)
    output = chat_response['message']['content']
    pattern = r'\{+.*\}'
    match = re.findall(pattern, output, re.DOTALL)[0]
    number = json.loads(match)['number']
    return number


def eval_response(query, response):
    model = "mistral"
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
    chat_response = ollama.chat(
    model=model,
    messages=messages)
    output = chat_response['message']['content']
    pattern = r'\{+.*\}'
    match = re.findall(pattern, output, re.DOTALL)[0]
    score = json.loads(match)['score']
    return float(score)


def evaluate_rag(queries=queries, expected_abstracts=expected_abstracts):
    output_path = Path(settings.RAG_JSON_DIR + "/" + "eval_rag.json")
    if not output_path.exists():
        for query, expected_abstract in zip(queries, expected_abstracts):
            create_eval_rag_json(query, expected_abstract)
    output_path = Path(settings.RAG_JSON_DIR + "/" + "eval_rag.json")
    with output_path.open( 'r', encoding='utf-8') as f:
        evaluation_data = json.load(f)
    queries = [data['query'] for data in evaluation_data]
    expected_abstracts = [data['expected_abstract'] for data in evaluation_data]
    score_retrieval = 0
    score_generation_list = []
    eval_rag_list = []
    for query, expected_abstract in zip(queries, expected_abstracts):
        response, retrieved_documents = rag_articles(query)
        number = eval_retrieval(query, retrieved_documents[0]["abstract"], expected_abstract)
        if number == 1:
            score_retrieval += 0.1
        score_generation_list.append(eval_response(query, response))
        eval_rag = {}
        eval_rag["query"] = query
        eval_rag["expected_abstract"] = expected_abstract
        eval_rag["found_abstract"] = retrieved_documents[0]["abstract"]
        eval_rag["response"] = response
        eval_rag_list.append(eval_rag)
    score_generation = round(sum(score_generation_list)/len(score_generation_list), 2)
    eval_rag = {}
    eval_rag["score_retrieval"] = score_retrieval
    eval_rag["score_generation"] = score_generation
    eval_rag_list.append(eval_rag)
    output_path = Path(settings.RAG_JSON_DIR + "/" + "results_eval_rag.json")
    with output_path.open('w', encoding='utf-8') as f:
        json.dump(eval_rag_list, f, ensure_ascii=False, indent=4)
    return score_generation, score_retrieval
    
import json
import re
from elasticsearch_dsl import Search
from polls.models import Article
from polls.utils import query_processing, model, rank_doc
import ollama
from pathlib import Path
from django.conf import settings
from .file_eval_json import queries, expected_abstracts, expected_response


def create_eval_rag_json(query, expected_abstract, expected_response):
    output_path = Path(settings.RAG_JSON_DIR + "/" + "eval_rag.json")
    evaluation_data = {
        'query': re.sub(r'\s+', ' ', query).replace('\n', ' '),
        'expected_abstract': re.sub(r'\s+', ' ', expected_abstract).replace('\n', ' '),
        'expected_response': re.sub(r'\s+', ' ', expected_response).replace('\n', ' ')
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
    k=5,
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
        score = res['score']
        title = res['title']
        abstract = res['abstract']
        # Get the article from the pre-fetched queryset
        article = next((art for art in articles if art.id == article_id), None)
        if article:
            # Retrieve authors and their affiliations
            affiliations_by_author = {}
            for authorship in article.authorships.all():
                author_name = authorship.author.name
                affiliation_name = authorship.affiliation.name
                # Avoid duplicates by using a set
                if author_name not in affiliations_by_author:
                    affiliations_by_author[author_name] = set()
                affiliations_by_author[author_name].add(affiliation_name)
            # Prepare data for authors and affiliations
            authors_affiliations = [
                {
                    'author_name': author,
                    'affiliations': '| '.join(affiliations)  # Join affiliations into a single string
                }
                for author, affiliations in affiliations_by_author.items()
            ]
            # Add article details to results
            results.append({
                'id': article_id,
                'score': score,
                'title': title,
                'abstract': abstract,
                'authors_affiliations': authors_affiliations
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


def eval_response(response, expected_response):
    model = "mistral"
    template = """You are an expert in evaluating llm responses. 
    You will receive two responses generated by a language model. Your task is to compare these two responses and determine their degree of similarity. 
    Please provide a similarity score on a scale from 0 to 1, where:
    0 means "not similar at all" (the responses are completely different),
    1 means "very similar" (the responses are almost identical).

    ## Response 1:\n
    '"""+response+"""'

    ## Response 2:\n
    '"""+expected_response+"""'

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


def evaluate_rag(queries=queries, expected_abstracts=expected_abstracts, expected_responses=expected_response):
    output_path = Path(settings.RAG_JSON_DIR + "/" + "eval_rag.json")
    if not output_path.exists():
        for query, expected_abstract, expected_response in zip(queries, expected_abstracts, expected_responses):
            create_eval_rag_json(query, expected_abstract, expected_response)
    output_path = Path(settings.RAG_JSON_DIR + "/" + "eval_rag.json")
    with output_path.open( 'r', encoding='utf-8') as f:
        evaluation_data = json.load(f)
    queries = [data['query'] for data in evaluation_data]
    expected_abstracts = [data['expected_abstract'] for data in evaluation_data]
    expected_responses = [data['expected_response'] for data in evaluation_data]
    score_retrieval = 0
    score_generation_list = []
    eval_rag_list = []
    for query, expected_abstract, expected_response in zip(queries, expected_abstracts, expected_responses):
        response, retrieved_documents = rag_articles(query)
        if retrieved_documents[0]["abstract"] == expected_abstract:
            score_retrieval += 0.1
        score_generation_list.append(eval_response(response, expected_response))
        eval_rag = {}
        eval_rag["query"] = query
        eval_rag["expected_abstract"] = expected_abstract
        eval_rag["response"] = expected_response
        eval_rag_list.append(eval_rag)
    score_generation = sum(score_generation_list)/len(score_generation_list)
    eval_rag = {}
    eval_rag["score_retrieval"] = score_retrieval
    eval_rag["score_generation"] = score_generation
    eval_rag_list.append(eval_rag)
    output_path = Path(settings.RAG_JSON_DIR + "/" + "results_eval_rag.json")
    with output_path.open('w', encoding='utf-8') as f:
        json.dump(eval_rag_list, f, ensure_ascii=False, indent=4)
    return score_generation, score_retrieval
    
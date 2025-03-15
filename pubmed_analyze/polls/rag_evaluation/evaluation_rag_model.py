import json
import os
import re
from elasticsearch_dsl import Search
import numpy as np
import requests
from polls.models import Article
from polls.utils import text_processing
from polls.business_logic import model, rank_doc, reciprocal_rank_fusion
from pathlib import Path
from django.conf import settings
from polls.es_config import INDEX_NAME
from openai import OpenAI
from polls.utils import error_handling
import matplotlib.pyplot as plt


@error_handling
def create_eval_rag_json(query, expected_abstract):
    """
    Creates a JSON file in settings.RAG_JSON_DIR with the evaluation data for the given query and expected abstract.
    
    The JSON file will contain the query and expected abstract, stripped of leading and trailing whitespace and with consecutive whitespace characters merged into a single space.
    
    If the file already exists, the new evaluation data will be appended to the existing list.
    
    :param query: The query to evaluate
    :param expected_abstract: The expected abstract for the given query
    :return: None
    """
    output_path = Path(settings.RAG_JSON_DIR + "/" + "eval_rag.json")
    evaluation_data = {
        'query': re.sub(r'\s+', ' ', query).replace('\n', ' '),
        'expected_abstract': re.sub(r'\s+', ' ', expected_abstract).replace('\n', ' '),
    }
    if output_path.exists():
        with output_path.open('r', encoding='utf-8') as f:
            existing_data = json.load(f)
    else:
        existing_data = []
    existing_data.append(evaluation_data)
    with output_path.open('w', encoding='utf-8') as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=4)
    print(f"Saved evaluation to {output_path}")


@error_handling
def search_articles_for_eval(query, research_type, number_of_results, number_of_articles, title_weight, abstract_weight, rank_scaling_factor):
    """
    Search articles in the database with a query using the given research type, number of results, number of articles, title weight, abstract weight, and rank scaling factor.
    
    This function takes a query string, research type, number of results, number of articles, title weight, abstract weight, and rank scaling factor, and returns a list of search results, where each result is a dictionary containing the title and abstract of the article.
    
    The research type can be one of 'hybrid', 'neural', or 'text'. If 'hybrid', the function will use both the vector and text searches. If 'neural', the function will only use the vector search. If 'text', the function will only use the text search.
    
    The function will also return the query string, which can be used to generate an evaluation JSON file.
    
    :param query: The query string to search for.
    :param research_type: The research type to use. Can be 'hybrid', 'neural', or 'text'.
    :param number_of_results: The number of results to return.
    :param number_of_articles: The number of articles to search in.
    :param title_weight: The weight to give to the title in the text search.
    :param abstract_weight: The weight to give to the abstract in the text search.
    :param rank_scaling_factor: The rank scaling factor to use in the reciprocal rank fusion.
    :return: A list of search results, where each result is a dictionary containing the title and abstract of the article, and the query string.
    """
    query_cleaned = text_processing(query)
    query_vector = model.encode(query_cleaned).tolist() 
    if research_type == 'hybrid' or research_type == 'neural':
        search_results_vector = Search(index=INDEX_NAME).query(
        "knn",
        field="title_abstract_vector",
        query_vector=query_vector,
        k=number_of_results,
        num_candidates=number_of_articles
        ).source(['title', 'abstract']) 
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
        retrieved_docs = reciprocal_rank_fusion(response_vector.hits, response_text.hits, k=rank_scaling_factor)
    elif research_type == 'neural':
        retrieved_docs = response_vector.hits
    elif research_type == 'text':
        retrieved_docs = response_text.hits
    response = rank_doc(query_cleaned, retrieved_docs, 3)
    results = []
    article_ids = [res['id'] for res in response]  
    articles = Article.objects.filter(id__in=article_ids).prefetch_related('authorships__author', 'authorships__affiliation')
    for res in response:
        article_id = int(res['id'])
        title = res['title']
        abstract = res['abstract']
        article = next((art for art in articles if art.id == article_id), None)
        if article:
            results.append({
                'title': title,
                'abstract': abstract            
                })
    return results, query


@error_handling
def rag_articles_for_eval(query, research_type, number_of_results, model, number_of_articles=None, title_weight=None, abstract_weight=None, rank_scaling_factor=None):
    """
    Retrieves articles for evaluation based on a query and constructs a context for model evaluation.

    This function searches for articles using the provided query and search parameters, constructs
    a context string by concatenating titles and abstracts of the retrieved documents, and prepares
    a template to prompt a model for generating a response to the query. The response and context
    are returned for further evaluation.

    :param query: The query string used to search for articles.
    :param research_type: The type of research to conduct. Can be 'hybrid', 'neural', or 'text'.
    :param number_of_results: The number of top results to retrieve.
    :param model: The model used for generating the response.
    :param number_of_articles: (Optional) Number of articles to consider in the search.
    :param title_weight: (Optional) The weight given to the title in the search.
    :param abstract_weight: (Optional) The weight given to the abstract in the search.
    :param rank_scaling_factor: (Optional) The rank scaling factor for reciprocal rank fusion.
    :return: A tuple containing the response generated by the model, the retrieved documents, 
             and the constructed context string.
    """

    retrieved_documents, query = search_articles_for_eval(query, research_type, number_of_results, number_of_articles, title_weight, abstract_weight, rank_scaling_factor)
    print(retrieved_documents)
    context = ""
    for i, source in enumerate(retrieved_documents):
        context += f"Abstract n°{i+1}:" + source['title'] + "." + "\n\n" + source['abstract'] + "\n\n"
    template = """You are an expert in analysing medical abstract and your are talking to a pannel of medical experts. Your task is to use only provided context to answer at best the query.
    If you don't know or if the answer is not in the provided context just return: "response": "I can't answer with the provide context".

        ## Instruction:\n
        1. Read carefully the query and look in all extract for the answer.
      
        ## Query:\n
        '"""+query+"""'

        ## Context:\n
        '"""+context+"""'

        ## Expected Answer:\n
            {
            "response": str
            }

        You must provid a valid JSON with the key "response".
    """
    data = {
        "model": model,
        "messages": [{"role": "user", "content": template}],
        "stream": False,
        "format": "json",
        "options": {
            "seed": 101,
            "temperature": 0
        }
    }
    chat_response = requests.post('http://ollama:11434/api/chat', json=data).json()
    print("Chat response:", chat_response, flush=True)
    output = chat_response['message']['content']
    print(output, flush=True)
    pattern = r'\{+.*\}'
    match = re.findall(pattern, output, re.DOTALL)[0]
    match = match.replace("\n", '')
    if match:
        response = json.loads(match)['response']
    return response, retrieved_documents, context


@error_handling
def eval_retrieval(query, retrieved_documents, expected_abstracts, model):
    """
    Evaluate the relevance of a list of retrieved documents given a query and the expected abstract.

    Parameters:
    query (str): The query string to be answered.
    retrieved_documents (list): A list of dictionaries, each containing 'title' and 'abstract' keys.
    expected_abstracts (str): The expected abstract to be retrieved.
    model (str): The model to be used for evaluation.

    Returns:
    tuple: A tuple containing the score of the retrieved documents and a string explaining the scoring reason.
    """
    template = """You are an expert in medical abstracts. 
    You will receive two medical abstracts and a query. Your task is to determine which of these abstracts contains the most pertinent information to answer the query.     
    You must return the number of the abstract containing the most relevant information. If the two abstracts contain the same information, return number 1.
    Please provide a clear reason for your decision.

    ## Query:\n
    '"""+query+"""'

    ## Abstract 1:\n
    '"""+retrieved_documents+"""'

    ## Abstract 2:\n
    '"""+expected_abstracts+"""'
     
    ## Expected output:\n
    {
    "score": int,
    "scoring_reason": str
    }
    Your must provide a valid JSON with the key "number" and "reason".
    """
    if model == "Mixtral 8x7B":
        data = {
        "model": model,
        "messages": [{"role": "user", "content": template}],
        "stream": False,
        "format": "json",
        "options": {
            "seed": 101,
            "temperature": 0
        }
    }
        chat_response = requests.post('http://ollama:11434/api/chat', json=data).json()
        output = chat_response['message']['content']
    else:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        messages = [{"role":"user", "content":template}]
        completion = client.chat.completions.create(model=model,
                                                    messages=messages,
                                                    temperature=0)
        output = completion.choices[0].message.content
    pattern = r'\{+.*\}'
    match = re.findall(pattern, output, re.DOTALL)[0]
    match = match.replace("\n", '')
    score = 0
    scoring_reason = None
    if match:
        score_data = json.loads(match)
        score = score_data.get('score', 0)
        scoring_reason = score_data.get('scoring_reason', 'No scoring reason provided')
    return score, scoring_reason


@error_handling
def eval_response(query, response, retrieval, model):
    """
    Evaluate the relevance of a generated response to a query based on retrieved information.

    This function takes a query, a generated response, retrieval data, and the model used for
    evaluation. It scores the generated answer's relevance to the query on a scale from 1 to 5,
    with a higher score indicating greater relevance and consistency with the retrieval. The function
    also provides a reason for the score, especially if the generated answer contradicts the retrieval.

    Scoring Guidelines:
    - 5: Ideal, the generated answer includes all necessary information and is consistent with the retrieval.
    - 4: Mostly relevant, though it may be slightly too narrow or broad, maintaining consistency with the retrieval.
    - 3: Somewhat relevant, partly helpful but might be difficult to read or contain irrelevant content, yet consistent.
    - 2: Barely relevant, contains contradictions with the retrieval.
    - 1: Completely irrelevant and contradictory to the retrieval.

    Parameters:
    query (str): The query string provided for evaluation.
    response (str): The generated response that needs to be evaluated.
    retrieval (str): The retrieval content against which the response is evaluated.
    model (str): The model used to evaluate the response.

    Returns:
    tuple: A tuple containing the score (float) and the scoring reason (str).
    """

    template = """Your task is to score the relevance between a generated answer and the query based on the retrieval in the range between 1 and 5, and please also provide the scoring reason.  
    Your primary focus should be on determining whether the generated answer contains sufficient information to address the given query according to the retrieval.    
    If the generated answer fails to provide enough relevant information or contains excessive extraneous information, then you should reduce the score accordingly.  
    If the generated answer contradicts the retrieval, it will receive a low score of 1-2.   
    For example, for query "Is the sky blue?", the retrieval is "the sky is blue." and the generated answer is "No, the sky is not blue.".   
    In this example, the generated answer contradicts the retrieval by stating that the sky is not blue, when in fact it is blue.   
    This inconsistency would result in a low score of 1-2, and the reason for the low score would reflect the contradiction between the generated answer and the retrieval.  
    Please provide a clear reason for the low score, explaining how the generated answer contradicts the retrieval.  
    Labeling standards are as following:  
    5 - ideal, should include all information to answer the query comparing to the retrieval， and the generated answer is consistent with the retrieval  
    4 - mostly relevant, although it might be a little too narrow or too broad comparing to the retrieval, and the generated answer is consistent with the retrieval  
    3 - somewhat relevant, might be partly helpful but might be hard to read or contain other irrelevant content comparing to the retrieval, and the generated answer is consistent with the retrieval  
    2 - barely relevant, perhaps shown as a last resort comparing to the retrieval, and the generated answer contradicts with the retrieval  
    1 - completely irrelevant, should never be used for answering this query comparing to the retrieval, and the generated answer contradicts with the retrieval

    ## Query:\n
    '"""+query+"""'

    ## Answer:\n
    '"""+response+"""'

    ## Retrieval:\n
    '"""+retrieval+"""'

    ## Expected output:\n
    {
    "score": int,
    "scoring_reason": str
    }
    Your must provide a valid JSON with the keys "score" and "scoring_reason". The value of score must be an integer between 1 and 5.
    """
    if model == "Mixtral 8x7B":
        data = {
        "model": model,
        "messages": [{"role": "user", "content": template}],
        "stream": False,
        "format": "json",
        "options": {
            "seed": 101,
            "temperature": 0
        }
    }
        chat_response = requests.post('http://ollama:11434/api/chat', json=data).json()
        output = chat_response['message']['content']
      
    else:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        messages = [{"role":"user", "content":template}]
        completion = client.chat.completions.create(model=model,
                                                    messages=messages,
                                                    temperature=0)
        output = completion.choices[0].message.content
    pattern = r'\{+.*\}'
    match = re.findall(pattern, output, re.DOTALL)[0]
    match = match.replace("\n", '')
    score = 0
    scoring_reason = None
    if match:
        score_data = json.loads(match)
        score = score_data.get('score', 0)
        if score < 1 or score > 5:
            score = None
        scoring_reason = score_data.get('scoring_reason', 'No scoring reason provided')
    return float(score), scoring_reason


@error_handling
def plot_scores():
    """
    Plot the scores of the last evaluation of each model in the test folder.

    This function reads all the JSON files in the test folder, extracts the scores of the last evaluation, and plots them in a bar chart.
    The models are on the x-axis, and the scores are on the y-axis.

    The resulting plot is saved in the png folder as 'scores_plot_retrieval.png'.
    """
    
    results_file = 'polls/rag_evaluation/data/json/test'
    results_plot = 'polls/rag_evaluation/data/png'
    if not os.path.exists(results_file):
        print(f"Le répertoire {results_file} n'existe pas.")
        return
    if not os.listdir(results_file):
        print(f"Le répertoire {results_file} est vide.")
        return
    data_list = []
    for filename in os.listdir(results_file):
        filepath = os.path.join(results_file, filename)
        with open(filepath) as f:
            print(f"Lecture du fichier : {filepath}")
            data = json.load(f)
            data_list.append(data[-1])
    x_labels = [f"{data['research_type']}" for data in data_list]  
    scores = [data["score_retrieval"] for data in data_list]         
    x = np.arange(len(x_labels))  
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(x, scores, color='skyblue', width=0.6)  
    ax.set_xticks(x)
    ax.set_xticklabels(x_labels, rotation=45, ha='right') 
    ax.set_xlabel('Modèles')
    ax.set_ylabel('Scores')
    ax.set_title('Performance des modèles de recherche')
    plt.tight_layout()
    os.makedirs(results_plot, exist_ok=True)
    image_path = os.path.join(results_plot, 'scores_plot_retrieval.png')
    plt.savefig(image_path, format='png')
    plt.close(fig)

    
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
import environ

env = environ.Env() 
environ.Env.read_env()

@error_handling
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


@error_handling
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


@error_handling
def rag_articles_for_eval(query, research_type, number_of_results, model, number_of_articles=None, title_weight=None, abstract_weight=None, rank_scaling_factor=None):
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
        # Validation du score entre 1 et 5
        if score < 1 or score > 5:
            score = None
        scoring_reason = score_data.get('scoring_reason', 'No scoring reason provided')
    return float(score), scoring_reason


@error_handling

def plot_scores():
    # Répertoires des résultats et des graphiques
    results_file = 'polls/rag_evaluation/data/json/test'
    results_plot = 'polls/rag_evaluation/data/png'

    # Vérifier si le répertoire existe
    if not os.path.exists(results_file):
        print(f"Le répertoire {results_file} n'existe pas.")
        return
    if not os.listdir(results_file):
        print(f"Le répertoire {results_file} est vide.")
        return

    # Charger les données depuis les fichiers JSON
    data_list = []
    for filename in os.listdir(results_file):
        filepath = os.path.join(results_file, filename)
        with open(filepath) as f:
            print(f"Lecture du fichier : {filepath}")
            data = json.load(f)
            data_list.append(data[-1])

    # Configurer les scores et les légendes
    x_labels = [f"{data['research_type']}" for data in data_list]  # Noms des modèles
    scores = [data["score_retrieval"] for data in data_list]         # Scores associés
    x = np.arange(len(x_labels))  # Position des barres

    # Configurer le graphique
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(x, scores, color='skyblue', width=0.6)  # Ajouter des couleurs pour plus de lisibilité

    # Ajouter des étiquettes et un titre
    ax.set_xticks(x)
    ax.set_xticklabels(x_labels, rotation=45, ha='right')  # Noms des modèles
    ax.set_xlabel('Modèles')
    ax.set_ylabel('Scores')
    ax.set_title('Performance des modèles de recherche')

    # Ajuster les marges pour éviter que les étiquettes soient coupées
    plt.tight_layout()

    # Sauvegarder le graphique
    os.makedirs(results_plot, exist_ok=True)
    image_path = os.path.join(results_plot, 'scores_plot_retrieval.png')
    plt.savefig(image_path, format='png')
    plt.close(fig)

    print(f"Graphique sauvegardé dans : {image_path}")

    
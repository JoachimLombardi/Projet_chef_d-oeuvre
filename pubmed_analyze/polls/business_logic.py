
from elasticsearch_dsl import Search
import numpy as np
from sentence_transformers import CrossEncoder
import requests
from bs4 import BeautifulSoup
import time
from .utils import query_processing
from .models import Article, model


def init_soup(url):
    # Envoyer une requête GET pour récupérer le contenu de la page
    response = requests.get(url)
    # Vérifier que la requête a réussi
    if response.status_code == 200:
    # Parser le contenu HTML avec BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        return soup
    return None


def extract_pubmed_url(base_url, term, filter):
    links = []
    url = base_url+"/"+"?term="+term+"&filter=years."+filter+"-2025"
    soup = init_soup(url)
    print(soup)
    page_max = int(soup.select_one('label.of-total-pages').get_text(strip=True).split(" ")[-1]) if soup.select_one('label.of-total-pages') else 1
    for i in range(1, page_max+1, 1):
        list_articles = soup.select('div.search-results-chunk')
        for article in list_articles:
            links.extend([base_url+a['href'] for a in article.find_all('a', href=True)][:10]) # TO do tester si le lien a été scrapper
        time.sleep(1)
        soup = init_soup(url+"&page="+str(i))
    return links


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


def rank_doc(query, text, topN):
    # Initialize the CrossEncoder model with the specified model name
    reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
    # Predict scores for each document in relation to the query
    scores = reranker.predict([[query, doc["title"] + " " + doc["abstract"]] for doc in text])
    # Convert scores to Python float for cleaner output
    scores = [float(score) for score in scores]
    # Get indices of the top N scores in descending order
    top_indices = np.argsort(scores)[::-1][:topN]
    # Retrieve the top-ranked text documents using list indexing
    top_pairs = [{**text[index], "score": scores[index]} for index in top_indices]
    return top_pairs  # Returns a list of the top-ranked text strings
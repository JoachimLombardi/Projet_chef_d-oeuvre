
from elasticsearch_dsl import Search
import numpy as np
from sentence_transformers import CrossEncoder
import requests
from bs4 import BeautifulSoup
import time
from .utils import text_processing
from .models import Article, model
import json
from pathlib import Path
from django.http import HttpResponse
from .models import Authors, Affiliations, Article, Authorship
from django.conf import settings
from .utils import format_date, get_absolute_url
from polls.es_config import INDEX_NAME


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


def scrap_article_to_json(base_url='https://pubmed.ncbi.nlm.nih.gov', test=False):
    articles_data = []
    term = "multiple_sclerosis"
    filter = "2024"
    if not test:
        links = extract_pubmed_url(base_url, term, filter)
    else: 
        links = base_url
    for link in links:
        # Initialize soup
        soup = init_soup(link)
        if soup is None:
            continue
        # Extract reviews title
        title_review = soup.select_one('button.journal-actions-trigger')['title'] if soup.select_one('button.journal-actions-trigger') else None
        # Extract date
        date = soup.select_one('span.cit').get_text(strip=True).split(";")[0] if soup.select_one('.cit') else None
        date = format_date(date)
        # Extract title
        title = soup.select_one('h1.heading-title').get_text(strip=True) if soup.select_one('h1.heading-title') else None
        # Extract abstract
        abstract = soup.select('div.abstract-content p')
        abstract = [p.get_text(strip=True) for p in abstract] if abstract else None
        if abstract:
            if isinstance(abstract, list):
                abstract = " ".join(abstract)
            # Extract PMID
            pmid = soup.select_one('span.identifier.pubmed strong.current-id').get_text(strip=True) if soup.select_one('span.identifier.pubmed strong.current-id') else None
            # Extract DOI
            doi = soup.select_one('span.identifier.doi a.id-link').get_text(strip=True) if soup.select_one('span.identifier.doi a.id-link') else None
            if doi:
                doi = "https://doi.org/"+doi
            # Extract conflict of interest statement
            disclosure = soup.select_one('div.conflict-of-interest div.statement p').get_text(strip=True) if soup.select_one('div.conflict-of-interest div.statement p') else None
            # Extract mesh terms
            buttons = soup.select('button.keyword-actions-trigger')
            mesh_terms = [button.get_text(strip=True) for button in buttons] if buttons else None
            mesh_terms = ", ".join(mesh_terms) if mesh_terms else None
            url = get_absolute_url(pmid)
            authors_tags = soup.select('.authors-list-item')
            authors_affiliations = []
            seen_authors = set() 
            for author_tag in authors_tags:
                # Extraire le nom de l'auteur
                author_name = author_tag.select_one('.full-name').get_text(strip=True) if author_tag.select_one('.full-name') else None
                if author_name and author_name not in seen_authors:
                    seen_authors.add(author_name)
                    # Extraire les affiliations
                    affiliation_elements = author_tag.select('.affiliation-link')
                    if affiliation_elements:
                        affiliations_names = [affil.get('title', None) for affil in affiliation_elements]
                        authors_affiliations.append({'author_name': author_name, 'affiliations': affiliations_names})
            # Add article data to list
            articles_data.append({
            'title_review': title_review,
            'date': str(date),  # Convert date to string for JSON serialization
            'title': title,
            'abstract': abstract,
            'pmid': pmid,
            'doi': doi,
            'disclosure': disclosure,
            'mesh_terms': mesh_terms,
            'url': url,
            'authors_affiliations': authors_affiliations
        })
            # Save articles data to a JSON file
            if not test:
                output_path = Path(settings.EXPORT_JSON_DIR + "/" + term + "_" + filter + ".json")
            else:
                output_path = Path(settings.EXPORT_JSON_DIR + "/" + term + "_" + filter + "_test.json")
            with output_path.open('w', encoding='utf-8') as f:
                json.dump(articles_data, f, ensure_ascii=False, indent=4)


def article_json_to_database(request): 
    term = "herpes_zoster"
    filter = "2024"
    output_path = Path(settings.EXPORT_JSON_DIR + "/" + term + "_" + filter + ".json")
    with output_path.open('r', encoding='utf-8') as f:
        articles = json.load(f)
        for article in articles:
            title = article['title']
            abstract = article['abstract']
            date = article['date']
            if date == "None":
                date = None
            url = article['url']
            pmid = article['pmid']
            doi = article['doi']
            mesh_terms = article['mesh_terms']
            disclosure = article['disclosure']
            title_review = article['title_review']
            authors_affiliations = article['authors_affiliations']
            if not Article.objects.filter(doi=doi).exists():
                article = Article.objects.create(title=title, abstract=abstract, date=date, url=url, pmid=pmid, doi=doi, mesh_terms=mesh_terms, disclosure=disclosure, title_review=title_review, term=term + "_" + filter)
                for author_affiliation in authors_affiliations:
                    author_name = author_affiliation['author_name']
                    affiliations = author_affiliation['affiliations']
                    author, created = Authors.objects.get_or_create(name=author_name)
                    for affiliation in affiliations:
                        affiliation, created = Affiliations.objects.get_or_create(name=affiliation)
                        if not Authorship.objects.filter(article=article, author=author, affiliation=affiliation).exists():
                            Authorship.objects.create(article=article, author=author, affiliation=affiliation)
    return HttpResponse("Article, authors and affiliations added to database with success.")


def reciprocal_rank_fusion(results1, results2, k=60):
    combined_scores = {}
    for results in [results1, results2]:
        for rank, doc in enumerate(results):
            doc_id = doc.meta.id
            score = 1 / (rank + 1 + k)
            combined_scores[doc_id] = combined_scores.get(doc_id, 0) + score
    sorted_results = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
    hits = {**{hit.meta.id: hit for hit in results1}, **{hit.meta.id: hit for hit in results2}}
    ids_added = set()
    response = [hits[doc_id] for doc_id, _ in sorted_results if doc_id in hits and doc_id not in ids_added and not ids_added.add(doc_id)]
    return response


def search_articles(query, index=""):
    query_cleaned = text_processing(query)
    query_vector = model.encode(query_cleaned).tolist() 
    search_results_vector = Search(index=INDEX_NAME).query(
    "knn",
    field="title_abstract_vector",
    query_vector=query_vector,
    k=20,
    num_candidates=5000
    ).source(['title', 'abstract']) # Include the 'title' and 'abstract' fields in the response
    response_vector = search_results_vector.execute()
    search_results_text = Search(index=INDEX_NAME).query(
    "multi_match",
    fields=['title^2', 'abstract'],
    query=query_cleaned,
    type="best_fields",
    ).source(['title', 'abstract']) 
    response_text = search_results_text[0:20].execute()
    # hybrid search
    retrieved_docs = reciprocal_rank_fusion(response_vector.hits, response_text.hits, k=60)
    # rerank
    response = rank_doc(query_cleaned, retrieved_docs, 3)
    # Prepare results for JSON response
    results = []
    article_ids = [res['id'] for res in response]  # Gather all article IDs for a single query
    articles = Article.objects.filter(id__in=article_ids).prefetch_related('authorships__author', 'authorships__affiliation')
    if index:
        articles = articles.filter(term=index)
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


def rank_doc(query, retrieved_docs, topN):
    text = [{"id":hit.meta.id, "title":hit.title, "abstract":hit.abstract} for hit in retrieved_docs]
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
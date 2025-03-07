
import ast
import csv
import re
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
from .utils import format_date, get_absolute_url, error_handling
from polls.es_config import INDEX_NAME
from django.db import transaction



@error_handling
def init_soup(url):
    # Envoyer une requête GET pour récupérer le contenu de la page
    response = requests.get(url)
    # Vérifier que la requête a réussi
    if response.status_code == 200:
    # Parser le contenu HTML avec BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        return soup
    return None


@error_handling
def extract_pubmed_url(base_url, term, filter):
    links = []
    url = base_url+"/"+"?term="+term+"&filter=years."+filter+"-2025"
    soup = init_soup(url)
    page_max = int(soup.select_one('label.of-total-pages').get_text(strip=True).split(" ")[-1]) if soup.select_one('label.of-total-pages') else 1
    for i in range(1, page_max+1, 1):
        list_articles = soup.select('div.search-results-chunk')
        for article in list_articles:
            links.extend([base_url+a['href'] for a in article.find_all('a', href=True)][:10]) # TO do tester si le lien a été scrapper
        time.sleep(1)
        soup = init_soup(url+"&page="+str(i))
    return links


@error_handling
def scrap_article_to_json(base_url='https://pubmed.ncbi.nlm.nih.gov', url=None, suffix_article=None):
    articles_data = []
    term = ""
    filter = "2025"
    suffix = term+"_"+filter
    if not url:
        links = extract_pubmed_url(base_url, term, filter)
    else:
        links = url
    if suffix_article:
        suffix += suffix_article
    for link in links:
        # Initialize soup
        soup = init_soup(link)
        if soup is None:
            continue
        # Extract abstract
        abstract = soup.select('div.abstract-content p')
        abstract = [p.get_text(strip=True) for p in abstract] if abstract else None
        if abstract:
            if isinstance(abstract, list):
                abstract = " ".join(abstract)
             # Extract reviews title
            title_review = soup.select_one('button.journal-actions-trigger')['title'] if soup.select_one('button.journal-actions-trigger') else None
            # Extract date
            date = soup.select_one('span.cit').get_text(strip=True).split(";")[0] if soup.select_one('.cit') else None
            date = format_date(date)
            # Extract title
            title = soup.select_one('h1.heading-title').get_text(strip=True) if soup.select_one('h1.heading-title') else None
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
            output_path = Path(settings.EXPORT_JSON_DIR + "/" + suffix + ".json")
            with output_path.open('w', encoding='utf-8') as f:
                json.dump(articles_data, f, ensure_ascii=False, indent=4)


def scrap_article_to_csv(base_url='https://pubmed.ncbi.nlm.nih.gov', url=None, suffix_article=None):
    articles_data = []
    term = ""
    filter = "2025"
    suffix = term+"_"+filter
    if not url:
        links = extract_pubmed_url(base_url, term, filter)
    else:
        links = url
    if suffix_article:
        suffix += suffix_article
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
            output_path = Path(settings.EXPORT_CSV_DIR + "/" + suffix + ".csv")
            with output_path.open('w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['title_review', 'date', 'title', 'abstract', 'pmid', 'doi', 'disclosure', 'mesh_terms', 'url', 'authors_affiliations']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for article in articles_data:
                    writer.writerow(article)


@error_handling
def article_json_to_database(): 
    """
    Read JSON files of articles scraped from PubMed and save them to the database
    
    This function reads JSON files that were created by the article_scraper function, 
    and save the articles to the database. 

    The function is decorated with the @error_handling decorator, so it will log
    and email the error if there is one.

    The JSON files are located in the EXPORT_JSON_DIR directory, and are named 
    after the term and filter used to search PubMed (e.g. "multiple_sclerosis_2024.json").

    The function creates an Article instance for each article in the JSON file, 
    and saves it to the database. It also creates Author and Affiliation instances 
    as needed, and creates Authorship instances to link authors to their affiliations.

    The function does not create duplicate articles if they already exist in the database.

    The function does not create duplicate authors, affiliations or authorships if they already exist in the database.

    The function is meant to be called as a management command, and should be called once
    after the article_scraper function has finished.

    Decorator:

    @error_handling: Captures and manages errors during execution.
    Models Used:

    Article: Stores metadata for articles.
    Authors: Stores information about authors.
    Affiliations: Stores information about affiliations.
    Authorship: Establishes relationships between articles, authors, and their affiliations.

    The function does not return anything.

    """
    existing_articles = {article.pmid: article for article in Article.objects.all()}
    existing_authors = {author.name: author for author in Authors.objects.all()}
    existing_affiliations = {affiliation.name: affiliation for affiliation in Affiliations.objects.all()}
    new_articles = []
    new_authors = []
    new_affiliations = []
    new_autorship = []
    article_in_json = set()
    author_in_json = set()
    affiliation_in_json = set()
    term_list = ["multiple_sclerosis", "herpes_zoster"]
    filter = "2024"
    for term in term_list:
        output_path = Path(settings.EXPORT_JSON_DIR + "/" + term + "_" + filter + ".json")
        with output_path.open('r', encoding='utf-8') as f:
            articles = json.load(f)
            for article in articles:
                title = article.get('title', "")
                abstract = article.get('abstract', "")
                date = article.get('date', "")
                if date == "None":
                    date = None
                url = article.get('url', "")
                pmid = article.get('pmid', "")
                doi = article.get('doi', "")
                mesh_terms = article.get('mesh_terms', "")
                disclosure = article.get('disclosure', "")
                title_review = article.get('title_review', "")
                authors_affiliations = article.get('authors_affiliations', "")
                article_obj = Article(title=title, 
                                    abstract=abstract, 
                                    date=date, url=url, 
                                    pmid=pmid, doi=doi, 
                                    mesh_terms=mesh_terms, 
                                    disclosure=disclosure, 
                                    title_review=title_review, 
                                    term=term + "_" + filter)
                if pmid not in existing_articles and pmid not in article_in_json:
                    new_articles.append(article_obj)
                    article_in_json.add(pmid)
                for author_affiliation in authors_affiliations:
                    author_name = author_affiliation.get('author_name', "")
                    author_name_obj = Authors(name=author_name)
                    if author_name not in existing_authors and author_name not in author_in_json:
                        new_authors.append(author_name_obj)
                        author_in_json.add(author_name)
                    affiliations = author_affiliation.get('affiliations', "")
                    for affiliation in affiliations:
                        affiliation_obj = Affiliations(name=affiliation)
                        if affiliation not in existing_affiliations and affiliation not in affiliation_in_json:
                            new_affiliations.append(affiliation_obj)
                            affiliation_in_json.add(affiliation)
    with transaction.atomic():
        if new_articles:
            Article.objects.bulk_create(new_articles)
            existing_articles.update({article.pmid: article for article in Article.objects.all()})
        if new_authors:
            Authors.objects.bulk_create(new_authors)
            existing_authors.update({author.name: author for author in Authors.objects.all()})
        if new_affiliations:
            Affiliations.objects.bulk_create(new_affiliations) 
            existing_affiliations.update({affiliation.name: affiliation for affiliation in Affiliations.objects.all()})
    for term in term_list:
        output_path = Path(settings.EXPORT_JSON_DIR + "/" + term + "_" + filter + ".json")
        with output_path.open('r', encoding='utf-8') as f:
            articles = json.load(f)
            for article in articles:
                pmid = article.get('pmid')
                authors_affiliations = article.get('authors_affiliations', "")
                article_obj = existing_articles.get(int(pmid))
                for author_affiliation in authors_affiliations:
                    author_name = author_affiliation.get('author_name', "")
                    affiliations = author_affiliation.get('affiliations', "")
                    author_name_obj = existing_authors.get(author_name)
                    for affiliation in affiliations:
                        affiliation_obj = existing_affiliations.get(affiliation)
                        new_autorship.append(Authorship(article=article_obj, author=author_name_obj, affiliation=affiliation_obj))
    with transaction.atomic():
        if new_autorship:
            Authorship.objects.bulk_create(new_autorship, ignore_conflicts=True)
        
              
def article_csv_to_database():
    """
    Read CSV files of articles scraped from PubMed and save them to the database
    
    This function reads CSV files that were created by the article_scraper function, 
    and saves the articles to the database. 

    The CSV files are located in the EXPORT_CSV_DIR directory, and are named 
    after the term and filter used to search PubMed (e.g. "multiple_sclerosis_2024.csv").

    The function creates an Article instance for each article in the CSV file, 
    and saves it to the database. It also creates Author and Affiliation instances 
    as needed, and creates Authorship instances to link authors to their affiliations.

    The function does not create duplicate articles if they already exist in the database.

    The function does not create duplicate authors, affiliations or authorships if they already exist in the database.

    The function is meant to be called as a management command, and should be called once
    after the article_scraper function has finished.
    
    """
    existing_articles = {article.doi: article for article in Article.objects.all()}
    existing_authors = {author.name: author for author in Authors.objects.all()}
    existing_affiliations = {affiliation.name: affiliation for affiliation in Affiliations.objects.all()}
    new_articles = []
    new_authors = []
    new_affiliations = []
    new_autorship = []
    term_list = ["multiple_sclerosis", "herpes_zoster"]
    for term in term_list:
        filter = "2024"
        output_path = Path(settings.EXPORT_CSV_DIR + "/" + term + "_" + filter + ".csv")
        with output_path.open('r', encoding='utf-8') as f:
            articles = csv.DictReader(f)
            for article in articles:
                title = article.get('title', "")
                abstract = article.get('abstract', "")
                date = article.get('date', "")
                if date == "None":
                    date = None
                url = article.get('url', "")
                pmid = article.get('pmid', "")
                doi = article.get('doi', "")
                mesh_terms = article.get('mesh_terms', "")
                disclosure = article.get('disclosure', "")
                title_review = article.get('title_review', "")
                authors_affiliations = article.get('authors_affiliations', "")
                try:
                    authors_affiliations = ast.literal_eval(authors_affiliations)
                except Exception as e:
                    author_affiliation = []
                    article_obj = Article(title=title, 
                                        abstract=abstract, 
                                        date=date, url=url, 
                                        pmid=pmid, doi=doi, 
                                        mesh_terms=mesh_terms, 
                                        disclosure=disclosure, 
                                        title_review=title_review, 
                                        term=term + "_" + filter)
                if not doi in existing_articles:
                    new_articles.append(article_obj)
                for author_affiliation in authors_affiliations:
                    author_name = author_affiliation.get('author_name', "")
                    author_name = Authors(name=author_name)
                    if not author_name in existing_authors:
                        new_authors.append(author_name)
                    affiliations = author_affiliation.get('affiliations', "")
                    try:
                        affiliations = ast.literal_eval(affiliations)
                    except:
                        affiliations = []
                    for affiliation in affiliations:
                        affiliation_obj = Affiliations(name=affiliation)
                        if not affiliation in existing_affiliations:
                            new_affiliations.append(affiliation_obj)
                        new_autorship.append(Authorship(article=article_obj, author=author_name, affiliation=affiliation_obj))
                with transaction.atomic():
                    if new_articles:
                        Article.objects.bulk_create(new_articles)
                    if new_authors:
                        Authors.objects.bulk_create(new_authors)
                    if new_affiliations:
                        Affiliations.objects.bulk_create(new_affiliations) 
                    if new_autorship:   
                        Authorship.objects.bulk_create(new_autorship, ignore_conflicts=True)


@error_handling
def reciprocal_rank_fusion(search_vector, search_text, k=60):
    combined_scores = {}
    for results in [search_vector, search_text]:
        for rank, doc in enumerate(results):
            doc_id = doc.meta.id
            score = 1 / (rank + 1 + k)
            combined_scores[doc_id] = combined_scores.get(doc_id, 0) + score
    sorted_results = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
    hits = {**{hit.meta.id: hit for hit in search_vector}, **{hit.meta.id: hit for hit in search_text}}
    ids_added = set()
    response = [hits[doc_id] for doc_id, _ in sorted_results if doc_id in hits and doc_id not in ids_added and not ids_added.add(doc_id)]
    return response


@error_handling
def search_articles(query, index):
    query_cleaned = text_processing(query)
    query_vector = model.encode(query_cleaned).tolist() 
    search_results_vector = Search(index=INDEX_NAME).query(
    "knn",
    field="title_abstract_vector",
    query_vector=query_vector,
    k=10,
    num_candidates=5000
    ).source(['title', 'abstract']) # Include the 'title' and 'abstract' fields in the response
    response_vector = search_results_vector.execute()
    search_results_text = Search(index=INDEX_NAME).query(
    "multi_match",
    fields=['title^2', 'abstract^5'],
    query=query_cleaned,
    type="best_fields",
    ).source(['title', 'abstract']) 
    response_text = search_results_text[0:10].execute()
    # hybrid search
    retrieved_docs = reciprocal_rank_fusion(response_vector.hits, response_text.hits, k=5)
    # rerank
    response = rank_doc(query_cleaned, retrieved_docs, 3)
    # Prepare results for JSON response
    results = []
    article_ids = [res['id'] for res in response]  # Gather all article IDs for a single query
    article_dict = {
        article.id: article
        for article in Article.objects.filter(id__in=article_ids).prefetch_related('authorships__author', 'authorships__affiliation')
    }
    articles = Article.objects.filter(id__in=article_ids).prefetch_related('authorships__author', 'authorships__affiliation')
    if index != "all":
        articles = articles.filter(term=index)
    # Process the search hits and build the results list
    for res in response:
        article_id = int(res['id'])
        score = res['score']
        title = res['title']
        abstract = res['abstract']
        # Get the article from the pre-fetched queryset
        article = article_dict.get(article_id, None)
        if article:
            # Retrieve authors and their affiliations
            affiliations_by_author = {}
            for authorship in article.authorships.all():
                author_name = authorship.author.name
                affiliation_name = authorship.affiliation.name
                # Avoid duplicates by using a set
                affiliations_by_author.setdefault(author_name, set()).add(affiliation_name)
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

@error_handling
def generation(query, retrieved_documents, model, index="all"):
    context = ""
    for i, source in enumerate(retrieved_documents):
        context += f"Abstract n°{i+1}: " + source['title'] + "." + "\n\n" + source['abstract'] + "\n\n"
    template = """You are an expert in analysing medical abstract and your are talking to a pannel of medical experts. Your task is to use only provided context to answer at best the query.
    If you don't know or if the answer is not in the provided context just say: "I can't answer with the provided context".

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
    print("voici la rep:", chat_response, flush=True)
    pattern = r'\{+.*\}'
    match = re.findall(pattern, chat_response['message']['content'], re.DOTALL)[0]
    if match:
        match = match.replace("\n", "")
        response = json.loads(match)['response']
    else:
        response = "I can't answer with the provided context"
    print("la réponse est: ", response)
    return response, context


@error_handling
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
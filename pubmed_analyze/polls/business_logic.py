
import csv
import functools
import os
import re

import pandas as pd
from elasticsearch_dsl import Search
import numpy as np
from sentence_transformers import CrossEncoder
import requests
from bs4 import BeautifulSoup
import time
from .utils import text_processing
from .models import Article, ArticlesWithAuthors, model
import json
from pathlib import Path
from .models import Authors, Affiliations, Article, Authorship
from django.conf import settings
from .utils import format_date, get_absolute_url, error_handling
from polls.es_config import INDEX_NAME
from django.db import transaction


@error_handling
def init_soup(url, session):
    """
    Initializes a BeautifulSoup object from the content of a given URL.

    This function makes an HTTP GET request to the specified URL and
    attempts to parse the response content into a BeautifulSoup object
    if the request is successful. It returns the BeautifulSoup object
    if the status code of the response is 200, otherwise returns None.

    Parameters
    ----------
    url : str
        The URL from which to fetch the content and initialize a
        BeautifulSoup object.

    Returns
    -------
    BeautifulSoup or None
        A BeautifulSoup object if the request is successful, otherwise
        None.
    """

    response = session.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        return soup
    return None


@error_handling
def extract_pubmed_url(base_url, term, filter, session):
    """
    Extracts PubMed article URLs based on a search term and filter.

    This function constructs a search URL using the provided base URL,
    search term, and filter, and then scrapes the PubMed search results
    pages to extract article URLs. It iterates over all pages of the
    search results if multiple pages are available.

    Parameters
    ----------
    base_url : str
        The base URL of PubMed.
    term : str
        The search term to be used in the PubMed query.
    filter : str
        The filter to apply to the search, typically indicating a date
        range or other criteria.

    Returns
    -------
    list of str
        A list of URLs of the articles found in the search results.
    """

    links = []
    url = base_url+"/"+"?term="+term+"&filter=years."+filter+"-2025"
    soup = init_soup(url, session)
    page_max = int(soup.select_one('label.of-total-pages').get_text(strip=True).split(" ")[-1]) if soup.select_one('label.of-total-pages') else 1
    for i in range(1, page_max+1, 1):
        list_articles = soup.select('div.search-results-chunk')
        for article in list_articles:
            links.extend([base_url+a['href'] for a in article.find_all('a', href=True)][:10]) 
        time.sleep(1)
        soup = init_soup(url+"&page="+str(i), session)
    return links


@error_handling
def scrap_article_to_json(base_url='https://pubmed.ncbi.nlm.nih.gov', url=None, suffix_article=None):
    """
    Scrapes PubMed article details and saves them to a JSON file.

    This function scrapes articles based on a search term and filter, and then
    saves the scraped data to a JSON file. The scraped data includes the title
    of the review, date of publication, title of the article, abstract, PMID,
    DOI, conflict of interest statement, mesh terms, URL of the article, and
    authors with their affiliations.

    Parameters
    ----------
    base_url : str, optional
        The base URL of PubMed. Defaults to 'https://pubmed.ncbi.nlm.nih.gov'.
    url : list of str, optional
        A list of URLs of articles to be scraped. If not provided, performs a
        search based on the term and filter.
    suffix_article : str, optional
        A suffix to be appended to the JSON file name.

    Returns
    -------
    None
    """
    articles_data = []
    term = ""
    filter = "2025"
    suffix = term+"_"+filter
    with requests.Session() as session:
        if not url:
            links = extract_pubmed_url(base_url, term, filter, session)
        else:
            links = url
        if suffix_article:
            suffix += suffix_article
        for link in links:
            soup = init_soup(link, session)
            if soup is None:
                continue
            abstract = soup.select('div.abstract-content p')
            abstract = [p.get_text(strip=True) for p in abstract] if abstract else None
            if abstract:
                if isinstance(abstract, list):
                    abstract = " ".join(abstract)
                title_review = soup.select_one('button.journal-actions-trigger')['title'] if soup.select_one('button.journal-actions-trigger') else None
                date = soup.select_one('span.cit').get_text(strip=True).split(";")[0] if soup.select_one('.cit') else None
                date = format_date(date)
                title = soup.select_one('h1.heading-title').get_text(strip=True) if soup.select_one('h1.heading-title') else None
                pmid = soup.select_one('span.identifier.pubmed strong.current-id').get_text(strip=True) if soup.select_one('span.identifier.pubmed strong.current-id') else None
                doi = soup.select_one('span.identifier.doi a.id-link').get_text(strip=True) if soup.select_one('span.identifier.doi a.id-link') else None
                if doi:
                    doi = "https://doi.org/"+doi
                disclosure = soup.select_one('div.conflict-of-interest div.statement p').get_text(strip=True) if soup.select_one('div.conflict-of-interest div.statement p') else None
                buttons = soup.select('button.keyword-actions-trigger')
                mesh_terms = [button.get_text(strip=True) for button in buttons] if buttons else None
                mesh_terms = ", ".join(mesh_terms) if mesh_terms else None
                url = get_absolute_url(pmid)
                authors_tags = soup.select('.authors-list-item')
                authors_affiliations = []
                seen_authors = set() 
                for author_tag in authors_tags:
                    author_name = author_tag.select_one('.full-name').get_text(strip=True) if author_tag.select_one('.full-name') else None
                    if author_name and author_name not in seen_authors:
                        seen_authors.add(author_name)
                        affiliation_elements = author_tag.select('.affiliation-link')
                        if affiliation_elements:
                            affiliations_names = [affil.get('title', None) for affil in affiliation_elements]
                            authors_affiliations.append({'author_name': author_name, 'affiliations': affiliations_names})
                articles_data.append({
                'title_review': title_review,
                'date': str(date),  
                'title': title,
                'abstract': abstract,
                'pmid': pmid,
                'doi': doi,
                'disclosure': disclosure,
                'mesh_terms': mesh_terms,
                'url': url,
                'authors_affiliations': authors_affiliations
            })
                output_path = Path(settings.EXPORT_JSON_DIR + "/" + suffix + ".json")
                with output_path.open('w', encoding='utf-8') as f:
                    json.dump(articles_data, f, ensure_ascii=False, indent=4)


def scrap_article_to_csv(base_url='https://pubmed.ncbi.nlm.nih.gov', url=None, suffix_article=None):
    """
    Scrapes PubMed article details and saves them to a CSV file.

    This function scrapes articles based on a search term and filter, extracting
    details such as the title of the review, publication date, article title, 
    abstract, PMID, DOI, conflict of interest statement, mesh terms, URL, and 
    authors with their affiliations. The extracted data is saved to a CSV file.

    Parameters
    ----------
    base_url : str, optional
        The base URL of PubMed. Defaults to 'https://pubmed.ncbi.nlm.nih.gov'.
    url : list of str, optional
        A list of URLs of articles to be scraped. If not provided, performs a
        search based on the term and filter.
    suffix_article : str, optional
        A suffix to be appended to the CSV file name.

    Returns
    -------
    None
    """

    articles_data = []
    term = ""
    filter = "2025"
    suffix = term+"_"+filter
    with requests.Session() as session:
        if not url:
            links = extract_pubmed_url(base_url, term, filter, session)
        else:
            links = url
        if suffix_article:
            suffix += suffix_article
        for link in links:
            soup = init_soup(link, session)
            if soup is None:
                continue
            title_review = soup.select_one('button.journal-actions-trigger')['title'] if soup.select_one('button.journal-actions-trigger') else None
            date = soup.select_one('span.cit').get_text(strip=True).split(";")[0] if soup.select_one('.cit') else None
            date = format_date(date)
            title = soup.select_one('h1.heading-title').get_text(strip=True) if soup.select_one('h1.heading-title') else None
            abstract = soup.select('div.abstract-content p')
            abstract = [p.get_text(strip=True) for p in abstract] if abstract else None
            if abstract:
                if isinstance(abstract, list):
                    abstract = " ".join(abstract)
                pmid = soup.select_one('span.identifier.pubmed strong.current-id').get_text(strip=True) if soup.select_one('span.identifier.pubmed strong.current-id') else None
                doi = soup.select_one('span.identifier.doi a.id-link').get_text(strip=True) if soup.select_one('span.identifier.doi a.id-link') else None
                if doi:
                    doi = "https://doi.org/"+doi
                disclosure = soup.select_one('div.conflict-of-interest div.statement p').get_text(strip=True) if soup.select_one('div.conflict-of-interest div.statement p') else None
                buttons = soup.select('button.keyword-actions-trigger')
                mesh_terms = [button.get_text(strip=True) for button in buttons] if buttons else None
                mesh_terms = ", ".join(mesh_terms) if mesh_terms else None
                url = get_absolute_url(pmid)
                authors_tags = soup.select('.authors-list-item')
                authors_affiliations = []
                seen_authors = set() 
                for author_tag in authors_tags:
                    author_name = author_tag.select_one('.full-name').get_text(strip=True) if author_tag.select_one('.full-name') else None
                    if author_name and author_name not in seen_authors:
                        seen_authors.add(author_name)
                        affiliation_elements = author_tag.select('.affiliation-link')
                        if affiliation_elements:
                            affiliations_names = [affil.get('title', None) for affil in affiliation_elements]
                            authors_affiliations.append({'author_name': author_name, 'affiliations': affiliations_names})
                articles_data.append({
                'title_review': title_review,
                'date': str(date),  
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
                date = article.get('date', "")
                if date.lower() in ["none", "", "null"]:
                    date = None
                pmid = article.get('pmid', "")
                authors_affiliations = article.get('authors_affiliations', "")
                if pmid not in existing_articles and pmid not in article_in_json:
                    new_articles.append(Article(title=article.get('title', ""), 
                                abstract=article.get('abstract', ""),
                                date=date, url=article.get('url', ""),
                                pmid=article.get('pmid', ""), doi=article.get('doi', ""),
                                mesh_terms=article.get('mesh_terms', ""),
                                disclosure=article.get('disclosure', ""),
                                title_review=article.get('title_review', ""),
                                term=term + "_" + filter))
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


@error_handling
def article_csv_to_database(): 
    """
    Read JSON files of articles scraped from PubMed and save them to the database
    
    This function reads CSV files that were created by the article_scraper function, 
    and save the articles to the database. 

    The function is decorated with the @error_handling decorator, so it will log
    and email the error if there is one.

    The JSON files are located in the EXPORT_CSV_DIR directory, and are named 
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
        output_path = Path(settings.EXPORT_CSV_DIR + "/" + term + "_" + filter + ".csv")
        with output_path.open('r', encoding='utf-8') as f:
            articles = csv.DictReader(f)
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


def articles_full_to_database():
    """
    Reads the Article, Author and Affiliation models from the database, and for each article
    creates an ArticlesWithAuthors instance, which contains all the article metadata as well
    as the affiliations of the authors. This function is meant to be called once after the
    article_csv_to_database function has finished.

    The function does not create duplicate articles if they already exist in the database.

    The function does not return anything.

    Models Used:

    Article: Stores metadata for articles.
    Authors: Stores information about authors.
    Affiliations: Stores information about affiliations.
    Authorship: Establishes relationships between articles, authors, and their affiliations.
    ArticlesWithAuthors: A model that contains all the article metadata as well as the affiliations
                         of the authors.

    Decorator:

    @error_handling: Captures and manages errors during execution.
    """
    existing_articles_wiht_authors = {article.doi: article for article in ArticlesWithAuthors.objects.all()}
    new_articles_with_authors = []
    articles_in_dict = set()
    articles = Article.objects.prefetch_related('authorships__author', 'authorships__affiliation').order_by('id')
    for article in articles:
        affiliations_by_author = {}
        for authorship in article.authorships.all():
            author_name = authorship.author.name
            affiliation_name = authorship.affiliation.name    
            affiliations_by_author.setdefault(author_name, set()).add(affiliation_name)
        article.affiliations_by_author = {author: list(affs) for author, affs in affiliations_by_author.items()}
        if article.doi not in existing_articles_wiht_authors and article.doi not in articles_in_dict:
            new_articles_with_authors.append(ArticlesWithAuthors(title=article.title, 
                                                                abstract=article.abstract, 
                                                                date=article.date, url=article.url, 
                                                                pmid=article.pmid, doi=article.doi, 
                                                                mesh_terms=article.mesh_terms, 
                                                                disclosure=article.disclosure, 
                                                                title_review=article.title_review, 
                                                                term=article.term, 
                                                                affiliations_by_author=article.affiliations_by_author))
            articles_in_dict.add(article.doi)
    with transaction.atomic():
        if new_articles_with_authors:
            ArticlesWithAuthors.objects.bulk_create(new_articles_with_authors)


@error_handling
def reciprocal_rank_fusion(search_vector, search_text, k=60):
    """
    Perform Reciprocal Rank Fusion (RRF) on two sets of search results.

    This function takes two sets of search results and combines their scores using the 
    Reciprocal Rank Fusion method. RRF is an ensemble method that ranks documents by 
    aggregating their ranks from multiple sources, in this case, the search vector and 
    search text results.

    Parameters:
    search_vector (list): A list of search results from a vector-based search, where each 
                          result contains metadata with an 'id'.
    search_text (list): A list of search results from a text-based search, where each 
                        result contains metadata with an 'id'.
    k (int, optional): A constant used in the RRF calculation to control the 
                       score discounting based on rank. Default is 60.

    Returns:
    list: A list of search results, sorted by their combined RRF scores, without duplicates.
    """

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
    """
    Search articles in the database with a query.

    This function takes a query string and an index (the term to search in), and returns a list of
    search results, where each result is a dictionary containing metadata for the article, such as
    title, abstract, score, and authors and affiliations.

    Parameters:
    query (str): The query string to search for.
    index (str): The term to search in. If "all", all terms are searched.

    Returns:
    list: A list of search results, where each result is a dictionary containing metadata for the article.
    """
    query_cleaned = text_processing(query)
    query_vector = model.encode(query_cleaned).tolist() 
    search_results_vector = Search(index=INDEX_NAME).query(
    "knn",
    field="title_abstract_vector",
    query_vector=query_vector,
    k=10,
    num_candidates=5000
    ).source(['title', 'abstract']) 
    response_vector = search_results_vector.execute()
    search_results_text = Search(index=INDEX_NAME).query(
    "multi_match",
    fields=['title^2', 'abstract^5'],
    query=query_cleaned,
    type="best_fields",
    ).source(['title', 'abstract']) 
    response_text = search_results_text[0:10].execute()
    retrieved_docs = reciprocal_rank_fusion(response_vector.hits, response_text.hits, k=5)
    response = rank_doc(query_cleaned, retrieved_docs, 3)
    results = []
    article_ids = [res['id'] for res in response] 
    articles = Article.objects.filter(id__in=article_ids).prefetch_related('authorships__author', 'authorships__affiliation')
    if index != "all":
        articles = articles.filter(term=index)
    article_dict = {
        article.id: article
        for article in articles
    }
    for res in response:
        article_id = int(res['id'])
        score = res['score']
        title = res['title']
        abstract = res['abstract']
        article = article_dict.get(article_id, None)
        if article:
            affiliations_by_author = {}
            for authorship in article.authorships.all():
                author_name = authorship.author.name
                affiliation_name = authorship.affiliation.name
                affiliations_by_author.setdefault(author_name, set()).add(affiliation_name)
            authors_affiliations = {author: list(affs) for author, affs in affiliations_by_author.items()}
            results.append({
                'id': article_id,
                'score': score,
                'title': title,
                'abstract': abstract,
                'authors_affiliations': authors_affiliations
            })
    return results, query

@error_handling
def generation(query, retrieved_documents, model):
    """
    Generate a response to a query based on retrieved medical documents.

    This function constructs a context from a list of retrieved medical documents,
    formats it into a template, and sends it to a chat model API to generate a response
    to the provided query. The function ensures to return a valid JSON response 
    containing the key "response".

    Parameters:
    query (str): The query string to be answered.
    retrieved_documents (list): A list of dictionaries, each containing 'title' and 'abstract' 
                                keys representing the retrieved medical documents.
    model (str): The model to be used for generating the response.
    index (str, optional): The index from which documents are retrieved. Default is "all".

    Returns:
    tuple: A tuple containing the generated response as a string and the context string.
    """

    context = ""
    for source in retrieved_documents:
        context += f"Abstract n°{source['id']}: " + source['title'] + "." + "\n\n" + source['abstract'] + "\n\n"
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
    pattern = r'\{+.*\}'
    match = re.findall(pattern, chat_response['message']['content'], re.DOTALL)[0]
    if match:
        match = match.replace("\n", "")
        response = json.loads(match)['response']
    else:
        response = "I can't answer with the provided context"
    print("la réponse est: ", response, flush=True)
    return response, retrieved_documents


@error_handling
def rank_doc(query, retrieved_docs, topN):
    """
    Rank the retrieved medical documents based on their relevance to the query.

    This function takes a query string and a list of retrieved medical documents and returns
    the topN most relevant documents based on their relevance to the query. The relevance is
    determined by a cross-encoder model that takes the query and the title + abstract of
    each document as input and outputs a relevance score.

    Parameters:
    query (str): The query string to be answered.
    retrieved_docs (list): A list of dictionaries, each containing 'title' and 'abstract' 
                            keys representing the retrieved medical documents.
    topN (int): The number of top documents to return.

    Returns:
    list: A list of dictionaries containing the topN most relevant documents, each with
          'title', 'abstract', 'id', and 'score' keys.
    """
    text = [{"id":hit.meta.id, "title":hit.title, "abstract":hit.abstract} for hit in retrieved_docs]
    reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
    scores = reranker.predict([[query, doc["title"] + " " + doc["abstract"]] for doc in text])
    scores = [float(score) for score in scores]
    top_indices = np.argsort(scores)[::-1][:topN]
    top_pairs = [{**text[index], "score": scores[index]} for index in top_indices]
    return top_pairs  


def function_calling(query, model):
    """
    Call a function based on its name and parameters.

    This function takes a query string and a function name and parameters and returns the result
    of the called function.

    Parameters:
    query (str): The query string to be answered.
    function_name (str): The name of the function to be called.
    function_parameters (dict): A dictionary containing the parameters for the function.

    Returns:
    str: The result of the called function.
    """

    file_path = "data/text/PS_LibreAcces_Personne_activite_202503110953.txt"
    df = pd.read_csv(file_path, sep="|", dtype=str) 
    code = '''def analyze_health_data(patients):
    from statistics import mean
    bmi_list = []
    for p in patients:
        bmi = p["weight"] / (p["height"] ** 2)
        bmi_list.append(bmi)
    return {
        "average_age": mean([p["age"] for p in patients]),
        "average_bmi": round(mean(bmi_list), 2),
        "bmi_values": [round(b, 2) for b in bmi_list]
    }
    '''

    system_prompt = """
    You are an AI assistant.
    Your job is to reply to questions related to the pubmed database.
    The pubmed data model represents a list of articles, their authors, and their affiliations.

    To answer user questions, you have one tool at your disposal.

    Firstly, a function called "get_sql_schema_of_table" which has a single parameter named "table" whose value is an element
    of the following list: ["Authors", "Article", "Authorship", "Article_authors"].

    A function called "run_sql_query" which has a single parameter named "sql_code".
    It will run SQL code on the pubmed database. The SQL dialect is PostgreSQL.

    For a given question, your job is to:
    1. Get the schemas of the tables that might help you answer the question using the "get_sql_schema_of_table" function.
    2. Run a PostgreSQL query on the relevant tables using the "run_sql_query" function.
    3. Answer the user based on the result of the SQL query.

    You will always remain factual, you will not hallucinate, and you will say that you don't know if you don't know.
    You will politely ask the user to shoot another question if the question is not related to the pubmed database.
    """

    # def run_sql_query(sql_code):
    #     """
    #     Executes the given SQL query against the database and returns the results.

    #     Args:
    #         sql_code (str): The SQL query to be executed.

    #     Returns:
    #         result: The results of the SQL query.
    #     """
    #     db = SQLDatabase.from_uri(os.getenv("DATABASE_URL"))
    #     return db.run(sql_code)


    def get_sql_schema_of_table(table):
        """
        Returns the SQL CREATE TABLE statement for a Django model mapped to a PostgreSQL table.

        Args:
            table (str): Name of the table (case-sensitive, Django model name)

        Returns:
            str: SQL CREATE TABLE statement or error message
        """
        if table == "Affiliations":
            return """The table Affiliations was created with the following code:

        CREATE TABLE "Affiliations" (
            "id" serial PRIMARY KEY,
            "name of affiliation" text
        );
            """

        if table == "Authors":
            return """The table Authors was created with the following code:

        CREATE TABLE "Authors" (
            "id" serial PRIMARY KEY,
            "name of author" varchar(2000)
        );
            """

        if table == "Article":
            return """The table Article was created with the following code:

        CREATE TABLE "Article" (
            "id" serial PRIMARY KEY,
            "title of review" varchar(2000),
            "date of publication" date,
            "title of article" varchar(2000),
            "abstract" text,
            "pubmed id" integer,
            "doi" varchar(200),
            "conflict of interest" text,
            "mesh terms" text,
            "url" varchar(200),
            "term" varchar(200)
        );
            """

        if table == "Authorship":
            return """The table Authorship was created with the following code:

        CREATE TABLE "Authorship" (
            "id" serial PRIMARY KEY,
            "article_id" integer NOT NULL REFERENCES "Article" ("id") ON DELETE CASCADE,
            "author_id" integer NOT NULL REFERENCES "Authors" ("id") ON DELETE CASCADE,
            "affiliation_id" integer NOT NULL REFERENCES "Affiliations" ("id") ON DELETE CASCADE,
            UNIQUE ("article_id", "author_id", "affiliation_id")
        );
            """

        if table == "Article_authors":  
            return """The table Article_authors was created with the following code:

        CREATE TABLE "Article_authors" (
            "id" serial PRIMARY KEY,
            "article_id" integer NOT NULL REFERENCES "Article" ("id") ON DELETE CASCADE,
            "authors_id" integer NOT NULL REFERENCES "Authors" ("id") ON DELETE CASCADE
        );
            """
        return f"The table {table} does not exist in the schema."

    

    def filter_name_general_practitioners(df, commune):
        if commune in df["Libellé commune (coord. structure)"].unique():
            print({'nom_médecin': df["Nom d'exercice"][df['Libellé commune (coord. structure)'] == "Versailles"].head(5).tolist()})
            return json.dumps({'nom_médecin': df["Nom d'exercice"][df['Libellé commune (coord. structure)'] == commune].head(5).tolist()})
        return json.dumps({'erreur': 'Commune introuvable'})


    def filter_count_general_practitioners(df, commune):
        if commune in df["Libellé commune (coord. structure)"].unique():
            print({'nombre_médecin': int(df["Nom d'exercice"][df['Libellé commune (coord. structure)'] == "Versailles"].count())})
            return json.dumps({'nombre_medecin': int(df["Nom d'exercice"][df['Libellé commune (coord. structure)'] == commune].count())})
        return json.dumps({'erreur': 'Commune introuvable'})


    def filter_id_number_general_practitioners(df, nom):
        if nom in df["Nom d'exercice"].unique():
            print({'identifiant': df["Identification nationale PP"][df["Nom d'exercice"] == "LEGER"].head(1).tolist()})
            return json.dumps({'identifiant': df["Identification nationale PP"][df["Nom d'exercice"] == nom].head(1).tolist()})
        return json.dumps({'erreur': 'Nom introuvable'})
    

    def analyze_health_data(code: str, patients: list):
        local_vars = {}
        exec(code, {}, local_vars)  # Exécute le code, remplit local_vars avec la fonction `run`
        if "run" not in local_vars:
            raise ValueError("Function 'run' not defined in snippet.")
        return local_vars["run"](patients) 
    
    tools = [
        {
            "type": "function",
            "function":{
            "name": "filter_name_general_practitioners",
            "description": "Filtre le nom des médecin généralistes par commune",
            "parameters": {
                "type": "object",
                "properties": {
                    "commune": {
                        "type": "string",
                        "description": "Nom de la commune"
                        }
                    },
                "required": ["commune"]
                }
            }
        },
        {
            "type": "function",
            "function":{
            "name": "filter_count_general_practitioners",
            "description": "Filtre le nombre des médecin généralistes par commune",
            "parameters": {
                "type": "object",
                "properties": {
                    "commune": {
                        "type": "string",
                        "description": "Nom de la commune"
                        }
                    },
                "required": ["commune"]
                }
            }
        },
        {
            "type": "function",
            "function":{
            "name": "get_quartiers_osm",
            "description": "Filtre les quartiers par commune",
            "parameters": {
                "type": "object",
                "properties": {
                    "commune": {
                        "type": "string",
                        "description": "Nom de la commune"
                        }
                    },
                "required": ["commune"]
                }
            }
        },
        {
            "type": "function",
            "function":{
            "name": "filter_id_number_general_practitioners",
            "description": "Filtre l'identifiant des médecin-Generalistes par nom",
            "parameters": {
                "type": "object",
                "properties": {
                    "nom": {
                        "type": "string",
                        "description": "Nom du médecin-Generalistes"
                        }
                    },
                "required": ["nom"]
                }
            }
        },
        {
            "type": "function",
            "function": {
            "name": "analyze_health_data",
            "description": "Analyse un ensemble de données de santé et retourne des statistiques clés.",
            "parameters": {
                "type": "object",
                "properties": {
                    "patients": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "age": {"type": "integer", "description": "Age du patient"},
                            "weight": {"type": "number", "description": "Poids du patient"},
                            "height": {"type": "number", "description": "Taille du patient"}
                            },
                            "required": ["age", "weight", "height"]
                            },
                            "description": "Liste de patients avec âge, poids (kg) et taille (m)"
                        }
                    },
                    "required": ["patients"]
                }
            }
        }
        

        # {
        # "type": "function",
        # "function": {
        #     "name": "get_sql_schema_of_table",
        #     "description": "Get the schema of a table in the pubmed database",
        #     "parameters": {
        #         "type": "object",
        #         "properties": {
        #             "table": {
        #                 "type": "string",
        #                 "enum": ["Authors", "Article", "Authorship", "Article_authors"],
        #                 "description": "The question asked by the user",
        #                 },
        #             },
        #         "required": ["table"],
        #         },
        #     },
        # },
        # {
        #     "type": "function",
        #     "function": {
        #         "name": "run_sql_query",
        #         "description": "Run an SQL query on the pubmed database",
        #         "parameters": {
        #             "type": "object",
        #             "properties": {
        #                 "sql_code": {
        #                     "type": "string",
        #                     "description": "SQL code to be run",
        #                 },
        #             },
        #             "required": ["sql_code"],
        #         },
        #     },
        # }
    ]
    names_to_functions = {
        "filter_name_general_practitioners": functools.partial(filter_name_general_practitioners, df),
        "filter_count_general_practitioners": functools.partial(filter_count_general_practitioners, df),
        "filter_id_number_general_practitioners": functools.partial(filter_id_number_general_practitioners, df),
        "generate_statistics": functools.partial(analyze_health_data, code),
        "get_sql_schema_of_table": functools.partial(get_sql_schema_of_table),
        # "run_sql_query": functools.partial(run_sql_query),
    }
    for attempt in range(1,4):
        try:
            print('api ollama mistral call')
            messages = [{"role":"system", "content": "Tu dois toujours utiliser les fonctions pour répondre"}, {"role": "user", "content": query}]
            data =  {
                    "model": model,
                    "messages": messages,
                    "tools": tools,
                    "stream": False,
                    "echo": False,
                    "max_tokens": 5000,
                    "temperature": 0,
                    "top_p": 1e-6,
                    "top_k": -1,
                    "logprobs": None,
                    "n": 1,
                    "best_of": 1,
                    "use_beam_search": False,
                    "seed":42,
            }

            response = requests.post('http://ollama:11434/api/chat', json=data).json()
            print("response :", response, flush=True)
            messages.append(response["message"])
            tool_call = response["message"]["tool_calls"][0]
            function_name = tool_call["function"]["name"]
            try:
                function_params = json.loads(tool_call["function"]["arguments"])
            except:
                function_params = tool_call["function"]["arguments"]
            print("function_params: ", function_params, flush=True)
            function_result = names_to_functions[function_name](**function_params)
            print("function_result: ", function_result, flush=True)
            if isinstance(function_result, dict):
                function_result = json.dumps(function_result)
            messages.append({"role": "tool", "name": function_name, "content": function_result})
            print(messages)
            data = {
                "model": model,
                "messages": messages,
                "stream": False
            }
            print(type(data), flush=True)
            response = requests.post('http://ollama:11434/api/chat', json=data).json()
            print("===============\n", response, flush=True)
            response = response["message"]["content"]
            print("===============\n", response, flush=True)
            return response
        except Exception as e:
            print(f"Mistral API call failed with error: {e}", flush=True)
    return response["message"]["content"]
    

# def function_calling(query, model, verbose=True):
    # """
    # Call a function based on its name and parameters.

    # This function takes a query string and a function name and parameters and returns the result
    # of the called function.

    # Parameters:
    # query (str): The query string to be answered.
    # function_name (str): The name of the function to be called.
    # function_parameters (dict): A dictionary containing the parameters for the function.

    # Returns:
    # str: The result of the called function.
    # """

    # file_path = "data/text/PS_LibreAcces_Personne_activite_202503110953.txt"
    # df = pd.read_csv(file_path, sep="|", dtype=str) 


    # def filter_name_general_practitioners(df, commune):
    #     if commune in df["Libellé commune (coord. structure)"].unique():
    #         print({'nom_médecin': df["Nom d'exercice"][df['Libellé commune (coord. structure)'] == "Versailles"].head(5).tolist()})
    #         return json.dumps({'nom_médecin': df["Nom d'exercice"][df['Libellé commune (coord. structure)'] == commune].head(5).tolist()})
    #     return json.dumps({'erreur': 'Commune introuvable'})


    # def filter_count_general_practitioners(df, commune):
    #     if commune in df["Libellé commune (coord. structure)"].unique():
    #         print({'nombre_médecin': int(df["Nom d'exercice"][df['Libellé commune (coord. structure)'] == "Versailles"].count())})
    #         return json.dumps({'nombre_medecin': int(df["Nom d'exercice"][df['Libellé commune (coord. structure)'] == commune].count())})
    #     return json.dumps({'erreur': 'Commune introuvable'})


    # def filter_id_number_general_practitioners(df, nom):
    #     if nom in df["Nom d'exercice"].unique():
    #         print({'identifiant': df["Identification nationale PP"][df["Nom d'exercice"] == "LEGER"].head(1).tolist()})
    #         return json.dumps({'identifiant': df["Identification nationale PP"][df["Nom d'exercice"] == nom].head(1).tolist()})
    #     return json.dumps({'erreur': 'Nom introuvable'})
    
    
    # def run_sql_query(sql_code):
    #     """
    #     Executes the given SQL query against the database and returns the results.

    #     Args:
    #         sql_code (str): The SQL query to be executed.

    #     Returns:
    #         result: The results of the SQL query.
    #     """
    #     db = SQLDatabase.from_uri(os.getenv("DATABASE_URL"))
    #     return db.run(sql_code)


    # def get_sql_schema_of_table(table):
    #     """
    #     Returns the SQL CREATE TABLE statement for a Django model mapped to a PostgreSQL table.

    #     Args:
    #         table (str): Name of the table (case-sensitive, Django model name)

    #     Returns:
    #         str: SQL CREATE TABLE statement or error message
    #     """
    #     if table == "Affiliations":
    #         return """The table Affiliations was created with the following code:

    #     CREATE TABLE "Affiliations" (
    #         "id" serial PRIMARY KEY,
    #         "name of affiliation" text
    #     );
    #         """

    #     if table == "Authors":
    #         return """The table Authors was created with the following code:

    #     CREATE TABLE "Authors" (
    #         "id" serial PRIMARY KEY,
    #         "name of author" varchar(2000)
    #     );
    #         """

    #     if table == "Article":
    #         return """The table Article was created with the following code:

    #     CREATE TABLE "Article" (
    #         "id" serial PRIMARY KEY,
    #         "title of review" varchar(2000),
    #         "date of publication" date,
    #         "title of article" varchar(2000),
    #         "abstract" text,
    #         "pubmed id" integer,
    #         "doi" varchar(200),
    #         "conflict of interest" text,
    #         "mesh terms" text,
    #         "url" varchar(200),
    #         "term" varchar(200)
    #     );
    #         """

    #     if table == "Authorship":
    #         return """The table Authorship was created with the following code:

    #     CREATE TABLE "Authorship" (
    #         "id" serial PRIMARY KEY,
    #         "article_id" integer NOT NULL REFERENCES "Article" ("id") ON DELETE CASCADE,
    #         "author_id" integer NOT NULL REFERENCES "Authors" ("id") ON DELETE CASCADE,
    #         "affiliation_id" integer NOT NULL REFERENCES "Affiliations" ("id") ON DELETE CASCADE,
    #         UNIQUE ("article_id", "author_id", "affiliation_id")
    #     );
    #         """

    #     if table == "Article_authors":  
    #         return """The table Article_authors was created with the following code:

    #     CREATE TABLE "Article_authors" (
    #         "id" serial PRIMARY KEY,
    #         "article_id" integer NOT NULL REFERENCES "Article" ("id") ON DELETE CASCADE,
    #         "authors_id" integer NOT NULL REFERENCES "Authors" ("id") ON DELETE CASCADE
    #     );
    #         """
    #     return f"The table {table} does not exist in the schema."


    
    # tools = [
    #     {
    #         "type": "function",
    #         "function":{
    #         "name": "filter_name_general_practitioners",
    #         "description": "Filtre le nom des médecin généralistes par commune",
    #         "parameters": {
    #             "type": "object",
    #             "properties": {
    #                 "commune": {
    #                     "type": "string",
    #                     "description": "Nom de la commune"
    #                     }
    #                 },
    #             "required": ["commune"]
    #             }
    #         }
    #     },
    #     {
    #         "type": "function",
    #         "function":{
    #         "name": "filter_count_general_practitioners",
    #         "description": "Filtre le nombre des médecin généralistes par commune",
    #         "parameters": {
    #             "type": "object",
    #             "properties": {
    #                 "commune": {
    #                     "type": "string",
    #                     "description": "Nom de la commune"
    #                     }
    #                 },
    #             "required": ["commune"]
    #             }
    #         }
    #     },
    #     {
    #         "type": "function",
    #         "function":{
    #         "name": "get_quartiers_osm",
    #         "description": "Filtre les quartiers par commune",
    #         "parameters": {
    #             "type": "object",
    #             "properties": {
    #                 "commune": {
    #                     "type": "string",
    #                     "description": "Nom de la commune"
    #                     }
    #                 },
    #             "required": ["commune"]
    #             }
    #         }
    #     },
    #     {
    #         "type": "function",
    #         "function":{
    #         "name": "filter_id_number_general_practitioners",
    #         "description": "Filtre l'identifiant des médecin-Generalistes par nom",
    #         "parameters": {
    #             "type": "object",
    #             "properties": {
    #                 "nom": {
    #                     "type": "string",
    #                     "description": "Nom du médecin-Generalistes"
    #                     }
    #                 },
    #             "required": ["nom"]
    #             }
    #         }
    #     },
    #      {
    #         "type": "function",
    #         "function": {
    #             "name": "get_sql_schema_of_table",
    #             "description": "Get the schema of a table in the pubmed database",
    #             "parameters": {
    #                 "type": "object",
    #                 "properties": {
    #                     "table": {
    #                         "type": "string",
    #                         "enum": ["Authors", "Article", "Authorship", "Article_authors"],
    #                         "description": "The question asked by the user",
    #                     },
    #                 },
    #                 "required": ["table"],
    #             },
    #         },
    #     },
    #     {
    #         "type": "function",
    #         "function": {
    #             "name": "run_sql_query",
    #             "description": "Run an SQL query on the pubmed database",
    #             "parameters": {
    #                 "type": "object",
    #                 "properties": {
    #                     "sql_code": {
    #                         "type": "string",
    #                         "description": "SQL code to be run",
    #                     },
    #                 },
    #                 "required": ["sql_code"],
    #             },
    #         },
    #     }
    # ]

    # names_to_functions = {
    #     "filter_name_general_practitioners": functools.partial(filter_name_general_practitioners, df),
    #     "filter_count_general_practitioners": functools.partial(filter_count_general_practitioners, df),
    #     "filter_id_number_general_practitioners": functools.partial(filter_id_number_general_practitioners, df)
    # }

    # system_prompt = """
    # You are an AI assistant.
    # Your job is to reply to questions related to the pubmed database.
    # The pubmed data model represents a list of articles, their authors, and their affiliations.

    # To answer user questions, you have one tool at your disposal.

    # Firstly, a function called "get_sql_schema_of_table" which has a single parameter named "table" whose value is an element
    # of the following list: ["Authors", "Article", "Authorship", "Article_authors"].

    # A function called "run_sql_query" which has a single parameter named "sql_code".
    # It will run SQL code on the pubmed database. The SQL dialect is PostgreSQL.

    # For a given question, your job is to:
    # 1. Get the schemas of the tables that might help you answer the question using the "get_sql_schema_of_table" function.
    # 2. Run a SQLite query on the relevant tables using the "run_sql_query" function.
    # 3. Answer the user based on the result of the SQL query.

    # You will always remain factual, you will not hallucinate, and you will say that you don't know if you don't know.
    # You will politely ask the user to shoot another question if the question is not related to the pubmed database.
    # """

    # messages = [
    #     {
    #         "role": "system",
    #         "content": system_prompt
    #     },
    #     {
    #         "role": "user",
    #         "content": query
    #     }
    # ]

    # used_run_sql = False
    # used_get_sql_schema_of_table = False
    # # Function to determine tool choice based on usage
    # def tool_choice(used_run_sql, used_get_sql_schema_of_table):
    #     # If the question is out of topic the agent is not expected to run a tool call
    #     if not used_get_sql_schema_of_table:
    #         return "auto"
    #     # The agent is expected to run "used_run_sql" after getting the specifications of the tables of interest
    #     if used_get_sql_schema_of_table and not used_run_sql:
    #         return "any"
    #     # The agent is not expected to run a tool call after querying the SQL table
    #     if used_run_sql and used_get_sql_schema_of_table:
    #         return "none"
    #     return "auto"
    # iteration = 0
    # max_iteration = 2
    # try:
    #     while iteration < max_iteration:
    #         data =  {
    #                 "model": model,
    #                 "messages": messages,
    #                 "tools": tools,
    #                 "stream": False,
    #                 "echo": False,
    #                 "max_tokens": 5000,
    #                 "temperature": 0,
    #                 "top_p": 1e-6,
    #                 "top_k": -1,
    #                 "logprobs": None,
    #                 "n": 1,
    #                 "best_of": 1,
    #                 "use_beam_search": False,
    #                 "seed":42,
    #                 "tool_choice": tool_choice(used_run_sql, used_get_sql_schema_of_table)
    #         }

    #         response = requests.post('http://ollama:11434/api/chat', json=data).json()
    #         print("response :", response, flush=True)
    #         messages.append(response["message"])
    #         tool_calls = response["message"]["tool_calls"]
    #         if not tool_calls:
    #             if verbose:
    #                 print(f"Assistant: {response['message']['content']}\n")
    #             return response["message"]["content"]
    #         for tool_call in tool_calls:
    #             function_name = tool_call["function"]["name"]
    #             print("function_params: ", tool_call["function"]["arguments"], flush=True)
    #             try:
    #                 function_params = json.loads(tool_call["function"]["arguments"])
    #             except:
    #                 function_params = tool_call["function"]["arguments"]
    #             if function_name == "get_sql_schema_of_table":
    #                 function_result = get_sql_schema_of_table(function_params['table'])
    #                 if verbose:
    #                     print(f"Tool: Getting SQL schema of table {function_params['table']}\n")
    #                 used_get_sql_schema_of_table = True
    #             elif function_name == "run_sql_query":
    #                 function_result = run_sql_query(function_params['sql_code'])
    #                 if verbose:
    #                     print(f"Tool: Running code {function_params['sql_code']}\n")
    #                 used_run_sql = True
    #             else:
    #                 function_result = names_to_functions[function_name](**function_params)
    #             print("function_result: ", function_result, flush=True)
    #             if isinstance(function_result, dict):
    #                 function_result = json.dumps(function_result)
    #             messages.append({"role": "tool", "name": function_name, "content": function_result, "tool_call_id": tool_call["id"]})
    #             print(messages)
    #         iteration += 1
    #     print("===============\n", response, flush=True)
    #     return response["message"]["content"]
    # except Exception as e:
    #         print(f"Mistral API call failed with error: {e}", flush=True)
    #         response = {}
    #         return response
    
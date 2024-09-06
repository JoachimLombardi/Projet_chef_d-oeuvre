# from django.shortcuts import render
# from django.http import HttpResponse
import re
from django.http import HttpResponse
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
from dateutil import parser
from .models import Review, Article, Cited_by

# def index(request):
#     return HttpResponse("Hello, world. You're at the polls index.")

def format_date(date):
    try:
        date_obj = parser.parse(date, fuzzy=True)
        return date_obj
    except ValueError:
        return None


def get_absolute_url(pmid):
    return "https://pubmed.ncbi.nlm.nih.gov/"+str(pmid)


def init_soup(url):
    # Envoyer une requête GET pour récupérer le contenu de la page
    response = requests.get(url)
    # Vérifier que la requête a réussi
    if response.status_code == 200:
    # Parser le contenu HTML avec BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
    return soup


def extract_review_url(url='https://www.journalsinsights.com/journals/'):
    links = []
    # We iter 110 times to get all the journals with a step of 20
    for i in range(0, 2180, 20):
        soup = init_soup(url+str(i))
        list_reviews = soup.select('div.abbreviation_box') 
        for review in list_reviews:
            links.extend([a['href'] for a in review.find_all('a', href=True)])
        time.sleep(1)
    pattern_to_exclude = re.compile(r"https://www\.journalsinsights\.com/journals/(\d+)?$")
    filtered_links = [link for link in links if not pattern_to_exclude.match(link)]
    return filtered_links


def extract_reviews_info(request):
    links = extract_review_url() 
    for link in links: 
        soup = init_soup(link)
        title = soup.find('td', string='Journal title').find_next_sibling('td').text.strip() if soup.find('td', string='Journal title') else None
        abbreviation = soup.find('td', string='Abbreviation').find_next_sibling('td').text.strip() if soup.find('td', string='Abbreviation') else None
        online_issn_td = soup.find('td', string='Online ISSN')
        issn = online_issn_td.find_next_sibling('td').text.strip() if online_issn_td else None
        # Trouver le titre "Impact Factor"
        title_h2 = soup.find('h2', string='Impact Factor')
        # Trouver le parent div du titre
        impact_factor_div = title_h2.find_parent('div', class_='col-md-12') if title_h2 else None
        # Trouver le chiffre en gras
        impact_factor = impact_factor_div.find('b').text.strip() if impact_factor_div else None
        Review.objects.create(title=title, abbreviation=abbreviation, issn=issn, impact_factor=impact_factor)
        time.sleep(1)
    return HttpResponse("Review scraped with success.")


def extract_authors_affiliations(url):
    soup = init_soup(url)
    authors = soup.select('.authors-list-item')
    author_affiliations = []
    for author in authors:
        # Extract author name
        author_name = author.select_one('.full-name').get_text(strip=True)
        # Extract affiliation
        affiliation_elements = author.select('.affiliation-link')
        affiliations = [affil.get('title') for affil in affiliation_elements]
        author_affiliations.append(author_name + '|' + " ".join(affiliations))
    return author_name, author_affiliations

def extract_pubmed_url(base_url, term="multiple_sclerosis", filter="2024"):
    links = []
    url = base_url+"/"+"?term="+term+"&filter=years."+filter+"-2025"
    soup = init_soup(url)
    page_max = int(soup.select_one('label.of-total-pages').get_text(strip=True).split(" ")[-1]) if soup.select_one('label.of-total-pages') else 1
    for i in range(1, 2, 1):
        list_articles = soup.select('div.search-results-chunk')
        for article in list_articles:
            links.extend([base_url+a['href'] for a in article.find_all('a', href=True)][:10])
        time.sleep(1)
        soup = init_soup(url+"&page="+str(i))
    print(links)
    return links

def extract_article_info(request, base_url='https://pubmed.ncbi.nlm.nih.gov'):
    links = extract_pubmed_url(base_url)
    for link in links:
        # Initialize soup
        soup = init_soup(link)
        # Extract reviews title
        title_review = soup.select_one('button.journal-actions-trigger')['title']
        # Extract date
        date = soup.select_one('span.cit').get_text(strip=True).split(";")[0] if soup.select_one('.cit') else None
        date = format_date(date)
        # Extract title
        title = soup.select_one('h1.heading-title').get_text(strip=True) if soup.select_one('h1.heading-title') else None
        # Extract abstract
        abstract = soup.select('div.abstract-content p')
        abstract = [p.get_text(strip=True) for p in abstract] if abstract else None
        if isinstance(abstract, list):
            abstract = " ".join(abstract)
        # Extract PMID
        pmid = soup.select_one('span.identifier.pubmed strong.current-id').get_text(strip=True) if soup.select_one('span.identifier.pubmed strong.current-id') else None
        # Extract DOI
        doi = soup.select_one('span.identifier.doi a.id-link').get_text(strip=True) if soup.select_one('span.identifier.doi a.id-link') else None
        # Extract conflict of interest statement
        disclosure = soup.select_one('div.conflict-of-interest div.statement p').get_text(strip=True) if soup.select_one('div.conflict-of-interest div.statement p') else None
        # Extract mesh terms
        buttons = soup.select('button.keyword-actions-trigger')
        mesh_terms = [button.get_text(strip=True) for button in buttons] if buttons else None
        author_name, author_affiliations = extract_authors_affiliations(link)
        url = get_absolute_url(pmid)
        # try:
        #     review = Review.objects.get(title=title_review)
        # except Review.DoesNotExist:
        #     pass
        Article.objects.create(title_review=title_review, pub_date=date, title=title, authors=author_name, author_affiliation=author_affiliations, abstract=abstract, pmid=pmid, doi=doi, disclosure=disclosure, mesh_terms=mesh_terms, url=url)
    return HttpResponse("Article scraped with success.")


def extract_cited_by(url='https://pubmed.ncbi.nlm.nih.gov/30920776/'):
    soup = init_soup(url)
    doi_related_article = soup.select_one('span.identifier.doi a.id-link').get_text(strip=True) if soup.select_one('span.identifier.doi a.id-link') else None
    cited = soup.select('.similar-articles .articles-list li.full-docsum')
    cited_articles = []
    for article in cited:
        abbreviation_title_review = article.select_one('.docsum-journal-citation').get_text(strip=True).split(".")[0]
        if "doi" in article.select_one('.docsum-journal-citation').get_text(strip=True):
            doi = article.select_one('.docsum-journal-citation').get_text(strip=True).split("doi:")[-1].replace(".","").split("Epub")[0] if article.select_one('.docsum-journal-citation') else None
        else:
            doi = ""
        pmid = article.select_one('.docsum-pmid').get_text(strip=True) if article.select_one('.docsum-pmid') else None
        try:
            article = Article.objects.get(doi=doi_related_article)
        except Article.DoesNotExist:
            pass
        try:
            review = Review.objects.get(abbreviation=abbreviation_title_review)
        except Review.DoesNotExist:
            pass
        url = get_absolute_url(pmid)
        Cited_by.objects.create(article=article, review=review, doi=doi, pmid=pmid, url=url)
    return cited_articles


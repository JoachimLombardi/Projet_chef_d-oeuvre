# from django.shortcuts import render
# from django.http import HttpResponse
import re
import requests
from bs4 import BeautifulSoup
import time
import random


# def index(request):
#     return HttpResponse("Hello, world. You're at the polls index.")

def init_soup(url):
    # Envoyer une requête GET pour récupérer le contenu de la page
    response = requests.get(url)
    # Vérifier que la requête a réussi
    if response.status_code == 200:
    # Parser le contenu HTML avec BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
    return soup


def extract_pubmed_info(url='https://pubmed.ncbi.nlm.nih.gov/30920776/'):
    # Initialize soup
    soup = init_soup(url)
    # Extract date
    date = soup.select_one('span.cit').get_text(strip=True).split(";")[0] if soup.select_one('.cit') else None
    # Extract title
    title = soup.select_one('h1.heading-title').get_text(strip=True) if soup.select_one('h1.heading-title') else None
    # Extract abstract
    abstract = soup.select('div.abstract-content p')
    abstract = [p.get_text(strip=True) for p in abstract] if abstract else None
    # Extract PMID
    pmid = soup.select_one('span.identifier.pubmed strong.current-id').get_text(strip=True) if soup.select_one('span.identifier.pubmed strong.current-id') else None
    # Extract DOI
    doi = soup.select_one('span.identifier.doi a.id-link').get_text(strip=True) if soup.select_one('span.identifier.doi a.id-link') else None
    # Extract conflict of interest statement
    disclosure = soup.select_one('div.conflict-of-interest div.statement p').get_text(strip=True) if soup.select_one('div.conflict-of-interest div.statement p') else None
    # Extract mesh terms
    buttons = soup.select('button.keyword-actions-trigger')
    mesh_terms = [button.get_text(strip=True) for button in buttons] if buttons else None
    return date, title, abstract, pmid, doi, disclosure, mesh_terms


def extract_authors_affiliations(url='https://pubmed.ncbi.nlm.nih.gov/30920776/'):
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
    return author_affiliations, author_name


def extract_cited_by(url='https://pubmed.ncbi.nlm.nih.gov/30920776/'):
    soup = init_soup(url)
    cited = soup.select('.similar-articles .articles-list li.full-docsum')
    print(len(cited))
    cited_articles = []
    for article in cited:
        if "doi" in article.select_one('.docsum-journal-citation').get_text(strip=True):
            doi = article.select_one('.docsum-journal-citation').get_text(strip=True).split("doi:")[-1].replace(".","").split("Epub")[0] if article.select_one('.docsum-journal-citation') else None
        else:
            doi = ""
        pmid = article.select_one('.docsum-pmid').get_text(strip=True) if article.select_one('.docsum-pmid') else None
        cited_articles.append({'doi': doi, 'pmid': pmid})
    return cited_articles


def extract_review_url(url='https://www.journalsinsights.com/journals/'):
    links = []
    # We iter 110 times to get all the journals with a step of 20
    for i in range(0, 2180, 20):
        soup = init_soup(url+str(i))
        list_reviews = soup.select('div.abbreviation_box') 
        for review in list_reviews:
            links.extend([a['href'] for a in review.find_all('a', href=True)])
        print(links)
        time.sleep(random.uniform(1, 3))
    pattern_to_exclude = re.compile(r"https://www\.journalsinsights\.com/journals/(\d+)?$")
    filtered_links = [link for link in links if not pattern_to_exclude.match(link)]
    return filtered_links


def extract_reviews_info():
    links = "https://www.journalsinsights.com/journals/american-journal-of-criminal-justice/"
    for link in links: 
        soup = init_soup(link)
        title = soup.select_one('h1.title_tag').get_text(strip=True) if soup.select_one('h1.title_tag') else None
        issn = soup.find('td', text='Print ISSN').find_next_sibling('td').text.strip()
        # Trouver le titre "Impact Factor"
        title_h2 = soup.find('h2', text='Impact Factor')
        # Trouver le parent div du titre
        impact_factor_div = title_h2.find_parent('div', class_='col-md-12')
        # Trouver le chiffre en gras
        impact_factor = impact_factor_div.find('b').text.strip()
        print(title, issn, impact_factor)
        time.sleep(1)
    return title, issn, impact_factor

extract_reviews_info()








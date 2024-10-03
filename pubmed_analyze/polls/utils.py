import string
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from sentence_transformers import SentenceTransformer
from dateutil import parser
from django.utils import timezone
import pytz
import requests
from bs4 import BeautifulSoup
from .models import Authors, Affiliations,  Authorship, Cited_by
import time


model = SentenceTransformer('bert-base-nli-mean-tokens')

def format_date(date):
    if date is None:
        return None  # Gérer le cas où l'entrée est None
    try:
        date_obj = parser.parse(date, fuzzy=True)
        if timezone.is_naive(date_obj):
            return timezone.make_aware(date_obj, timezone=timezone.utc)
         # Assurez-vous que le fuseau horaire est valide
        if date_obj.tzinfo:
            date_obj = date_obj.astimezone(pytz.UTC)
        return date_obj
    except (ValueError, OverflowError, pytz.UnknownTimeZoneError):
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
    return None


def get_authors_affiliations(soup, article):
    authors_tags = soup.select('.authors-list-item')
    for author_tag in authors_tags:
        # Extraire le nom de l'auteur
        author_name = author_tag.select_one('.full-name').get_text(strip=True) if author_tag.select_one('.full-name') else None
        if author_name:
            # Récupérer ou créer l'auteur
            author, created = Authors.objects.get_or_create(name=author_name)
            # Extraire les affiliations
            affiliation_elements = author_tag.select('.affiliation-link')
            if affiliation_elements:
                affiliations_names = [affil.get('title', None) for affil in affiliation_elements]
                for affiliation_name in affiliations_names:
                    # Récupérer ou créer l'affiliation
                    affiliation, created = Affiliations.objects.get_or_create(name=affiliation_name)
                    # Vérifier si la relation existe déjà dans Authorship
                    if not Authorship.objects.filter(article=article, author=author, affiliation=affiliation).exists():
                        # Créer la liaison entre l'article, l'auteur et l'affiliation
                        Authorship.objects.create(article=article, author=author, affiliation=affiliation)


def extract_pubmed_url(base_url, term="multiple_sclerosis", filter="2024"):
    links = []
    url = base_url+"/"+"?term="+term+"&filter=years."+filter+"-2025"
    soup = init_soup(url)
    page_max = int(soup.select_one('label.of-total-pages').get_text(strip=True).split(" ")[-1]) if soup.select_one('label.of-total-pages') else 1
    for i in range(1, page_max+1, 1):
        list_articles = soup.select('div.search-results-chunk')
        for article in list_articles:
            links.extend([base_url+a['href'] for a in article.find_all('a', href=True)][:10])
        time.sleep(1)
        soup = init_soup(url+"&page="+str(i))
    return links


def extract_cited_by(soup, article):
    cited_articles = soup.select('.similar-articles .articles-list li.full-docsum')
    for cited_article in cited_articles:
        if "doi" in cited_article.select_one('.docsum-journal-citation').get_text(strip=True):
            doi = cited_article.select_one('.docsum-journal-citation').get_text(strip=True).split("doi:")[-1].replace(".","").split("Epub")[0] if cited_article.select_one('.docsum-journal-citation') else None
            if doi:
                doi = "https://doi.org/"+doi
        else:
            doi = ""
        pmid = cited_article.select_one('.docsum-pmid').get_text(strip=True) if cited_article.select_one('.docsum-pmid') else None
        url = get_absolute_url(pmid)
        if not Cited_by.objects.filter(doi=doi).exists():
            Cited_by.objects.create(article=article, doi=doi, pmid=pmid, url=url)


def lemmatize(text: str):
    try:
        lemmatizer = WordNetLemmatizer()
        word_tokens = word_tokenize(text)
        return [lemmatizer.lemmatize(word) for word in word_tokens]
    except Exception:
        return text.split(" ")
    

def remove_stop_words_and_punctuation(text: str) -> list[str]:
    try:
        stop_words_french = set(stopwords.words("french"))
        stop_words_english = set(stopwords.words("english"))
        stop_words = stop_words_french.union(stop_words_english)
        word_tokens = word_tokenize(text)
        text_trimmed = [
            word
            for word in word_tokens
            if (word.casefold() not in stop_words and word not in string.punctuation)
        ]
        return text_trimmed or word_tokens
    except Exception:
        return text.split(" ")


def query_processing(
    query: str,
) -> str:
    query = " ".join(remove_stop_words_and_punctuation(query))
    query = " ".join(lemmatize(query))
    return query


def get_vector(article):
    title = query_processing(article.title) if article.title is not None else ""
    abstract = query_processing(article.abstract) if article.abstract is not None else ""    
    return model.encode(title + " " + abstract).tolist()
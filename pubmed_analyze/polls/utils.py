import string
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import numpy as np
from sentence_transformers import CrossEncoder, SentenceTransformer
from dateutil import parser
from django.utils import timezone
import pytz
import requests
from bs4 import BeautifulSoup
import time


model = SentenceTransformer('microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract')

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


def extract_pubmed_url(base_url, term="multiple_sclerosis", filter="2024"):
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
    if query:
        query = " ".join(remove_stop_words_and_punctuation(query))
        query = " ".join(lemmatize(query))
        return query


def get_vector(article):
    title = query_processing(article.title) 
    abstract = query_processing(article.abstract)  
    return model.encode(title + " " + abstract).tolist()


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
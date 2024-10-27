from dateutil import parser
from django.utils import timezone
import pytz
import string
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer


def get_absolute_url(pmid):
    return "https://pubmed.ncbi.nlm.nih.gov/"+str(pmid)


def format_date(date):
    if date is None:
        return None  # Gérer le cas où l'entrée est None
    try:
        date_obj = parser.parse(date, fuzzy=True)
        if timezone.is_naive(date_obj):
            return timezone.make_aware(date_obj, timezone=timezone.utc).date()
         # Assurez-vous que le fuseau horaire est valide
        if date_obj.tzinfo:
            return date_obj.astimezone(pytz.UTC).date()
    except (ValueError, OverflowError, pytz.UnknownTimeZoneError):
        return None


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



import re
from dateutil import parser
from django.conf import settings
from django.utils import timezone
import pytz
from django.core.mail import send_mail
import traceback
import logging


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


def clean_whitespace(text: str) -> str:
    """
    Normalizes whitespace by removing excessive spaces, tabs, and newlines.
    """
    return re.sub(r'\s+', ' ', text).strip()


def lowercase_text(text: str) -> str:
    """
    Converts text to lowercase. Only use this if you're working with an uncased BERT model.
    """
    return text.lower()


def remove_noise(text: str) -> str:
    """
    Removes common noise such as HTML tags or URLs, while keeping sentence structure intact.
    """
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Remove URLs
    text = re.sub(r'http\S+|www\S+|https\S+', '', text)
    # Remove extra non-textual characters, keeping punctuation intact
    text = re.sub(r'[^A-Za-z0-9.,;:?!\'"()\[\] ]+', '', text)
    return text


def text_processing(text: str) -> str:
    """
    Cleans and prepares text minimally for BERT encoding.
    """
    text = clean_whitespace(text)
    text = remove_noise(text)
    text = lowercase_text(text)
    return text


def convert_seconds(seconds):
    minutes = round(seconds // 60)  
    remaining_seconds = round(seconds % 60) 
    return f'{minutes} minutes and {remaining_seconds} seconds'


logger = logging.getLogger(__name__)

def handle_error(e):
    """Gère les erreurs en les loguant et en envoyant un email de notification."""
    error_message = str(e)
    # Log de l'erreur avec traceback complet
    logger.error(f"Une erreur est survenue: {error_message}")
    logger.error(traceback.format_exc())
    
    # Envoi d'un email avec les détails de l'erreur
    subject = "Erreur dans l'application"
    message = f"Une erreur s'est produite : {error_message}\n\nTraceback:\n{traceback.format_exc()}"
    recipient_list = settings.ERROR_NOTIFICATION_EMAIL
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list)
from functools import wraps
import re
import subprocess
from dateutil import parser
from django.conf import settings
from django.utils import timezone
from django.core.mail import send_mail
import traceback
import logging

logger = logging.getLogger(__name__)


def handle_error(e):
    """
    Handle an error by sending an email to the developers with the
    error message and the traceback.

    Parameters
    ----------
    e : Exception
        The exception to handle
    """
    error_message = str(e)
    logger.error(f"Une erreur est survenue: {error_message}")
    logger.error(traceback.format_exc())
    subject = "Erreur dans l'application pubmed analyze"
    message = f"Une erreur s'est produite : {error_message}\n\n{traceback.format_exc()}"
    recipient_list = settings.ERROR_NOTIFICATION_EMAIL
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list)


def error_handling(func):
    """
    A decorator that handles any exception that might be raised by the
    decorated function.

    If an exception is raised, it is handled by sending an email to the
    developers with the error message and the traceback.

    Parameters
    ----------
    func : callable
        The function to decorate

    Returns
    -------
    callable
        The decorated function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        """
        A wrapper around a function that handles any exception raised by the
        function.

        If an exception is raised, it is handled by sending an email to the
        developers with the error message and the traceback.

        Parameters
        ----------
        *args : tuple
            The arguments to pass to the decorated function
        **kwargs : dict
            The keyword arguments to pass to the decorated function

        Returns
        -------
        object
            The result of the decorated function if it does not raise an
            exception, None otherwise
        """

        try:
            return func(*args, **kwargs)
        except Exception as e:
            handle_error(e)
    return wrapper


def get_absolute_url(pmid):
    """
    Get the absolute URL of an article on PubMed from its PMID.

    Parameters
    ----------
    pmid : str or int
        The PubMed ID of the article

    Returns
    -------
    str
        The absolute URL of the article on PubMed
    """
    return "https://pubmed.ncbi.nlm.nih.gov/"+str(pmid)


@error_handling
def format_date(date):
    """
    Format a date string into a datetime.date object.

    Parameters
    ----------
    date : str or None
        The date string to format

    Returns
    -------
    datetime.date or None
        The formatted date if the input is not None, None otherwise
    """
    if date is None:
        return None  
    date_obj = parser.parse(date, fuzzy=True)
    if timezone.is_naive(date_obj):
        return timezone.make_aware(date_obj, timezone=timezone.get_default_timezone()).date()
    if date_obj.tzinfo:
        return date_obj.astimezone(timezone.get_default_timezone()).date()


def clean_whitespace(text: str) -> str:
    """
    Cleans up whitespace in a given text string.

    This function replaces multiple consecutive whitespace characters
    (spaces, tabs, newlines) with a single space and then strips any
    leading or trailing whitespace from the string.

    Parameters
    ----------
    text : str
        The input string to clean.

    Returns
    -------
    str
        The cleaned string with normalized whitespace.
    """

    return re.sub(r'\s+', ' ', text).strip()


def lowercase_text(text: str) -> str:
    """
    Lowercases a given text string.

    Parameters
    ----------
    text : str
        The input string to lowercase.

    Returns
    -------
    str
        The lowercased string.
    """

    return text.lower()


def remove_noise(text: str) -> str:
    """
    Removes noise from a given text string.

    This function removes HTML tags, URLs, and all non-alphanumeric characters
    (except for spaces, punctuation, and a few special characters) from the
    input string.

    Parameters
    ----------
    text : str
        The input string to clean.

    Returns
    -------
    str
        The cleaned string with noise removed.
    """
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'http\S+|www\S+|https\S+', '', text)
    text = re.sub(r'[^A-Za-z0-9.,;:?!\'"()\[\] ]+', '', text)
    return text


def text_processing(text: str) -> str:
    """
    Applies a series of preprocessing steps to a given text string.

    Parameters
    ----------
    text : str
        The input string to preprocess.

    Returns
    -------
    str
        The preprocessed string after applying the following steps:

        1. remove_noise: removes HTML tags, URLs, and all non-alphanumeric
           characters (except for spaces, punctuation, and a few special
           characters)
        2. clean_whitespace: replaces multiple consecutive whitespace
           characters with a single space and strips any leading or trailing
           whitespace
        3. lowercase_text: lowercases the string
    """
    text = clean_whitespace(text)
    text = remove_noise(text)
    text = lowercase_text(text)
    return text


def convert_seconds(seconds):
    """
    Converts a given number of seconds to a string in the format of "minutes 
    and seconds".

    Parameters
    ----------
    seconds : int
        The number of seconds to convert.

    Returns
    -------
    str
        The converted string in the format "minutes and seconds".
    """
    minutes = round(seconds // 60)  
    remaining_seconds = round(seconds % 60) 
    return f'{minutes} minutes and {remaining_seconds} seconds'





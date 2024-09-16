# from django.shortcuts import render
import re
from django.http import HttpResponse
import requests
from bs4 import BeautifulSoup
import time
from dateutil import parser
from .models import Authors, Affiliations, Article, Articles_authors_affiliations, Cited_by
from django.utils import timezone
import pytz
from django.shortcuts import render, redirect
from .forms import AffiliationForm, ArticleForm,  AuthorAffiliationForm, AuthorAffiliationFormSet, AuthorForm


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


def extract_authors(soup):
    authors = soup.select('.authors-list-item')
    # Extract author name
    author_names = [author.select_one('.full-name').get_text(strip=True) for author in authors]
    return author_names


def extract_affiliations(soup):
    affiliations = soup.select('.affiliations ul.item-list li')
    affiliation_list = [affil.get_text(strip=True) for affil in affiliations]
    # Remove first number from affiliation list with regex
    affiliation_list = [re.sub(r'^\d+', '', affil) for affil in affiliation_list]
    return affiliation_list


def get_authors_affiliations_numbers(url, article_number):
    soup = init_soup(url)
    authors = soup.select('.authors-list-item')
    for author in authors:
        # Extract author name
        author_name = author.select_one('.full-name').get_text(strip=True) if author.select_one('.full-name') else None
        if author_name:
            try:
                author_number = Authors.objects.get(name=author_name)
            except Authors.DoesNotExist:
                author_number = None
        else:
            author_number = None
        # Extract affiliation
        affiliation_elements = author.select('.affiliation-link')
        if affiliation_elements:
            affiliations_names = [affil.get('title', None) for affil in affiliation_elements]
            for affiliation_name in affiliations_names:
                try:
                    affiliation_number = Affiliations.objects.get(name=affiliation_name)
                except Affiliations.DoesNotExist:
                    affiliation_number = None
                if not Articles_authors_affiliations.objects.filter(article=article_number, author=author_number, affiliation=affiliation_number).exists():
                    Articles_authors_affiliations.objects.create(article=article_number, author=author_number, affiliation=affiliation_number)
    return HttpResponse("Authors and affiliations scraped with success.")


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


def extract_article_info(request, base_url='https://pubmed.ncbi.nlm.nih.gov'):
    links = extract_pubmed_url(base_url)
    authors = []
    affiliations = []
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
        author_names = extract_authors(soup)
        authors.extend(author_names)
        affiliation_names = extract_affiliations(soup)
        affiliations.extend(affiliation_names)
        url = get_absolute_url(pmid)
        if not Article.objects.filter(doi=doi).exists():
           article = Article.objects.create(title_review=title_review, pub_date=date, title=title, abstract=abstract, pmid=pmid, doi=doi, disclosure=disclosure, mesh_terms=mesh_terms, url=url)
           extract_cited_by(soup, article)
    # Remove duplicate authors
    authors = list(set(authors))
    for author in authors:
        if not Authors.objects.filter(name=author).exists():
            Authors.objects.create(name=author)
    # Remove duplicate affiliations
    affiliations = list(set(affiliations))
    for affiliation in affiliations:
        if not Affiliations.objects.filter(name=affiliation).exists():
            Affiliations.objects.create(name=affiliation)
    return HttpResponse("Article, authors, affiliations and cited_by scraped with success.")


def extract_articles_authors_affiliations(request):
    articles = Article.objects.all()
    for article in articles:
        get_authors_affiliations_numbers(article.url, Article.objects.get(doi=article.doi))
    return HttpResponse("Authors and affiliation created with success.")


def create_article(request):
    if request.method == 'POST':
        article_form = ArticleForm(request.POST)
        formset = AuthorAffiliationFormSet(request.POST)
        if article_form.is_valid() and formset.is_valid():
            author_affiliation_data = [
                {
                    'author_name': form.cleaned_data.get('author_name'),
                    'affiliations': form.cleaned_data.get('affiliations')
                }
                for form in formset
            ]
            # Use the save method from ArticleForm to handle saving the article with authors and affiliations
            article_form.save_article_with_authors(author_affiliation_data)
            return redirect('article_list')
    else:
        article_form = ArticleForm()
        formset = AuthorAffiliationFormSet()
    return render(request, 'polls/create_article.html', {'article_form': article_form, 'formset': formset})


def article_list(request):
    articles = Article.objects.all()
    context = {'articles': articles}
    return render(request, 'polls/article_list.html', context)


def update_article(request, id):
    article = Article.objects.get(id=id)
    if request.method == 'POST':
        form = ArticleForm(request.POST, instance=article)
        if form.is_valid():
            form.save()
            return redirect('article_list')
    else:
        form = ArticleForm(instance=article)
    context = {'form': form}
    return render(request, 'polls/article_form.html', context)


def delete_article(request, id):
    article = Article.objects.get(id=id)
    if request.method == 'POST':
        article.delete()
        return redirect('article_list')
    context = {'article': article}
    return render(request, 'polls/article_confirm_delete.html', context)


def author_list(request):
    authors = Authors.objects.all()
    context = {'authors': authors}
    return render(request, 'polls/author_list.html', context)


def update_author(request, id):
    author = Authors.objects.get(id=id)
    if request.method == 'POST':
        form = AuthorForm(request.POST, instance=author)
        if form.is_valid():
            form.save()
            return redirect('author_list')
    else:
        form = AuthorForm(instance=author)
    context = {'form': form}
    return render(request, 'polls/author_form.html', context)


def delete_author(request, id):
    author = Authors.objects.get(id=id)
    if request.method == 'POST':
        author.delete()
        return redirect('author_list')
    context = {'author': author}
    return render(request, 'polls/author_confirm_delete.html', context)



def affiliation_list(request):
    affiliations = Affiliations.objects.all()
    context = {'affiliations': affiliations}
    return render(request, 'polls/affiliation_list.html', context)


def update_affiliation(request, id):
    affiliation = Affiliations.objects.get(id=id)
    if request.method == 'POST':
        form = AffiliationForm(request.POST, instance=affiliation)
        if form.is_valid():
            form.save()
            return redirect('affiliation_list')
    else:
        form = AffiliationForm(instance=affiliation)
    context = {'form': form}
    return render(request, 'polls/affiliation_form.html', context)


def delete_affiliation(request, id):
    affiliation = Affiliations.objects.get(id=id)
    if request.method == 'POST':
        affiliation.delete()
        return redirect('affiliation_list')
    context = {'affiliation': affiliation}
    return render(request, 'polls/affiliation_confirm_delete.html', context)

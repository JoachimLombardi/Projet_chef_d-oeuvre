# python manage.py runserver   

import json
import os
from pathlib import Path
import re
from django.http import HttpResponse
import requests
from bs4 import BeautifulSoup
import time
from dateutil import parser

from .models import Authors, Affiliations, Article, Authorship, Cited_by
from django.utils import timezone
import pytz
from django.shortcuts import render, redirect
from .forms import ArticleForm, AuthorAffiliationFormSet
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.http import JsonResponse
from django.core.serializers.json import DjangoJSONEncoder
from polls.documents import ArticleDocument
from sentence_transformers import SentenceTransformer

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


def extract_article_info(request, base_url='https://pubmed.ncbi.nlm.nih.gov'):
    links = extract_pubmed_url(base_url)
    # authors = []
    # affiliations = []
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
        url = get_absolute_url(pmid)
        if not Article.objects.filter(doi=doi).exists():
            article = Article.objects.create(title=title, abstract=abstract, date=date, url=url, pmid=pmid, doi=doi, mesh_terms=mesh_terms, disclosure=disclosure, title_review=title_review)
            get_authors_affiliations(soup, article)
            # Extract number of citations
            extract_cited_by(soup, article)
    return HttpResponse("Article, authors, affiliations and cited_by scraped with success.")


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
    return render(request, 'polls/create_update_article.html', {'article_form': article_form, 'formset': formset})


def article_list(request):
    articles = Article.objects.prefetch_related('authorships__author', 'authorships__affiliation')
    # Regrouper les affiliations par auteur
    for article in articles:
        affiliations_by_author = {}
        for authorship in article.authorships.all():
            author_name = authorship.author.name
            affiliation_name = authorship.affiliation.name    
            # Utiliser un set pour éviter les doublons
            if author_name not in affiliations_by_author:
                affiliations_by_author[author_name] = set()
            affiliations_by_author[author_name].add(affiliation_name)
        # Attacher les affiliations regroupées à chaque article
        article.affiliations_by_author = {author: list(affs) for author, affs in affiliations_by_author.items()}
    context = {
        'articles': articles,
    }
    return render(request, 'polls/article_list.html', context)


def update_article(request, id):
    article = Article.objects.get(id=id)
    authorships = article.authorships.prefetch_related('author', 'affiliation')
    # Regrouper les affiliations par auteur
    affiliations_by_author = {}
    for authorship in authorships:
        author_name = authorship.author.name
        affiliation_name = authorship.affiliation.name
        # Utiliser un set pour éviter les doublons
        if author_name not in affiliations_by_author:
            affiliations_by_author[author_name] = set()
        affiliations_by_author[author_name].add(affiliation_name)
    # Préparer les données initiales pour le formset
    initial_data = []
    for author, affiliations in affiliations_by_author.items():
        initial_data.append({
            'author_name': author,
            'affiliations': '| '.join(affiliations)  # Joindre les affiliations en une seule chaîne
        })
    if request.method == 'POST':
        article_form = ArticleForm(request.POST, instance=article)
        formset = AuthorAffiliationFormSet(request.POST, initial=initial_data)
        if article_form.is_valid() and formset.is_valid():
            # Itérer à travers le formset pour mettre à jour les auteurs et affiliations
            author_affiliation_data = [
                {
                    'author_name': form.cleaned_data.get('author_name'),
                    'affiliations': form.cleaned_data.get('affiliations')
                }
                for form in formset
            ]        
            article_form.save_article_with_authors(author_affiliation_data)
            return redirect('article_list')
    else:
        article_form = ArticleForm(instance=article)
        formset = AuthorAffiliationFormSet(initial=initial_data)
    context = {
        'article_form': article_form,
        'formset': formset,
    }
    return render(request, 'polls/create_update_article.html', context)


def delete_article(request, id):
    article = Article.objects.get(id=id)
    if request.method == 'POST':
        article.delete()
        return redirect('article_list')
    context = {'article': article}
    return render(request, 'polls/article_confirm_delete.html', context)


# Signal qui s'active après la suppression d'un article
@receiver(post_delete, sender=Article)
def delete_orphan_authors(sender, instance, **kwargs):
    authors = instance.authors.all()
    for author in authors:
        if not author.articles.exists():
            author.delete()


@receiver(post_delete, sender=Authors)
def delete_orphan_affiliations(sender, instance, **kwargs):
    affiliations = instance.affiliations.all()
    for affiliation in affiliations:
        if not affiliation.authors.exists():
            affiliation.delete()


def search_articles(request):
    # Get the search query, or use a default value
    query = request.GET.get("q", "Environmental factors related to multiple sclerosis progression")
    # Encode the search query into a vector
    query_vector = model.encode(query).tolist() 
    # Perform the KNN search using elastiknn
    search_results = ArticleDocument.search().query(
        'elastiknn',
        field='title_abstract_vector',
        query_vector=query_vector,
        model='cosine',  # Specify distance model
        k=5  # Number of neighbors to return
    )
    # Execute the search
    response = search_results.execute()
    # Prepare results for JSON response
    results = []
    article_ids = [hit.meta.id for hit in response.hits]  # Gather all article IDs for a single query
    articles = Article.objects.filter(id__in=article_ids).prefetch_related('authorships__author', 'authorships__affiliation')
    # Process the search hits and build the results list
    for hit in response.hits:
        article_id = hit.meta.id
        score = hit.meta.score
        # Get the article from the pre-fetched queryset
        article = next((art for art in articles if art.id == article_id), None)
        if article:
            # Retrieve authors and their affiliations
            affiliations_by_author = {}
            for authorship in article.authorships.all():
                author_name = authorship.author.name
                affiliation_name = authorship.affiliation.name
                # Avoid duplicates by using a set
                if author_name not in affiliations_by_author:
                    affiliations_by_author[author_name] = set()
                affiliations_by_author[author_name].add(affiliation_name)
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
                'title': article.title,
                'abstract': article.abstract,
                'authors_affiliations': authors_affiliations,
            })

    return JsonResponse(results, safe=False)  # Return results as JSON









def export_articles_json(request):
    # Chemin du dossier d'export (il peut être configuré dans settings.py)
    export_dir = os.path.join(Path(__file__).resolve().parent.parent, 'exports')
    if not os.path.exists(export_dir):
        os.makedirs(export_dir)

    # Récupérer les articles
    articles = Article.objects.prefetch_related('authorships__author', 'authorships__affiliation').all()

    # Préparer la structure JSON
    data = []
    for article in articles:
        article_data = {
            'title': article.title,
            'date': article.date,
            'title_review': article.title_review,
            'abstract': article.abstract,
            'pmid': article.pmid,
            'doi': article.doi,
            'disclosure': article.disclosure,
            'mesh_terms': article.mesh_terms,
            'url': article.url,
            'authors': []
        }
        for authorship in article.authorships.all():
            author_data = {
                'author_name': authorship.author.name,
                'affiliation': authorship.affiliation.name
            }
            article_data['authors'].append(author_data)
        data.append(article_data)

    # Créer le fichier JSON dans le dossier 'exports'
    json_file_path = os.path.join(export_dir, 'articles_export.json')
    with open(json_file_path, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4, cls=DjangoJSONEncoder)

    # Retourner les données JSON dans la réponse (optionnel)
    return JsonResponse(data, safe=False)


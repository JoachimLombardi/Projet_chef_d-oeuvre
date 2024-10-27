# python manage.py runserver   
# docker-compose up --build
# http://localhost:9200/articles/_search?pretty
# http://localhost:9200/articles/_mapping?pretty
# http://localhost:9200/_cat/indices?v
# Remove indices: curl -X DELETE "http://localhost:9200/articles" in bash


import json
from pathlib import Path
import re
from django.http import HttpResponse
from .models import Authors, Affiliations, Article, Authorship
from django.shortcuts import render, redirect
from .forms import ArticleForm, AuthorAffiliationFormSet
from django.http import JsonResponse
from django.conf import settings
from .utils import format_date, get_absolute_url
from .business_logic import init_soup, extract_pubmed_url, search_articles
import ollama


def scrap_article_to_json(request, base_url='https://pubmed.ncbi.nlm.nih.gov', test=False):
    articles_data = []
    term = "multiple_sclerosis"
    filter = "2024"
    if not test:
        links = extract_pubmed_url(base_url, term, filter)
    else: 
        links = base_url
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
        if abstract:
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
            authors_tags = soup.select('.authors-list-item')
            authors_affiliations = []
            seen_authors = set() 
            for author_tag in authors_tags:
                # Extraire le nom de l'auteur
                author_name = author_tag.select_one('.full-name').get_text(strip=True) if author_tag.select_one('.full-name') else None
                if author_name and author_name not in seen_authors:
                    seen_authors.add(author_name)
                    # Extraire les affiliations
                    affiliation_elements = author_tag.select('.affiliation-link')
                    if affiliation_elements:
                        affiliations_names = [affil.get('title', None) for affil in affiliation_elements]
                        authors_affiliations.append({'author_name': author_name, 'affiliations': affiliations_names})
            # Add article data to list
            articles_data.append({
            'title_review': title_review,
            'date': str(date),  # Convert date to string for JSON serialization
            'title': title,
            'abstract': abstract,
            'pmid': pmid,
            'doi': doi,
            'disclosure': disclosure,
            'mesh_terms': mesh_terms,
            'url': url,
            'authors_affiliations': authors_affiliations
        })
            # Save articles data to a JSON file
            if not test:
                output_path = Path(settings.EXPORT_JSON_DIR + "/" + term + "_" + filter + ".json")
            else:
                output_path = Path(settings.EXPORT_JSON_DIR + "/" + term + "_" + filter + "_test.json")
            with output_path.open('w', encoding='utf-8') as f:
                json.dump(articles_data, f, ensure_ascii=False, indent=4)
    return HttpResponse("Article, authors and affiliations scraped with success.")


def article_json_to_database(request): 
    term = "multiple_sclerosis"
    filter = "2024"
    output_path = Path(settings.EXPORT_JSON_DIR + "/" + term + "_" + filter + ".json")
    with output_path.open('r', encoding='utf-8') as f:
        articles = json.load(f)
        for article in articles:
            title = article['title']
            abstract = article['abstract']
            date = article['date']
            if date == "None":
                date = None
            url = article['url']
            pmid = article['pmid']
            doi = article['doi']
            mesh_terms = article['mesh_terms']
            disclosure = article['disclosure']
            title_review = article['title_review']
            authors_affiliations = article['authors_affiliations']
            if not Article.objects.filter(doi=doi).exists():
                article = Article.objects.create(title=title, abstract=abstract, date=date, url=url, pmid=pmid, doi=doi, mesh_terms=mesh_terms, disclosure=disclosure, title_review=title_review, term=term + "_" + filter)
                for author_affiliation in authors_affiliations:
                    author_name = author_affiliation['author_name']
                    affiliations = author_affiliation['affiliations']
                    author, created = Authors.objects.get_or_create(name=author_name)
                    for affiliation in affiliations:
                        affiliation, created = Affiliations.objects.get_or_create(name=affiliation)
                        if not Authorship.objects.filter(article=article, author=author, affiliation=affiliation).exists():
                            Authorship.objects.create(article=article, author=author, affiliation=affiliation)
    return HttpResponse("Article, authors and affiliations added to database with success.")


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


def rag_articles(request):
    if request.method == 'POST':
        query = request.POST.get('query')
        if query:
            retrieved_documents, query = search_articles(query)
            context = ""
            for i, source in enumerate(retrieved_documents):
                context += f"Abstract n°{i+1}: " + source['title'] + "." + "\n\n" + source['abstract'] + "\n\n"
            print(context)
            model = "mistral"
            template = """You are an expert in analysing medical abstract and your are talking to a pannel of medical experts. Your task is to use only provided context to answer at best the query.
            If you don't know or if the answer is not in the provided context just say: "I can't answer with the provide context".

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
            messages = [{"role":"user", "content":template}]
            chat_response = ollama.chat(
            model=model,
            messages=messages)
            pattern = r'\{+.*\}'
            match = re.findall(pattern, chat_response['message']['content'], re.DOTALL)[0]
            response = json.loads(match)['response']
            try:
                return render(request, 'polls/rag.html', {'response': response, 'context': context})
            except:
                return context
    return render(request, 'polls/rag.html')












# python manage.py runserver   
# docker-compose up --build
# http://localhost:9200/articles/_search?pretty
# http://localhost:9200/articles/_mapping?pretty
# http://localhost:9200/_cat/indices?v
# Remove indices: curl -X DELETE "http://localhost:9200/articles" in bash


import json
import re
from .models import Article
from django.shortcuts import render, redirect
from .forms import ArticleForm, AuthorAffiliationFormSet, CustomUserCreationForm
from .business_logic import search_articles
import ollama
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages



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


@login_required
def rag_articles(request):
    if request.method == 'POST':
        query = request.POST.get('query')
        if query:
            retrieved_documents, query = search_articles(query)
            context = ""
            for i, source in enumerate(retrieved_documents):
                context += f"Abstract n°{i+1}: " + source['title'] + "." + "\n\n" + source['abstract'] + "\n\n"
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
            response = ""
            if match:
                response = json.loads(match)['response']
            try:
                return render(request, 'polls/rag.html', {'response': response, 'context': context})
            except:
                return context
    return render(request, 'polls/rag.html')


# User Registration View
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)  # Log in the user after registration
            return redirect('rag_articles')
    else:
        form = CustomUserCreationForm()
    return render(request, 'polls/register.html', {'form': form})


def custom_login(request):
    if request.user.is_authenticated:
        return redirect('rag_articles') 
    form = AuthenticationForm(request, data=request.POST)
    if request.method == 'POST':
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                auth_login(request, user)
                return redirect('rag_articles')
     # Check if the user is coming from the logout and set a message
    return render(request, 'polls/login.html', {'form': form})


def custom_logout(request):
    auth_logout(request)
    messages.info(request, "Vous avez bien été déconnecté")
    return redirect('login')











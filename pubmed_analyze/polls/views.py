# python manage.py runserver   
# docker-compose up --build
# http://localhost:9200/articles/_search?pretty
# http://localhost:9200/articles/_mapping?pretty
# http://localhost:9200/_cat/indices?v
# Remove indices: curl -X DELETE "http://localhost:9200/articles" in bash


import json
import re
from .models import Article
from django.shortcuts import render, redirect, get_object_or_404
from .forms import ArticleForm, AuthorAffiliationFormSet, CustomUserCreationForm, RAGForm
from .business_logic import search_articles
import ollama
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages


def create_article(request):
    message = ''
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
            created, updated = article_form.save_article_with_authors(author_affiliation_data)
            if created:
                messages.success(request, "L'article a bien été sauvegardé dans la base de données.")
                return redirect('article_list') 
            else:
                message = "Un article avec les mêmes détails existe déjà dans la base de données."
        else:
            message = "Le formulaire n'est pas valide."
    else:
        article_form = ArticleForm()
        formset = AuthorAffiliationFormSet()
    return render(request, 'polls/create_update_article.html', {'article_form': article_form, 'formset': formset, 'message': message})


@login_required
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
    message = ''
    article = get_object_or_404(Article, id=id)
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
            created, updated = article_form.save_article_with_authors(author_affiliation_data, id)
            if updated:
                messages.success(request, "L'article a bien été mis à jour.")
                return redirect('article_list')
            else:    
                message = "L'article n'a pas été modifié dans la base de données."
        else:
            message = "Le formulaire n'est pas valide."
            
    article_form = ArticleForm(instance=article)
    formset = AuthorAffiliationFormSet(initial=initial_data)
    return render(request, 'polls/create_update_article.html', {'article_form': article_form, 'formset': formset, 'message': message})


def delete_article(request, id):
    message = ''
    article = get_object_or_404(Article, id=id)
    if request.method == 'POST':
        article.delete()
        # Check if the article is deleted
        if not Article.objects.filter(id=id).exists():
            messages.success(request, "L'article a bien été supprimé de la base de données.")
            return redirect('article_list')
        else:
            message = "L'article n'a pas été supprimé de la base de données."
    return render(request, 'polls/article_confirm_delete.html', {'article': article, 'message': message})


@login_required
def rag_articles(request):
    message = ''
    if request.method == 'POST':
        form = RAGForm(request.POST)
        if form.is_valid():
            query = form.cleaned_data.get('query')
            index = form.cleaned_data.get('index_choice')
            retrieved_documents, query = search_articles(query, index)
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
            try:
                match = re.findall(pattern, chat_response['message']['content'], re.DOTALL)[0]
            except:
                match = ""
            response = ""
            if match:
                response = json.loads(match)['response']
            return render(request, 'polls/rag.html', {'form': form, 'response': response, 'context': context})
        else:
            message = "Le formulaire n'est pas valide."
    else:
        form = RAGForm()
    return render(request, 'polls/rag.html', {'form': form, 'message': message})


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)  # Log in the user after registration
            return redirect('rag_articles')
        else:
            messages.error("Le formulaire n'est pas valide")
    else:
        form = CustomUserCreationForm()
    return render(request, 'polls/register.html', {'form': form})


def custom_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        print(form.error_messages)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                auth_login(request, user)
                next_url = request.POST.get('next')
                if next_url:
                    return redirect(next_url)
                else:
                    return redirect('rag_articles')
            else:
                messages.error(request, "Nom d'utilisateur ou mot de passe incorrect")
        else:
            messages.error(request, "Le formulaire n'est pas valide")
    else:
        form = AuthenticationForm()
    return render(request, 'polls/login.html', {'form': form})


def custom_logout(request):
    auth_logout(request)
    messages.info(request, "Vous avez bien été déconnecté")
    return redirect('login')











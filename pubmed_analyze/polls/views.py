# python manage.py runserver   
# docker-compose up --build
# http://localhost:9200/articles/_search?pretty
# http://localhost:9200/articles/_mapping?pretty
# http://localhost:9200/_cat/indices?v
# Remove indices: curl -X DELETE "http://localhost:9200/articles" in bash


import json
from pathlib import Path
import re
import time
from django.conf import settings
from django.http import HttpResponse
import requests

from polls.monitoring.monitor_rag import handle_rag_pipeline
from .models import Article
from django.shortcuts import render, redirect, get_object_or_404
from .forms import ArticleForm, AuthorAffiliationFormSet, CustomUserCreationForm, RAGForm, EvaluationForm
from .business_logic import generation, search_articles
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from polls.rag_evaluation.file_eval_json import queries, expected_abstracts
from polls.rag_evaluation.evaluation_rag_model import create_eval_rag_json, rag_articles_for_eval, eval_retrieval, eval_response
from polls.utils import convert_seconds, error_handling
import prometheus_client


@error_handling
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


@error_handling
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


@error_handling
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


@error_handling
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
@error_handling
def rag_articles(request):
    message = ''
    if request.method == 'POST':
        form = RAGForm(request.POST)
        if form.is_valid():
            query = form.cleaned_data.get('query')
            index = form.cleaned_data.get('index_choice')
            response, context = generation(query, index)
            return render(request, 'polls/rag.html', {'form': form, 'response': response, 'context': context})
        else:
            message = "Le formulaire n'est pas valide."
    else:
        form = RAGForm()
    return render(request, 'polls/rag.html', {'form': form, 'message': message})


@error_handling
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


@error_handling
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
                    return redirect('article_list')
            else:
                messages.error(request, "Nom d'utilisateur ou mot de passe incorrect")
        else:
            messages.error(request, "Le formulaire n'est pas valide")
    else:
        form = AuthenticationForm()
    return render(request, 'polls/login.html', {'form': form})


@error_handling
def custom_logout(request):
    auth_logout(request)
    messages.info(request, "Vous avez bien été déconnecté")
    return redirect('login')


@error_handling
def forbidden(request):
    return render(request, 'polls/forbidden.html')


@login_required
@user_passes_test(lambda user: user.is_staff, login_url='/forbidden/')
@error_handling
def evaluate_rag(request, queries=queries, expected_abstracts=expected_abstracts):
    if request.method == 'POST':
        # Calculate time execution
        start_time = time.time()
        form = EvaluationForm(request.POST)
        if form.is_valid():
            research_type = form.cleaned_data['research_type']
            number_of_results = form.cleaned_data['number_of_results']
            model_generation = form.cleaned_data['model_generation']
            model_evaluation = form.cleaned_data['model_evaluation']
            number_of_articles = form.cleaned_data['number_of_articles']
            title_weight = form.cleaned_data['title_weight']
            abstract_weight = form.cleaned_data['abstract_weight']
            rank_scaling_factor = form.cleaned_data['rank_scaling_factors']
            # Définir les chemins de fichiers
            eval_path = Path(settings.RAG_JSON_DIR) / "eval_rag.json"
            # Créer le fichier JSON d'évaluation si nécessaire
            if not eval_path.exists():
                for query, expected_abstract in zip(queries, expected_abstracts):
                    create_eval_rag_json(query, expected_abstract)
            # Charger les données d'évaluation
            with eval_path.open('r', encoding='utf-8') as f:
                evaluation_data = json.load(f)
            # Initialiser les scores
            score_retrieval = 0
            score_generation_list = []
            eval_rag_list = []
            # Calculer les scores pour chaque requête
            for data in evaluation_data:
                query = data['query']
                expected_abstract = data['expected_abstract']
                response, retrieved_documents, context = rag_articles_for_eval(query,
                                                                               research_type,
                                                                               number_of_results,
                                                                               model_generation,
                                                                               number_of_articles,
                                                                               title_weight,
                                                                               abstract_weight,
                                                                               rank_scaling_factor)
                found_abstract = retrieved_documents[0]["abstract"]
                number = eval_retrieval(query, found_abstract, expected_abstract, model_evaluation) 
                # Évaluation de la récupération
                if number == 1:
                    score_retrieval += 0.1
                    # Évaluation de la génération
                    score_generation, scoring_generation_reason = eval_response(query, response, context, model_evaluation)
                    score_generation = (score_generation - 1)/4
                    score_generation_list.append(score_generation)
                    # Stocker les résultats
                    eval_rag_list.append({
                        "query": query,
                        "expected_abstract": expected_abstract,
                        "found_abstract": found_abstract,
                        "response": response
                    })
            # Calcul des scores finaux
            score_generation = round(sum(score_generation_list) / len(score_generation_list), 2)
            end_time = time.time()
            if research_type == "hybrid":
                eval_rag_list.append({
                    "execution_time": convert_seconds(round(end_time - start_time, 2)),  
                    "research_type": research_type,
                    "number_of_results": number_of_results,
                    "model_generation": model_generation,
                    "model_evaluation": model_evaluation,
                    "number_of_articles": number_of_articles,
                    "title_weight": title_weight,
                    "abstract_weight": abstract_weight,
                    "rank_scaling_factor": rank_scaling_factor,
                    "score_retrieval": round(score_retrieval, 2),
                    "score_generation": round(score_generation, 2),
                    "scoring_generation_reason": scoring_generation_reason
                })
            elif research_type == "text":
                eval_rag_list.append({
                    "execution_time": convert_seconds(round(end_time - start_time, 2)),  
                    "research_type": research_type,
                    "number_of_results": number_of_results,
                    "model_generation": model_generation,
                    "model_evaluation": model_evaluation,
                    "title_weight": title_weight,
                    "abstract_weight": abstract_weight,
                    "score_retrieval": round(score_retrieval, 2),   
                    "score_generation": round(score_generation, 2), 
                    "scoring_generation_reason": scoring_generation_reason
                })
            else:
                eval_rag_list.append({
                    "execution_time": convert_seconds(round(end_time - start_time, 2)),  
                    "research_type": research_type,
                    "number_of_results": number_of_results,
                    "model_generation": model_generation,
                    "model_evaluation": model_evaluation,
                    "number_of_articles": number_of_articles,
                    "score_retrieval": round(score_retrieval, 2),
                    "score_generation": round(score_generation, 2),
                    "scoring_generation_reason": scoring_generation_reason
                })
            # Enregistrer les résultats
            results_path = Path(settings.RAG_JSON_DIR) / f"results_eval_rag_{research_type}_{number_of_results}_{model_generation}_{model_evaluation}_{number_of_articles}_{title_weight}_{abstract_weight}_{rank_scaling_factor}.json"
            with results_path.open('w', encoding='utf-8') as f:
                json.dump(eval_rag_list, f, ensure_ascii=False, indent=4)
            return render(request, 'polls/evaluate_rag.html', {'form': form, 'score_generation': score_generation, 'score_retrieval': round(score_retrieval, 2)})
        else:
            messages.error(request, "Le formulaire n'est pas valide")
    else:
        form = EvaluationForm()
    return render(request, 'polls/evaluate_rag.html', {'form': form})


@login_required
@user_passes_test(lambda user: user.is_staff, login_url='/forbidden/')
@error_handling
def grafana(request):
    return redirect('http://127.0.0.1:3000')


@login_required
@user_passes_test(lambda user: user.is_staff, login_url='/forbidden/')
@error_handling
def uptime_kuma(request):
    return redirect('http://127.0.0.1:3001')









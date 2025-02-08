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
from django.core.paginator import Paginator
from deepeval.metrics import FaithfulnessMetric, ContextualRelevancyMetric
from deepeval.test_case import LLMTestCase
import os

openai_key = os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_API_KEY"] = openai_key

@error_handling
def create_or_update_article(request, pk=None):
    article = None
    initial_data = []
    if pk:
        article = get_object_or_404(Article, id=pk)
        authorships = article.authorships.prefetch_related('author', 'affiliation')
        affiliations_by_author = {}
        for authorship in authorships:
            author_name = authorship.author.name
            affiliation_name = authorship.affiliation.name
            affiliations_by_author.setdefault(author_name, set()).add(affiliation_name)
        initial_data = [
            {
                'author_name': author,
                'affiliations': ' | '.join(affiliations)
            }
            for author, affiliations in affiliations_by_author.items()
        ]
    article_form = ArticleForm(request.POST or None, instance=article)
    formset = AuthorAffiliationFormSet(request.POST or None, initial=initial_data)
    if request.method == 'POST':
        if article_form.is_valid() and formset.is_valid():
            author_affiliation_data = [
                {
                    'author_name': form.cleaned_data.get('author_name'),
                    'affiliations': form.cleaned_data.get('affiliations')
                }
                for form in formset
            ]
            created, updated = article_form.save_article_with_authors(author_affiliation_data, id)
            if created:
                messages.success(request, "L'article a bien été créé dans la base de données.")
                return redirect('article_list')
            elif updated:
                messages.success(request, "L'article a bien été mis à jour.")
                return redirect('article_list')
            else:
                messages.error(request, "Un article avec les mêmes détails existe déjà dans la base de données.")
        else:
            messages.error(request, "Le formulaire n'est pas valide.") 
    return render(request, 'polls/create_update_article.html', {'article_form': article_form,'formset': formset})


@error_handling
@login_required
def article_list(request):
    articles = Article.objects.prefetch_related('authorships__author', 'authorships__affiliation').order_by('id')
    for article in articles:
        affiliations_by_author = {}
        for authorship in article.authorships.all():
            author_name = authorship.author.name
            affiliation_name = authorship.affiliation.name    
            affiliations_by_author.setdefault(author_name, set()).add(affiliation_name)
        article.affiliations_by_author = {author: list(affs) for author, affs in affiliations_by_author.items()}
    paginator = Paginator(articles, 3)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    return render(request, 'polls/article_list.html', {'page_obj': page_obj})


@error_handling
def delete_article(request, id):
    article = get_object_or_404(Article, id=id)
    if request.method == 'POST':
        article.delete()
        if not Article.objects.filter(id=id).exists():
            messages.success(request, "L'article a bien été supprimé de la base de données.")
            return redirect('article_list')
        else:
            messages.error(request, "L'article n'a pas été supprimé de la base de données.")
    return render(request, 'polls/article_confirm_delete.html', {'article': article})


@login_required
@error_handling
def rag_articles(request):
    form = RAGForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            query = form.cleaned_data.get('query')
            index = form.cleaned_data.get('index_choice')
            llm = form.cleaned_data.get('llm_choice')
            response, context = handle_rag_pipeline(query, llm, index)
            if "error" in response:
                messages.error(request, response)
                response = ""
                context = ""
            return render(request, 'polls/rag.html', {'form': form, 'response': response, 'context': context})
        else:
            messages.error(request, "Le formulaire n'est pas valide.")
    return render(request, 'polls/rag.html', {'form': form})


@error_handling
def register(request):
    form = CustomUserCreationForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            user = form.save()
            auth_login(request, user)  
            return redirect('rag_articles')
        else:
            messages.error("Le formulaire n'est pas valide")
    return render(request, 'polls/register.html', {'form': form})


@error_handling
def custom_login(request):
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == 'POST':
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
        # Initialiser les scores
        score_retrieval_list = []
        score_generation_list = []
        eval_rag_list = []
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
            choose_eval_method = form.cleaned_data['choose_eval_method']
            # Définir les chemins de fichiers
            eval_path = Path(settings.RAG_JSON_DIR) / "eval_rag.json"
            # Créer le fichier JSON d'évaluation si nécessaire
            if not eval_path.exists():
                for query, expected_abstract in zip(queries, expected_abstracts):
                    create_eval_rag_json(query, expected_abstract)
            # Charger les données d'évaluation
            with eval_path.open('r', encoding='utf-8') as f:
                evaluation_data = json.load(f)
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
                print(context, flush=True)
                print(type(context), flush=True)
                if choose_eval_method == "deep_eval":
                    metric = FaithfulnessMetric(
                        threshold=0.7,
                        model=model_evaluation,
                        include_reason=True
                    )
                    test_case = LLMTestCase(
                        input=query,
                        actual_output=response,
                        retrieval_context=list(context)
                    )
                    metric.measure(test_case)
                    score_generation = metric.score
                    score_generation_list.append(score_generation)
                    scoring_generation_reason = metric.reason
                    metric = ContextualRelevancyMetric(
                    threshold=0.7,
                    model=model_evaluation,
                    include_reason=True
                    )
                    test_case = LLMTestCase(
                        input=query,
                        actual_output=response,
                        retrieval_context=list(context)
                    )
                    metric.measure(test_case)
                    score_retrieval = metric.score
                    score_retrieval_list.append(score_retrieval)
                    scoring_retrieval_reason = metric.reason
                else:
                    number, scoring_retrieval_reason = eval_retrieval(query, found_abstract, expected_abstract, model_evaluation) 
                    # Évaluation de la récupération
                    score_retrieval_list.append(number)
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
                score_retrieval = round(sum(score_retrieval_list) / len(score_retrieval_list), 2)
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
                    "scoring_retrieval_reason": scoring_retrieval_reason,
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
                    "scoring_generation_reason": scoring_generation_reason,
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
                    "scoring_retrieval_reason": scoring_retrieval_reason,
                    "scoring_generation_reason": scoring_generation_reason
                })
            # Enregistrer les résultats
            results_path = Path(settings.RAG_JSON_DIR) / f"results_eval_rag_{model_generation}_{choose_eval_method}_{research_type}_{number_of_results}_{model_evaluation}_{number_of_articles}_{title_weight}_{abstract_weight}_{rank_scaling_factor}.json"
            with results_path.open('w', encoding='utf-8') as f:
                json.dump(eval_rag_list, f, ensure_ascii=False, indent=4)
            return render(request, 'polls/evaluate_rag.html', {'form': form, 'score_generation': score_generation, 'score_retrieval': score_retrieval})
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









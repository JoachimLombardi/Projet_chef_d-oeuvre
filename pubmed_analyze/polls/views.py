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
from .models import Article
from django.shortcuts import render, redirect, get_object_or_404
from .forms import ArticleForm, AuthorAffiliationFormSet, CustomUserCreationForm, RAGForm, EvaluationForm
from .business_logic import search_articles
import ollama
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from polls.rag_evaluation.file_eval_json import queries, expected_abstracts
from polls.rag_evaluation.evaluation_rag_model import create_eval_rag_json, rag_articles_for_eval, eval_retrieval, eval_response
from polls.utils import convert_seconds


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
            chat_response = ollama.chat(model=model,
                                        messages=messages,
                                        options={"temperature": 0})
            pattern = r'\{+.*\}'
            try:
                match = re.findall(pattern, chat_response['message']['content'], re.DOTALL)[0]
                match = match.replace("\n", "")
            except:
                match = ""
            if match:
                try:
                    response = json.loads(match)['response']
                except json.JSONDecodeError as e:
                    print("Erreur JSON:", e)
                    print("Contenu de match:", repr(match))
                    response = ""
                    message = "Suite à un problème de codage JSON, le résultat de la conversation n'est pas valide."
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
                    return redirect('list_articles')
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

def forbidden(request):
    return render(request, 'polls/forbidden.html')


@login_required
@user_passes_test(lambda user: user.is_staff, login_url='/forbidden/')
def evaluate_rag(request, queries=queries, expected_abstracts=expected_abstracts):
    if request.method == 'POST':
        # Calculate time execution
        start_time = time.time()
        form = EvaluationForm(request.POST)
        if form.is_valid():
            research_type = form.cleaned_data['research_type']
            number_of_results = form.cleaned_data['number_of_results']
            model = form.cleaned_data['model']
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
            query_find_braces_rag_list = []
            query_load_json_rag_list = []
            error_find_braces_rag_list = []
            error_load_json_rag_list = []
            query_find_braces_retrieval_list = []
            query_load_json_retrieval_list = []
            error_find_braces_retrieval_list = []
            error_load_json_retrieval_list = []
            query_find_braces_generation_list = []
            query_load_json_generation_list = []
            error_find_braces_generation_list = []
            error_load_json_generation_list = []
            query_error_score_generation_list = []
            error_score_generation_list = []
            score_generation_list = []
            eval_rag_list = []
            # Calculer les scores pour chaque requête
            for data in evaluation_data:
                query = data['query']
                expected_abstract = data['expected_abstract']
                response, retrieved_documents, context, error_find_braces_rag, error_load_json_rag = rag_articles_for_eval(query,
                                                                                                                    research_type,
                                                                                                                    number_of_results,
                                                                                                                    model,
                                                                                                                    number_of_articles,
                                                                                                                    title_weight,
                                                                                                                    abstract_weight,
                                                                                                                    rank_scaling_factor)
                if error_find_braces_rag:
                    query_find_braces_rag_list.append(query)
                    error_find_braces_rag_list.append(error_find_braces_rag)
                elif error_load_json_rag:
                    query_load_json_rag_list.append(query)
                    error_load_json_rag_list.append(error_load_json_rag)
                else:
                    found_abstract = retrieved_documents[0]["abstract"]
                    number, error_find_braces_retrieval, error_load_json_retrieval = eval_retrieval(query, found_abstract, expected_abstract) 
                    if error_find_braces_retrieval:
                        query_find_braces_retrieval_list.append(query)
                        error_find_braces_retrieval_list.append(error_find_braces_retrieval)
                    elif error_load_json_retrieval:
                        query_load_json_retrieval_list.append(query)    
                        error_load_json_retrieval_list.append(error_load_json_retrieval)
                    else:
                        # Évaluation de la récupération
                        if number == 1:
                            score_retrieval += 0.1
                    # Évaluation de la génération
                    score_generation, scoring_generation_reason, error_find_braces_generation, error_load_json_generation, error_score_generation = eval_response(query, response, context)
                    if error_find_braces_generation:
                        query_find_braces_generation_list.append(query)
                        error_find_braces_generation_list.append(error_find_braces_generation)
                    elif error_load_json_generation:
                        query_load_json_generation_list.append(query)
                        error_load_json_generation_list.append(error_load_json_generation)
                    elif error_score_generation:
                        query_error_score_generation_list.append(query)
                        error_score_generation_list.append(error_score_generation)
                    else:
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
                    "model": model,
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
                    "model": model,
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
                    "model": model,
                    "number_of_articles": number_of_articles,
                    "score_retrieval": round(score_retrieval, 2),
                    "score_generation": round(score_generation, 2),
                    "scoring_generation_reason": scoring_generation_reason
                })
            # Save log errors
            log_path = Path(settings.ERROR_JSON_DIR) / "log_errors.json"
            log_errors = {
                "query_find_braces_list": query_find_braces_rag_list,
                "error_find_braces_list": error_find_braces_rag_list,
                "query_load_json_list": query_load_json_rag_list,
                "error_load_json_list": error_load_json_rag_list,
                "query_find_braces_list": query_find_braces_retrieval_list,
                "error_find_braces_list": error_find_braces_retrieval_list,
                "query_load_json_list": query_load_json_retrieval_list,
                "error_load_json_list": error_load_json_retrieval_list,
                "query_find_braces_list": query_find_braces_generation_list,
                "error_find_braces_list": error_find_braces_generation_list,
                "query_load_json_list": query_load_json_generation_list,
                "error_load_json_list": error_load_json_generation_list,
                "query_error_score_generation_list": query_error_score_generation_list,
                "error_score_generation_list": error_score_generation_list
            }
            with log_path.open('w', encoding='utf-8') as f:
                json.dump(log_errors, f, ensure_ascii=False, indent=4)
            # Enregistrer les résultats
            results_path = Path(settings.RAG_JSON_DIR) / f"results_eval_rag_{research_type}_{number_of_results}_{model}_{number_of_articles}_{title_weight}_{abstract_weight}_{rank_scaling_factor}.json"
            with results_path.open('w', encoding='utf-8') as f:
                json.dump(eval_rag_list, f, ensure_ascii=False, indent=4)
            return render(request, 'polls/evaluate_rag.html', {'form': form, 'score_generation': score_generation, 'score_retrieval': round(score_retrieval, 2)})
        else:
            messages.error(request, "Le formulaire n'est pas valide")
    else:
        form = EvaluationForm()
    return render(request, 'polls/evaluate_rag.html', {'form': form})









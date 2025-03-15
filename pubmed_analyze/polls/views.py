# python manage.py runserver   
# docker-compose up --build
# http://localhost:9200/articles/_search?pretty
# http://localhost:9200/articles/_mapping?pretty
# http://localhost:9200/_cat/indices?v
# Remove indices: curl -X DELETE "http://localhost:9200/articles" in bash

import ast
import json
from pathlib import Path
import time
from django.conf import settings
<<<<<<< HEAD
from polls.monitoring.monitor_rag import handle_rag_pipeline
from .models import Article, ArticlesWithAuthors, RnaPrecomputed
=======
from django.http import HttpResponseForbidden
from polls.monitoring.monitor_rag import handle_rag_pipeline
from .models import Article, RnaPrecomputed
>>>>>>> 07bd1c18571c6bbfb47f8c669322eb3ec9cdab28
from django.shortcuts import render, redirect, get_object_or_404
from .forms import ArticleForm, AuthorAffiliationFormSet, CustomUserCreationForm, RAGForm, EvaluationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from polls.rag_evaluation.file_eval_json import queries, expected_abstracts
from polls.rag_evaluation.evaluation_rag_model import create_eval_rag_json, rag_articles_for_eval, eval_retrieval, eval_response
from polls.utils import convert_seconds, error_handling
from django.core.paginator import Paginator
import os
from rest_framework.decorators import api_view
<<<<<<< HEAD
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
import pdb
=======
from drf_yasg.utils import swagger_auto_schema
from rest_framework.response import Response
>>>>>>> 07bd1c18571c6bbfb47f8c669322eb3ec9cdab28


openai_key = os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_API_KEY"] = openai_key

pk_param = openapi.Parameter(
    'pk',
    in_=openapi.IN_QUERY,
    description="ID de l'article à modifier (optionnel)",
    type=openapi.TYPE_INTEGER,
    required=False
)

@swagger_auto_schema(
    method='get',
<<<<<<< HEAD
    manual_parameters=[pk_param], 
    operation_description="Affiche le formulaire de création ou mise à jour d'un article.",
    responses={
        200: 'Formulaire rendu.',
        404: 'Article non trouvé.',
=======
    operation_description="Displays the article creation or update form.",
    responses={
        200: 'Form for creating or updating an article rendered.',
        404: 'Article not found when editing.',
>>>>>>> 07bd1c18571c6bbfb47f8c669322eb3ec9cdab28
    }
)
@swagger_auto_schema(
    method='post',
<<<<<<< HEAD
    manual_parameters=[pk_param], 
    operation_description="Crée ou met à jour un article.",
    responses={
        200: 'Article créé ou mis à jour.',
        400: 'Erreur de validation du formulaire.',
=======
    operation_description="Handles both creation and update of articles.",
    responses={
        200: 'Article successfully created or updated.',
        400: 'Form validation failed or article with the same details already exists.',
>>>>>>> 07bd1c18571c6bbfb47f8c669322eb3ec9cdab28
    }
)
@api_view(['GET', 'POST'])
@error_handling
def create_or_update_article(request, pk=None):
    """
    Handles both creation and update of articles.

    Displays a form containing the following fields: title, journal, year, volume, pages, 
    keywords, and authors along with their affiliations. If the article being edited 
    already exists, the form is prepopulated with the article's existing data. 

    If the form is valid, creates or updates the article in the database and redirects to the article list page.

    If the form is invalid, redisplays the form with error messages. If an article with the same details already exists, 
    displays an error message.

    :param request: The HTTP request object.
    :param pk: The primary key of the article to be updated. If None, a new article is created.
    :return: A rendered HTML page displaying the form and any error messages.
    """
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
            created, updated = article_form.save_article_with_authors(author_affiliation_data, pk)
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


@swagger_auto_schema(
    method='get',
    operation_description="Displays a paginated list of articles with authors and their affiliations.",
    responses={
        200: 'A list of paginated articles with authors and affiliations.',
        403: 'Permission denied. User not authenticated.',
    }
)
@api_view(['GET'])
@error_handling
@login_required
def article_list(request):
    """
<<<<<<< HEAD
    Displays a paginated list of articles with authors and their affiliations.

    Paginates all articles with their authors and affiliations. Each page
    contains 3 articles. The page number can be specified in the query
    string with the parameter 'page'.

    If the user is not authenticated, this view will return a 403 status
    code. The user needs to be logged in to access this view.

    :param request: The request object
    :return: A rendered template with the paginated list of articles
    """
    articles = ArticlesWithAuthors.objects.all()
=======
    Displays a paginated list of articles along with their authors and affiliations.

    This view fetches all articles from the database, prefetching related author and 
    affiliation data to minimize database queries. It then constructs a dictionary 
    mapping authors to their respective affiliations for each article. The articles 
    are paginated, displaying a specified number per page.

    This view requires the user to be authenticated and is decorated with 
    error handling to manage exceptions gracefully.

    Args:
        request: The HTTP request object.

    Returns:
        A rendered HTML page displaying the list of articles, paginated, with 
        author and affiliation details.
    """

    articles = Article.objects.prefetch_related('authorships__author', 'authorships__affiliation').order_by('id')
    for article in articles:
        affiliations_by_author = {}
        for authorship in article.authorships.all():
            author_name = authorship.author.name
            affiliation_name = authorship.affiliation.name    
            affiliations_by_author.setdefault(author_name, set()).add(affiliation_name)
        article.affiliations_by_author = {author: list(affs) for author, affs in affiliations_by_author.items()}
>>>>>>> 07bd1c18571c6bbfb47f8c669322eb3ec9cdab28
    paginator = Paginator(articles, 3)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    return render(request, 'polls/article_list.html', {'page_obj': page_obj})


@swagger_auto_schema(
    method='get',
    operation_description="Displays a confirmation page for deleting an article by its ID.",
    responses={ 
        200: 'Confirmation page rendered successfully.',
    }
)
@swagger_auto_schema(
    method='post',
    operation_description="Deletes an article by its ID.",
    responses={ 
        200: 'Article successfully deleted.',
        404: 'Article not found.',
    }
)
@api_view(['GET', 'POST'])
@error_handling
def delete_article(request, id):
    """
    Handles the deletion of an article identified by its id.

    This view function retrieves an Article instance by id and checks if the request
    method is POST. If so, it deletes the article from the database. It then verifies
    if the deletion was successful by checking the existence of the article in the database.

    If the article is successfully deleted, a success message is displayed to the user,
    and the user is redirected to the article list. If the deletion fails, an error
    message is displayed.

    The function renders a confirmation page before deletion, allowing the user to 
    confirm or cancel the deletion operation.

    Args:
        request: The HTTP request object.
        id: The id of the article to be deleted.

    Returns:
        A rendered confirmation page if the request method is not POST, or a redirect
        to the article list if the deletion is successful.
    """

    article = get_object_or_404(Article, id=id)
    if request.method == 'POST':
        article.delete()
        if not Article.objects.filter(id=id).exists():
            messages.success(request, "L'article a bien été supprimé de la base de données.")
            return redirect('article_list')
        else:
            messages.error(request, "L'article n'a pas été supprimé de la base de données.")
    return render(request, 'polls/article_confirm_delete.html', {'article': article})


@swagger_auto_schema(
    method='get',
    operation_description="Displays the RAG (Retrieval-Augmented Generation) form to the user.",
    responses={ 
        200: 'RAG form rendered successfully.',
    }
)
@swagger_auto_schema(
    method='post',
    operation_description="Handles the RAG (Retrieval-Augmented Generation) form submission and response.",
    responses={ 
        200: 'The RAG query was successfully processed.',
        400: 'The form is invalid or an error occurred during processing.',
    }
)
@api_view(['GET', 'POST'])
@login_required
@error_handling
def rag_articles(request):
    """
    Handles the RAG (Retrieval-Augmented Generation) form submission and response.

    This view is decorated with @login_required to ensure that only authenticated
    users can access it, and @error_handling to manage exceptions that may occur
    during processing.

    The view processes a RAG form submission, where a user can input a query, 
    select an index, and choose a language model (LLM). If the form is valid, 
    it invokes the `handle_rag_pipeline` function to process the query and 
    generate a response along with context. If an error occurs during processing,
    an error message is displayed to the user.

    Renders either the form with the response and context if the form submission 
    is successful, or the form with validation error messages if the form is invalid.
    """

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


@swagger_auto_schema(
<<<<<<< HEAD
    methods=['get', 'post'],
    operation_description="Handles user registration: displays the form and processes submission.",
    responses={ 
        200: 'Registration form rendered successfully or user registered.',
=======
    method='get',
    operation_description="Displays the registration form for a new user.",
    responses={ 
        200: 'Registration form rendered successfully.',
    }
)
@swagger_auto_schema(
    method='post',
    operation_description="Registers a new user and logs them in if the form is valid.",
    responses={ 
        200: 'User successfully registered and logged in.',
>>>>>>> 07bd1c18571c6bbfb47f8c669322eb3ec9cdab28
        400: 'Form submission is invalid.',
    }
)
@api_view(['GET', 'POST'])
@error_handling
<<<<<<< HEAD
def create_or_update_register(request):
    """
    Handles user registration: displays the form and processes submission.

    - If the user already exists, the form is pre-filled.
    - If the method is GET, it displays the registration form.
    - If the method is POST:
        - If the form is valid, it creates or updates the user and logs them in.
        - If the form is invalid, it returns an error message.
    """
    user = None
    if request.user.is_authenticated:  
        user = request.user
    form = CustomUserCreationForm(request.POST or None, instance=user)  
    if request.method == 'POST':
        if form.is_valid():
            user = form.save(commit=False)
            if 'password1' in form.cleaned_data and form.cleaned_data['password1']:
                user.set_password(form.cleaned_data['password1'])
            user.save()
            auth_login(request, user)
=======
def register(request):
    """
    Registers a new user and logs them in if the form is valid.

    This view is connected to the 'register' URL pattern and is decorated with
    the @error_handling decorator to catch any exceptions that may occur during
    the registration process.

    If the form is valid, it creates a new user and logs them in using
    the auth_login function. If the user is successfully logged in, it
    redirects to the article list page.

    If the form is not valid, it displays an error message to the user.

    """
    form = CustomUserCreationForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            user = form.save()
            auth_login(request, user)  
>>>>>>> 07bd1c18571c6bbfb47f8c669322eb3ec9cdab28
            return redirect('list_articles')
        else:
            messages.error(request, "Le formulaire n'est pas valide")
    return render(request, 'polls/register.html', {'form': form})


@swagger_auto_schema(
    method='get',
    operation_description="Displays the login form to the user.",
    responses={ 
        200: 'Login form rendered successfully.',
    }
)
@swagger_auto_schema(
    method='post',
    operation_description="Logs in the user and redirects to the next page if the form is valid.",
    responses={ 
        200: 'User successfully logged in and redirected.',
        400: 'Form submission is invalid.',
        401: 'Invalid username or password.',
    }
)
@api_view(['GET', 'POST'])
@error_handling
def custom_login(request):
    """
    Logs in the user and redirects to the next page if the form is valid.

    This view is connected to the 'login' URL pattern and is decorated with
    the @error_handling decorator to catch any exceptions that may occur during
    the login process.

    If the form is valid, it authenticates the user and logs them in using
    the auth_login function. If the user is successfully logged in, it
    redirects to the next page if the 'next' field is set in the form data,
    otherwise it redirects to the article list page.

    If the form is not valid, it displays an error message to the user.

    """
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == 'POST':
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


@swagger_auto_schema(
<<<<<<< HEAD
    method='post',
=======
    method='get',
>>>>>>> 07bd1c18571c6bbfb47f8c669322eb3ec9cdab28
    operation_description="Logs out the user and redirects to the login page.",
    responses={
        200: 'User successfully logged out and redirected to login.',
    }
)
<<<<<<< HEAD
@api_view(['POST'])
=======
@api_view(['GET'])
>>>>>>> 07bd1c18571c6bbfb47f8c669322eb3ec9cdab28
@error_handling
def custom_logout(request):
    """
    Logs out the user and redirects to the login page.

    This view is connected to the 'logout' URL pattern and is decorated with
    the @error_handling decorator to catch any exceptions that may occur during
    the logout process.

    """
    auth_logout(request)
    messages.info(request, "Vous avez bien été déconnecté")
    return redirect('login')


@swagger_auto_schema(
<<<<<<< HEAD
    method='get',
    operation_description="Displays the user's profile page.",
    responses={
        200: 'User profile page rendered successfully.',
    }
)
@api_view(['GET'])
@error_handling
def user_profile(request):
    user = request.user  
    return render(request, 'polls/profile.html', {'user': user})


@swagger_auto_schema(
=======
>>>>>>> 07bd1c18571c6bbfb47f8c669322eb3ec9cdab28
    methods=['GET', 'POST'],  
    operation_description="Deletes the authenticated user's account.",
    responses={
        204: 'User account successfully deleted.',
        401: 'Unauthorized - User not authenticated.',
        200: 'Confirmation page for deletion.',
    }
)
@api_view(['GET', 'POST'])  
@login_required
@error_handling
def delete_account(request):
    """
    Allows an authenticated user to delete their own account.

    This view ensures that the user is logged in before proceeding with the deletion.
    """
<<<<<<< HEAD
    if request.method == 'POST':
=======
    if request.method == 'POST' and request.POST.get('_method') == 'DELETE':
>>>>>>> 07bd1c18571c6bbfb47f8c669322eb3ec9cdab28
        user = request.user
        user.delete()  
        auth_logout(request)  
        messages.success(request, "Votre compte a été supprimé avec succès.")
        return redirect('register')  
    return render(request, 'polls/account_confirm_delete.html')



@swagger_auto_schema(
    method='get',
    operation_description="Returns a rendered HTML page indicating that the user is not allowed to access the requested page.",
    responses={
        403: 'Forbidden - The user is not allowed to access the requested page.',
    }
)
@api_view(['GET'])
@error_handling
def forbidden(request):
    """
    Returns a rendered HTML page indicating that the user is not allowed to access the requested page.

    This view is used as the login_url for the user_passes_test decorator when the user is not staff.
    """
    return render(request, 'polls/forbidden.html')


@swagger_auto_schema(
    method='post',
    operation_description="Evaluates the performance of a RAG (Research Article Generator) model. This includes calculating retrieval and generation scores, creating an evaluation JSON file, and rendering the results.",
    responses={
        200: 'Evaluation completed successfully, returns results of the RAG evaluation.',
        400: 'Bad request, form is invalid.',
    }
)
@swagger_auto_schema(
    method='get',
    operation_description="Displays the form to evaluate a RAG model.",
    responses={
        200: 'Returns the form for RAG evaluation.',
    }
)
@api_view(['GET', 'POST'])
@login_required
@user_passes_test(lambda user: user.is_staff, login_url='/forbidden/')
@error_handling
def evaluate_rag(request, queries=queries, expected_abstracts=expected_abstracts):
    """
    Evaluate a RAG (Research Article Generator) model.

    This view creates a JSON file with the evaluation results of the RAG model
    in the `settings.RAG_JSON_DIR` directory. The JSON file contains the scores
    for retrieval and generation, as well as the execution time and the
    parameters used for the evaluation.

    The view also renders a HTML page with the scores and the parameters used
    for the evaluation.

    :param request: The request object
    :param queries: The list of queries to evaluate
    :param expected_abstracts: The list of expected abstracts for each query
    :return: A rendered HTML page with the scores and the parameters used for the evaluation
    """
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
            eval_path = Path(settings.RAG_JSON_DIR) / "eval_rag.json"
            if not eval_path.exists():
                for query, expected_abstract in zip(queries, expected_abstracts):
                    create_eval_rag_json(query, expected_abstract)
            with eval_path.open('r', encoding='utf-8') as f:
                evaluation_data = json.load(f)
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
                number, scoring_retrieval_reason = eval_retrieval(query, found_abstract, expected_abstract, model_evaluation) 
<<<<<<< HEAD
                score_retrieval_list.append(number)
                score_generation, scoring_generation_reason = eval_response(query, response, context, model_evaluation)
                score_generation = (score_generation - 1)/4
                score_generation_list.append(score_generation)
=======
                # Évaluation de la récupération
                score_retrieval_list.append(number)
                # Évaluation de la génération
                score_generation, scoring_generation_reason = eval_response(query, response, context, model_evaluation)
                score_generation = (score_generation - 1)/4
                score_generation_list.append(score_generation)
                # Stocker les résultats
>>>>>>> 07bd1c18571c6bbfb47f8c669322eb3ec9cdab28
                eval_rag_list.append({
                    "query": query,
                    "expected_abstract": expected_abstract,
                    "found_abstract": found_abstract,
                    "response": response
                })
<<<<<<< HEAD
=======
                # Calcul des scores finaux
>>>>>>> 07bd1c18571c6bbfb47f8c669322eb3ec9cdab28
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
            results_path = Path(settings.RAG_JSON_DIR) / f"results_eval_rag_{model_generation}_{choose_eval_method}_{research_type}_{number_of_results}_{model_evaluation}_{number_of_articles}_{title_weight}_{abstract_weight}_{rank_scaling_factor}.json"
            with results_path.open('w', encoding='utf-8') as f:
                json.dump(eval_rag_list, f, ensure_ascii=False, indent=4)
            return render(request, 'polls/evaluate_rag.html', {'form': form, 'score_generation': score_generation, 'score_retrieval': score_retrieval})
        else:
            messages.error(request, "Le formulaire n'est pas valide")
    else:
        form = EvaluationForm()
    return render(request, 'polls/evaluate_rag.html', {'form': form})


@swagger_auto_schema(
    method='get',
    operation_description="Redirects to the Grafana dashboard (http://127.0.0.1:3000) for staff users. If the user is not logged in or is not a staff member, they are redirected to the login or forbidden page respectively.",
    responses={
        302: 'Redirects to the Grafana dashboard.',
        403: 'Forbidden - User does not have the necessary staff privileges.',
        401: 'Unauthorized - User is not logged in.',
    }
)
@api_view(['GET'])        
@login_required
@user_passes_test(lambda user: user.is_staff, login_url='/forbidden/')
@error_handling
def grafana(request):
    """
    Redirect to Grafana (http://127.0.0.1:3000) for staff users.

    This view is protected by the @login_required and @user_passes_test decorators.
    If the user is not logged in or is not a staff user, they will be redirected to
    the login page or the forbidden page, respectively.

    :param request: The request object
    :return: A redirect response to Grafana
    """
    return redirect('http://127.0.0.1:3000')


@swagger_auto_schema(
    method='GET',
    operation_description="Redirects to the Uptime Kuma dashboard (http://127.0.0.1:3001) for staff users. If the user is not logged in or is not a staff member, they are redirected to the login or forbidden page respectively.",
    responses={
        302: 'Redirects to the Uptime Kuma dashboard.',
        403: 'Forbidden - User does not have the necessary staff privileges.',
        401: 'Unauthorized - User is not logged in.',
    }
)
@api_view(['GET'])
@login_required
@user_passes_test(lambda user: user.is_staff, login_url='/forbidden/')
@error_handling
def uptime_kuma(request):
    """
    Redirect to Uptime Kuma (http://127.0.0.1:3001) for staff users.

    This view is protected by the @login_required and @user_passes_test decorators.
    If the user is not logged in or is not a staff user, they will be redirected to
    the login page or the forbidden page, respectively.

    :param request: The request object
    :return: A redirect response to Uptime Kuma
    """
    return redirect('http://127.0.0.1:3001')


@swagger_auto_schema(
    method='get',
    operation_description="Fetches information about a gene from the Ensembl database based on specific filters.",
    responses={
        200: 'Returns a list of gene IDs related to the filter conditions.',
        500: 'Internal Server Error if something goes wrong.',
    }
)
@api_view(['GET'])
@error_handling
def get_info_gene(request):
    """Function to get information about a gene from Ensembl database using Django ORM.

    Parameters:
    gene_name (str): The name of the gene to search for.

    Returns:
    dict: A dictionary containing information about the gene.
    """
    query = RnaPrecomputed.objects.using('external').filter(
        taxid__lineage__icontains='cellular organisms; Bacteria; %',
        is_active=True,
        rna_type='rRNA'
    ).values('id')
    return render(request, 'polls/info_gene.html', {"genes": query})


@swagger_auto_schema(
    method='get',
    operation_description="Redirects to the Disclaimer page.",
    responses={
        200: 'Returns a rendered Disclaimer page.',
        500: 'Internal Server Error if something goes wrong.',
    }
)
@api_view(['GET'])
@error_handling
def disclaimer(request):
    """
    Redirects to the Disclaimer page.

    Parameters:
    request (HttpRequest): The request object

    Returns:
    HttpResponse: An HTTP response with the rendered Disclaimer page.
    """
<<<<<<< HEAD
=======

>>>>>>> 07bd1c18571c6bbfb47f8c669322eb3ec9cdab28
    return render(request, 'polls/disclaimer.html')








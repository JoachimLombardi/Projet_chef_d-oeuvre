# python manage.py search_index --create 
# python manage.py commands index_articles  
# python manage.py commands evaluate_rag_model
# python manage.py commands scrap_article
# python manage.py commands article_to_database

from django.core.management.base import BaseCommand
from django_elasticsearch_dsl.registries import registry
from polls.models import Article
from polls.documents import ArticleDocument
from elasticsearch.exceptions import NotFoundError
from polls.documents import index
from polls.es_config import INDEX_NAME
from polls.rag_evaluation.evaluation_rag_model import evaluate_rag
from polls.business_logic import scrap_article_to_json, article_json_to_database


class Command(BaseCommand):
    help = 'Command to manage various operations'

    def add_arguments(self, parser):
        parser.add_argument('operation', type=str, help="Specify the operation")
        parser.add_argument('--request', type=str, help="Optional request data") 


    def handle(self, *args, **kwargs):
        self.operation = kwargs['operation']
        request_data = kwargs.get('request')
        if self.operation == 'index_articles':
            self.index_articles()
        elif self.operation == 'evaluate_rag_model':
            self.evaluate_rag_model()
        elif self.operation == 'scrap_article':
            self.scrap_article(request_data)
        elif self.operation == 'article_to_database':
            self.article_to_database(request_data)
        else:
            self.stdout.write(self.style.ERROR('Invalid operation'))


    def index_articles(self):
        # Indexer les articles
        articles = Article.objects.filter(term=INDEX_NAME)
        for article in articles:
            # Préparer le vecteur avant de mettre à jour le document
            title_abstract_vector = article.get_vector()  # Appeler votre méthode de génration de vecteur ici
            doc = ArticleDocument(
                meta={'id': article.id},  # Assurez-vous que le document a le bon ID
                title=article.title,
                abstract=article.abstract,
                title_abstract_vector=title_abstract_vector  # Passer le vecteur au document
            )
            doc.save()  # Enregistrer le document dans Elasticsearch
        self.stdout.write(self.style.SUCCESS('Successfully indexed articles'))


    def evaluate_rag_model(self):
        # RAG model evaluation logic
        score_generation, score_retrieval = evaluate_rag()
        self.stdout.write(self.style.SUCCESS(f'RAG model score generation: {score_generation}, RAG model score retrieval: {score_retrieval}'))


    def scrap_article(self, request_data):
        scrap_article_to_json(request_data)
        self.stdout.write(self.style.SUCCESS('Successfully scraped articles'))

    
    def article_to_database(self, request_data):
        article_json_to_database(request_data)
        self.stdout.write(self.style.SUCCESS('Successfully imported articles'))



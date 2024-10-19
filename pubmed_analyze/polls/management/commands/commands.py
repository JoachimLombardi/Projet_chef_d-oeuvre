# python manage.py search_index --create 
# python manage.py commands index_articles  
# python manage.py commands evaluate_rag_model

from django.core.management.base import BaseCommand
from django_elasticsearch_dsl.registries import registry
from polls.models import Article
from polls.documents import ArticleDocument
from elasticsearch.exceptions import NotFoundError
from polls.documents import index
from polls.rag_evaluation.evaluation_rag_model import evaluate_rag


class Command(BaseCommand):
    help = 'Command to manage various operations'

    def add_arguments(self, parser):
        parser.add_argument('operation', type=str, help="Specify the operation: 'index_articles' or 'evaluate_rag'")


    def handle(self, *args, **kwargs):
        self.operation = kwargs['operation']
        if self.operation == 'index_articles':
            self.index_articles()
        elif self.operation == 'evaluate_rag_model':
            self.evaluate_rag_model()
        else:
            self.stdout.write(self.style.ERROR('Invalid operation'))


    def index_articles(self):
        # Indexer les articles
        articles = Article.objects.all()
        for article in articles:
            # Préparer le vecteur avant de mettre à jour le document
            title_abstract_vector = article.get_title_abstract_vector()  # Appeler votre méthode de génration de vecteur ici
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
        score_generation, score_retrieval = self.calculate_rag_score()
        self.stdout.write(self.style.SUCCESS(f'RAG model score generation: {score_generation}, RAG model score retrieval: {score_retrieval}'))


    def calculate_rag_score(self):
        # Logic for evaluating and scoring your RAG model
        return evaluate_rag()

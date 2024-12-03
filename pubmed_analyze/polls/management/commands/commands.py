# python manage.py search_index --create 
# python manage.py commands index_articles  
# python manage.py commands scrap_article
# python manage.py commands article_to_database
# python manage.py commands plot_scores


from django.core.management.base import BaseCommand
from django_elasticsearch_dsl.registries import registry
from polls.models import Article
from polls.documents import ArticleDocument
from polls.documents import index
from polls.es_config import INDEX_NAME
from polls.business_logic import scrap_article_to_json, article_json_to_database
from polls.rag_evaluation.evaluation_rag_model import plot_scores


class Command(BaseCommand):
    help = 'Command to manage various operations'

    def add_arguments(self, parser):
        parser.add_argument('operation', type=str, help="Specify the operation")


    def handle(self, *args, **kwargs):
        self.operation = kwargs['operation']
        if self.operation == 'index_articles':
            self.index_articles()
        elif self.operation == 'scrap_article':
            self.scrap_article()
        elif self.operation == 'article_to_database':
            self.article_to_database()
        elif self.operation == 'plot_scores':
            plot_scores()
        else:
            self.stdout.write(self.style.ERROR('Invalid operation'))


    def index_articles(self):
        # Indexer les articles
        articles = Article.objects.all()
        for article in articles:
            # Préparer le vecteur avant de mettre à jour le document
            title_abstract_vector = article.get_vector()  # Appeler votre méthode de génration de vecteur ici
            doc = ArticleDocument(
                meta={'id': article.id},  # Assurez-vous que le document a le bon ID
                title=article.title,
                abstract=article.abstract,
                title_abstract_vector=title_abstract_vector  
            )
            doc.save()  # Enregistrer le document dans Elasticsearch
        self.stdout.write(self.style.SUCCESS('Successfully indexed articles'))


    def scrap_article(self):
        scrap_article_to_json()
        self.stdout.write(self.style.SUCCESS('Successfully scraped articles'))

    
    def article_to_database(self):
        article_json_to_database()
        self.stdout.write(self.style.SUCCESS('Successfully imported articles'))


    def plot_scores(self):
        plot_scores()
        self.stdout.write(self.style.SUCCESS('Successfully plotted scores'))


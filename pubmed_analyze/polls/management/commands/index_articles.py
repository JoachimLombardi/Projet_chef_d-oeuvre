# python manage.py search_index --create 
# python manage.py index_articles  

from django.core.management.base import BaseCommand
from django_elasticsearch_dsl.registries import registry
from polls.models import Article
from polls.documents import ArticleDocument
from elasticsearch.exceptions import NotFoundError
from polls.documents import index


class Command(BaseCommand):
    help = 'Index articles into Elasticsearch with KNN vectors'

    def handle(self, *args, **kwargs):
        # Indexer les articles
        articles = Article.objects.filter(term=index)
        for article in articles:
            # Préparer le vecteur avant de mettre à jour le document
            title_abstract_vector = article.get_title_abstract_vector()  # Appeler votre méthode de génération de vecteur ici
            doc = ArticleDocument(
                meta={'id': article.id},  # Assurez-vous que le document a le bon ID
                title=article.title,
                abstract=article.abstract,
                title_abstract_vector=title_abstract_vector  # Passer le vecteur au document
            )
            doc.save()  # Enregistrer le document dans Elasticsearch
        self.stdout.write(self.style.SUCCESS('Successfully indexed articles'))

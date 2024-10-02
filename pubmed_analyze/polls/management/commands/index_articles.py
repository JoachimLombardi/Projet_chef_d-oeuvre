from django.core.management.base import BaseCommand
from django_elasticsearch_dsl.registries import registry
from polls.models import Article
from polls.documents import ArticleDocument  # Ensure this import is correct

class Command(BaseCommand):
    help = 'Index articles into Elasticsearch with KNN vectors'

    def handle(self, *args, **kwargs):
        articles = Article.objects.all()
        for article in articles:
            # Prepare the vector before updating the document
            title_vector = article.get_title_abstract_vector()  # Call your vector generation method here
            doc = ArticleDocument(
                meta={'id': article.id},  # Ensure the document has the correct ID
                title=article.title,
                abstract=article.abstract,
                title_vector=title_vector  # Pass the vector to the document
            )
            doc.save()  # Save the document to Elasticsearch
        self.stdout.write(self.style.SUCCESS('Successfully indexed articles'))

# python manage.py search_index --create 
# python manage.py commands index_articles  
# python manage.py commands scrap_article
# python manage.py commands article_to_database
# python manage.py commands plot_scores
# python manage.py commands article_full_to_database


from django.core.management.base import BaseCommand
from polls.models import Article
from polls.documents import ArticleDocument
from polls.documents import index
from polls.es_config import INDEX_NAME
from polls.business_logic import scrap_article_to_json, article_json_to_database, articles_full_to_database
from polls.rag_evaluation.evaluation_rag_model import plot_scores


class Command(BaseCommand):
    help = 'Command to manage various operations'

    def add_arguments(self, parser):
        """
        Add command-line arguments to the parser.

        Args:
            parser (argparse.ArgumentParser): The argument parser to which 
            command-line arguments are added.

        The added argument is:
            operation (str): Specifies the operation to be performed by the command.
        """

        parser.add_argument('operation', type=str, help="Specify the operation")


    def handle(self, *args, **kwargs):
        """
        Handles the command operations.

        Given the operation specified by the command-line argument, this method
        performs the corresponding operation.

        Args:
            *args: Command-line arguments
            **kwargs: Command-line keyword arguments

        """
        self.operation = kwargs['operation']
        if self.operation == 'index_articles':
            self.index_articles()
        elif self.operation == 'scrap_article':
            self.scrap_article()
        elif self.operation == 'article_to_database':
            self.article_to_database()
        elif self.operation == 'plot_scores':
            self.plot_scores()
        elif self.operation == 'article_full_to_database':
            self.articles_full_database()
        else:
            self.stdout.write(self.style.ERROR('Invalid operation'))


    def index_articles(self):
        """
        Indexes all articles in the database to the Elasticsearch index.

        This method fetches all articles from the database and creates an
        Elasticsearch document for each one. The document contains the article's
        title, abstract, and a DenseVectorField containing the article's
        title-abstract vector. The document is then saved to the Elasticsearch
        index.

        The method prints a success message to the console once all articles have
        been indexed.

        """
        articles = Article.objects.all()
        for article in articles:
            title_abstract_vector = article.get_vector()  
            doc = ArticleDocument(
                meta={'id': article.id},  
                title=article.title,
                abstract=article.abstract,
                title_abstract_vector=title_abstract_vector  
            )
            doc.save() 
        self.stdout.write(self.style.SUCCESS('Successfully indexed articles'))


    def scrap_article(self):
        """
        Scrapes articles from PubMed and saves them to a JSON file.

        This method calls `scrap_article_to_json` to scrape articles from PubMed
        and saves the scraped data to a JSON file. The method prints a success
        message to the console once all articles have been scraped.

        """
        scrap_article_to_json()
        self.stdout.write(self.style.SUCCESS('Successfully scraped articles'))

    
    def article_to_database(self):
        """
        Imports articles from JSON file to the database.

        This method calls `article_json_to_database` to import articles from a JSON file
        and saves the imported data to the database. The method prints a success
        message to the console once all articles have been imported.

        """
        article_json_to_database()
        self.stdout.write(self.style.SUCCESS('Successfully imported articles'))


    def plot_scores(self):
        """
        Plots the scores of the last evaluation of each model.

        This method calls the `plot_scores` function to read JSON files, extract scores,
        and plot them in a bar chart. The plot is saved as 'scores_plot_retrieval.png',
        and a success message is printed to the console.
        """
        plot_scores()
        self.stdout.write(self.style.SUCCESS('Successfully plotted scores'))


    def articles_full_database(self): 
        """
        Imports articles from JSON file to the database.

        This method calls `article_json_to_database` to import articles from a JSON file
        and saves the imported data to the database. The method prints a success
        message to the console once all articles have been imported.

        """
        articles_full_to_database()
        self.stdout.write(self.style.SUCCESS('Successfully imported articles'))
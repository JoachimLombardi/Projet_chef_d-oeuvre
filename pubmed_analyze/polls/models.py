# python manage.py makemigrations polls
# python manage.py migrate
# To empty the database:
# python manage.py flush
# Important changes in models: 
# 1. remove and recreate database
# 2. remove migrations files
# 3. Reexcecute migrations


from django.db import models
from .utils import text_processing
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract')

class Affiliations(models.Model):
    name = models.TextField(null=True, verbose_name='name of affiliation', db_column='name of affiliation')

    def __str__(self):
        return self.name
    

class Authors(models.Model):
    name = models.CharField(null=True, max_length=2000, verbose_name='name of author', db_column='name of author')

    def __str__(self):
        return self.name


class Article(models.Model):
    title_review = models.CharField(null=True, max_length=2000, verbose_name='title of review', db_column='title of review')
    date = models.DateField(null=True, verbose_name='date of publication', db_column='date of publication')
    title = models.CharField(null=True, max_length=2000, verbose_name='title of article', db_column='title of article')
    abstract = models.TextField(null=True, verbose_name='abstract', db_column='abstract')
    pmid = models.IntegerField(null=True, verbose_name='pubmed id', db_column='pubmed id')
    doi = models.CharField(null=True, max_length=200, verbose_name='doi', db_column='doi')
    disclosure = models.TextField(null=True, verbose_name='conflict of interest', db_column='conflict of interest')
    mesh_terms = models.TextField(null=True, verbose_name='mesh terms', db_column='mesh terms')
    url = models.CharField(max_length=200, null=True, verbose_name='url', db_column='url')
    term = models.CharField(null=True, max_length=200, verbose_name='term', db_column='term')
    authors = models.ManyToManyField(Authors, through='Authorship', related_name='articles')

    def get_vector(article):
        title = text_processing(article.title) 
        abstract = text_processing(article.abstract)  
        return model.encode(title + " " + abstract).tolist()
  
    def __str__(self):
        return self.title
   

class Authorship(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='authorships')
    author = models.ForeignKey(Authors, on_delete=models.CASCADE)
    affiliation = models.ForeignKey(Affiliations, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('article', 'author', 'affiliation')

    def __str__(self):
        return f"{self.author.name} - {self.affiliation.name} (Article: {self.article.title})"


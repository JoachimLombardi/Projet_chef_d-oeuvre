from django.db import models
from .utils import get_vector


    
class Affiliations(models.Model):
    name = models.TextField(null=True, verbose_name='name of affiliation', db_column='name of affiliation')

    def __str__(self):
        return self.name
    

class Authors(models.Model):
    name = models.CharField(null=True, verbose_name='name of author', db_column='name of author')

    def __str__(self):
        return self.name


class Article(models.Model):
    title_review = models.CharField(null=True, verbose_name='title of review', db_column='title of review')
    date = models.DateTimeField(null=True, verbose_name='date of publication', db_column='date of publication')
    title = models.CharField(null=True, verbose_name='title of article', db_column='title of article')
    abstract = models.TextField(null=True, verbose_name='abstract', db_column='abstract')
    pmid = models.IntegerField(null=True, verbose_name='pubmed id', db_column='pubmed id')
    doi = models.CharField(null=True, verbose_name='doi', db_column='doi')
    disclosure = models.TextField(null=True, verbose_name='conflict of interest', db_column='conflict of interest')
    mesh_terms = models.TextField(null=True, verbose_name='mesh terms', db_column='mesh terms')
    url = models.CharField(max_length=200, null=True, verbose_name='url', db_column='url')
    authors = models.ManyToManyField(Authors, through='Authorship', related_name='articles')

    def get_title_abstract_vector(self):
        return get_vector(self)
  
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

class Cited_by(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, null=True, verbose_name='article id')
    doi = models.CharField(max_length=200, null=True, verbose_name='doi')
    pmid = models.IntegerField(null=True, verbose_name='pubmed id')
    url = models.CharField(max_length=200, null=True, verbose_name='url')
    

    def __str__(self):
        return self.review_title
    

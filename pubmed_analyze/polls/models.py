
from django.db import models
from django import forms


class Authors(models.Model):
    name = models.CharFieldField(null=True, verbose_name='name of author', db_column='name of author')

    def __str__(self):
        return self.name
    
class Affiliations(models.Model):
    name = models.TextField(null=True, verbose_name='name of affiliation', db_column='name of affiliation')

    def __str__(self):
        return self.name


class Article(models.Model):
    title_review = models.CharField(null=True, verbose_name='title of review', db_column='title of review')
    pub_date = models.DateTimeField(null=True, verbose_name='date of publication', db_column='date of publication')
    title = models.CharField(null=True, verbose_name='title of article', db_column='title of article')
    abstract = models.TextField(null=True, verbose_name='abstract', db_column='abstract')
    pmid = models.IntegerField(null=True, verbose_name='pubmed id', db_column='pubmed id')
    doi = models.CharField(null=True, verbose_name='doi', db_column='doi')
    disclosure = models.TextField(null=True, verbose_name='conflict of interest', db_column='conflict of interest')
    mesh_terms = models.TextField(null=True, verbose_name='mesh terms', db_column='mesh terms')
    url = models.CharField(max_length=200, null=True, verbose_name='url', db_column='url')


    def __str__(self):
        return self.title

class Articles_authors_affiliations(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE,verbose_name='article')
    author = models.ForeignKey(Authors, on_delete=models.CASCADE, verbose_name='author')
    affiliation = models.ForeignKey(Affiliations, on_delete=models.CASCADE, verbose_name='affiliation')
    
   

class Cited_by(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, null=True, verbose_name='article id')
    doi = models.CharField(max_length=200, null=True, verbose_name='doi')
    pmid = models.IntegerField(null=True, verbose_name='pubmed id')
    url = models.CharField(max_length=200, null=True, verbose_name='url')
    

    def __str__(self):
        return self.review_title
    


from django.db import models


class Review(models.Model):
    title = models.CharField(max_length=200, null=True)
    abbreviation = models.CharField(max_length=200, null=True)
    issn = models.CharField(max_length=200, null=True)
    impact_factor = models.CharField(max_length=200, null=True)
    

    def __str__(self):
        return self.title


class Article(models.Model):
    review = models.ForeignKey(Review, null=True, on_delete=models.SET_NULL)
    title_review = models.TextField(null=True)
    pub_date = models.DateTimeField("date published", null=True)
    title = models.TextField(null=True)
    authors = models.TextField(null=True)
    author_affiliation = models.TextField(null=True)
    abstract = models.TextField(null=True)
    pmid = models.IntegerField(null=True)
    doi = models.TextField(null=True)
    disclosure = models.TextField(null=True)
    mesh_terms = models.TextField(null=True)
    url = models.CharField(max_length=200, null=True)


    def __str__(self):
        return self.title
    

class Cited_by(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, null=True)
    review = models.ForeignKey(Review, null=True, on_delete=models.SET_NULL)
    doi = models.CharField(max_length=200, null=True)
    pmid = models.IntegerField(null=True)
    url = models.CharField(max_length=200, null=True)
    

    def __str__(self):
        return self.review_title
    

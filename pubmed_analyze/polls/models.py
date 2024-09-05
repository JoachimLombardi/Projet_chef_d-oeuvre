from django.utils import timezone
from django.db import models
import datetime


class Review(models.Model):
    title = models.CharField(max_length=200)
    impact_factor = models.FloatField(default=0)
    issn = models.IntegerField()

    def __str__(self):
        return self.title


class Article(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE)
    pub_date = models.DateTimeField("date published")
    title = models.CharField(max_length=200)
    authors = models.CharField(max_length=200)
    author_affiliation = models.CharField(max_length=200)
    abstract = models.CharField(max_length=200)
    pmid = models.IntegerField()
    doi = models.CharField(max_length=200)
    mesh_terms = models.CharField(max_length=200)
    disclosure = models.CharField(max_length=200)

    def __str__(self):
        return self.title
    
    def was_published_recently(self):
        return self.pub_date >= timezone.now() - datetime.timedelta(days=1)

    def format_date(self):
        return self.pub_date.strftime('%d/%m/%Y %H:%M:%S')

    def get_absolute_url(self):
        return "https://pubmed.ncbi.nlm.nih.gov/"+str(self.pmid)
    

    def __str__(self):
        return self.names


class Cited_by(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    review = models.ForeignKey(Review, on_delete=models.CASCADE)
    pmid = models.IntegerField()
    doi = models.CharField(max_length=200)

    def __str__(self):
        return self.review_title
    
    def format_date(self):
        return self.pub_date.strftime('%d/%m/%Y %H:%M:%S')
    
    def get_absolute_url(self):
        return "https://pubmed.ncbi.nlm.nih.gov/"+str(self.pmid)
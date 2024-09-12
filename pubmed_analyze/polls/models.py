
from django.db import models

class Authors(models.Model):
    name = models.CharField(max_length=200, null=True)

    def __str__(self):
        return self.name
    
class Affiliations(models.Model):
    name = models.TextField(null=True)

    def __str__(self):
        return self.affiliation

class Article(models.Model):
    title_review = models.TextField(null=True)
    pub_date = models.DateTimeField("date published", null=True)
    title = models.TextField(null=True)
    abstract = models.TextField(null=True)
    pmid = models.IntegerField(null=True)
    doi = models.TextField(null=True)
    disclosure = models.TextField(null=True)
    mesh_terms = models.TextField(null=True)
    url = models.CharField(max_length=200, null=True)


    def __str__(self):
        return self.title

class Articles_authors_affiliations(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, null=True)
    author = models.ForeignKey(Authors, on_delete=models.CASCADE, null=True)
    affiliation = models.ForeignKey(Affiliations, on_delete=models.CASCADE, null=True)
    
   

class Cited_by(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, null=True)
    doi = models.CharField(max_length=200, null=True)
    pmid = models.IntegerField(null=True)
    url = models.CharField(max_length=200, null=True)
    

    def __str__(self):
        return self.review_title
    

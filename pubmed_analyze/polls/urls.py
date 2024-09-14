from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("article/", views.extract_article_info, name="article"),
    path("articles_authors_affiliations/", views.create_articles_authors_affiliations, name="articles_authors_affiliations")
]
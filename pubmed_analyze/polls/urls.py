from django.urls import path

from . import views

urlpatterns = [
    # path("hello", views.index, name="index"),
    path("article/", views.extract_article_info, name="article"),
    path("cited_by/", views.extract_cited_by, name="cited_by"),
    path("article_authors_affiliations/", views.create_article_authors_affiliations, name="article_authors_affiliations")
]
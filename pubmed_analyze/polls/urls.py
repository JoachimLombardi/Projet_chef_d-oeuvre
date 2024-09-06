from django.urls import path

from . import views

urlpatterns = [
    # path("hello", views.index, name="index"),
    path("review/", views.extract_reviews_info, name="review"),
    path("article/", views.extract_article_info, name="article"),
    path("cited_by/", views.extract_cited_by, name="cited_by"),
]
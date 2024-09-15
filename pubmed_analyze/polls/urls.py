from django.urls import path

from . import views

urlpatterns = [
    path("article/", views.extract_article_info, name="extract_article"),
    path("articles_authors_affiliations/", views.extract_articles_authors_affiliations, name="extract_articles_authors_affiliations"),
    path('article/new/', views.create_article, name='create_article'),
    path('article/read/', views.article_list, name='article_list'), 
    path('article/<int:id>/edit/', views.update_article, name='update_article'),  
    path('article/<int:id>/delete/', views.delete_article, name='delete_article'), 
    path('author/read/', views.author_list, name='author_list'), 
    path('author/<int:id>/edit/', views.update_author, name='update_author'),  
    path('author/<int:id>/delete/', views.delete_author, name='delete_author'), 
    path('affiliation/read/', views.affiliation_list, name='affiliation_list'), 
    path('affiliation/<int:id>/edit/', views.update_affiliation, name='update_affiliation'),  
    path('affiliation/<int:id>/delete/', views.delete_affiliation, name='delete_affiliation'),
]
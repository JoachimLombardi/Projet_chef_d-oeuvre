from django.urls import path

from . import views

urlpatterns = [
    path("article/extract/", views.extract_article_info, name="extract_article"),
    path('article/new/', views.create_article, name='create_article'),
    path('article/read/', views.article_list, name='article_list'), 
    path('article/<int:id>/edit/', views.update_article, name='update_article'),  
    path('article/<int:id>/delete/', views.delete_article, name='delete_article'), 
    path('author/read/', views.author_list, name='author_list'),  
    path('affiliation/read/', views.affiliation_list, name='affiliation_list'), 
]
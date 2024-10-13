from django.urls import path

from . import views

urlpatterns = [
    path("article/scrap_to_json/", views.scrap_article_to_json, name="scrap_article_to_json"),
    path('articles/json_to_database/', views.article_json_to_database, name='article_json_to_database'),
    path('article/create/', views.create_article, name='create_article'),
    path('article/read/', views.article_list, name='article_list'), 
    path('article/<int:id>/update/', views.update_article, name='update_article'),  
    path('article/<int:id>/delete/', views.delete_article, name='delete_article'), 
    path('articles/rag/', views.rag_articles, name='rag_articles'),
]
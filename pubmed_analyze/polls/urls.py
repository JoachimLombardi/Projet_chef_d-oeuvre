from django.urls import path

from . import views

urlpatterns = [
    path("article/extract/", views.extract_article_info, name="extract_article"),
    path('article/create/', views.create_article, name='create_article'),
    path('article/read/', views.article_list, name='article_list'), 
    path('article/<int:id>/update/', views.update_article, name='update_article'),  
    path('article/<int:id>/delete/', views.delete_article, name='delete_article'), 
    path('articles/export/json/', views.export_articles_json, name='export_articles_json'),
    # path('articles/search/', views.search_articles, name='search_articles'),
    path('articles/rag/', views.rag_articles, name='rag_articles'),
]
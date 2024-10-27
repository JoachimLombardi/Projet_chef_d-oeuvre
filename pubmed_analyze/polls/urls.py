from django.urls import path
from . import views

urlpatterns = [
    path('article/create/', views.create_article, name='create_article'),
    path('article/read/', views.article_list, name='article_list'), 
    path('article/<int:id>/update/', views.update_article, name='update_article'),  
    path('article/<int:id>/delete/', views.delete_article, name='delete_article'), 
    path('articles/rag/', views.rag_articles, name='rag_articles'),
    path('register/', views.register, name='register'),
    path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),
]
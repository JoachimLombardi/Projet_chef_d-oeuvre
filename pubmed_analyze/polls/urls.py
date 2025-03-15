# http://127.0.0.1:8000/swagger/

from . import views
from django.urls import path, include, re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Pumed Analyze API",
        default_version="v1",
        description="Documentation de l'API",
        terms_of_service="github.com/JoachimLombardi/Projet_chef_d-oeuvre",
        contact=openapi.Contact(email="lombardi.joachim@gmail.com"),
        license=openapi.License(name="Free License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    re_path(r'^article/create_update(?:/(?P<pk>\d+))?/$', views.create_or_update_article, name='create_update_article'),
    path('article/read/', views.article_list, name='article_list'), 
    path('article/<int:id>/delete/', views.delete_article, name='delete_article'), 
    path('articles/rag/', views.rag_articles, name='rag_articles'),
    path('register/create_update/', views.create_or_update_register, name='create_update_profile'),
    path('profile/', views.user_profile, name='profile'),
    path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('delete-account/', views.delete_account, name='delete_account'),
    path('forbidden/', views.forbidden, name='forbidden'),
    path('evaluate/rag', views.evaluate_rag, name='evaluate_rag'),
    path('grafana/', views.grafana, name='grafana'),
    path('uptime_kuma/', views.uptime_kuma, name='uptime_kuma'),
    path("", include("django_prometheus.urls")),
    path('gene/', views.get_info_gene, name='get_info_gene'),
    path("app_doc/", schema_view.with_ui("swagger", cache_timeout=0), name="app_doc"),
    path('disclaimer/', views.disclaimer, name='disclaimer'),

]
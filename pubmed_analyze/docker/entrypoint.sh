#!/bin/bash

# Vérification des migrations
if python manage.py showmigrations | grep '\[ \]'; then
  echo 'Migrations en attente, application...'
  python manage.py makemigrations
  python manage.py migrate
else
  echo 'Aucune migration en attente.'
fi

# Vérification de l'existence d'un superutilisateur
if python manage.py shell -c "from django.contrib.auth import get_user_model; print(get_user_model().objects.filter(is_superuser=True).exists())" | grep -q 'False'; then
  echo 'Création du superutilisateur...'
  python manage.py createsuperuser --noinput
else
  echo 'Superutilisateur déjà existant.'
fi

# Vérification des articles dans la base de données
if ! python manage.py shell -c "from pubmed_analyze.models import Article; exit(1 if Article.objects.exists() else 0)"; then
  echo 'Ajout des articles à la base de données...'
  python manage.py commands article_to_database
else
  echo 'Les articles sont déjà ajoutés.'
fi

# Vérification de l'indexation des articles
if ! python manage.py shell -c "from django_elasticsearch_dsl.registries import registry; exit(1 if registry.get_documents() else 0)"; then
  echo 'Indexation des articles...'
  python manage.py commands index_articles
else
  echo 'Les articles sont déjà indexés.'
fi

# Démarrage du serveur Django
echo 'Démarrage du serveur Django...'
python manage.py runserver 0.0.0.0:8000

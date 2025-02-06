#!/bin/bash

# Attente de la base de données
echo "Attente de la base de données..."
while ! nc -z db 5432; do
  sleep 1
done
echo "Base de données prête."

# Appliquer les migrations Django
echo "Exécution des migrations Django..."
python manage.py makemigrations
python manage.py migrate

# Créer un superutilisateur si nécessaire
echo "Création du superutilisateur..."
python manage.py createsuperuser --noinput || echo "Superutilisateur déjà existant"

# Exécuter des commandes personnalisées si nécessaire
echo "Exécution des commandes personnalisées..."
python manage.py commands article_to_database
python manage.py commands index_articles

# Lancer le serveur Django
echo "Démarrage du serveur Django..."
python manage.py runserver 0.0.0.0:8000

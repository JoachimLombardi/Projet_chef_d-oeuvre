#!/bin/bash

# Vérification de la disponibilité des dépendances
echo "Attente de la base de données..."
while ! nc -z db 5432; do
  sleep 1
done
echo "Base de données prête."

echo "Attente d'Elasticsearch..."
while ! nc -z elasticsearch 9200; do
  sleep 1
done
echo "Elasticsearch prêt."

# Appliquer les migrations Django
echo "Exécution des migrations Django..."
python manage.py makemigrations
python manage.py migrate

# Ajouter des commandes spécifiques si nécessaire
echo "Exécution des commandes personnalisées..."
python manage.py commands article_to_database
python manage.py commands index_articles

# Lancer le serveur Django
echo "Démarrage du serveur Django..."
exec "$@"

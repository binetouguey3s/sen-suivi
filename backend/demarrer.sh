#!/bin/sh
# Démarrage en production (Render, VPS) : met la base à jour, prépare les
# fichiers statiques, puis lance Gunicorn sur le port donné par l'hébergeur.
set -e

python manage.py migrate --noinput
# createcachetable crée la table du cache (compteurs d'échecs de connexion) si
# elle n'existe pas encore ; la commande ne fait rien si elle existe déjà.
python manage.py createcachetable
python manage.py collectstatic --noinput

# Remplit le RAG de Titou en arrière-plan : le site démarre sans l'attendre,
# même si le microservice IA est encore en train de se réveiller.
python manage.py reindexer_ressources &

exec gunicorn config.wsgi:application \
    --bind "0.0.0.0:${PORT:-8000}" \
    --workers "${GUNICORN_WORKERS:-2}" \
    --timeout 120 \
    --access-logfile -

# Sen Suivi — Back-end Django + DRF

FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# createcachetable crée la table du cache (compteurs d'échecs de connexion) si
# elle n'existe pas encore ; la commande ne fait rien si elle existe déjà.
CMD ["sh", "-c", "python manage.py createcachetable && python manage.py runserver 0.0.0.0:8000"]

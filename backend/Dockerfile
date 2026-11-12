# Sen Suivi — Back-end Django + DRF

FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Production : migrations, fichiers statiques puis Gunicorn (voir demarrer.sh).
# En développement, docker-compose remplace cette commande par runserver.
CMD ["sh", "demarrer.sh"]

# Sen Suivi — Microservice IA FastAPI

FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Télécharge dès la construction le modèle d'embeddings par défaut de ChromaDB
# (all-MiniLM-L6-v2, licence Apache 2.0, aucune clé requise) : le service
# n'a ainsi plus besoin d'Internet au démarrage ni après un redémarrage.
RUN python -c "from chromadb.utils.embedding_functions import DefaultEmbeddingFunction; DefaultEmbeddingFunction()(['amorce'])"

COPY . .

EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]

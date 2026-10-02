# Sen Suivi — Microservice IA FastAPI

FROM python:3.12-slim

WORKDIR /app

# PyTorch pèse plusieurs centaines de Mo : sur une connexion lente, pip
# abandonnait au bout de 15 s. Plus de patience, et quelques reprises.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DEFAULT_TIMEOUT=300 \
    PIP_RETRIES=10

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Télécharge dès la construction le modèle d'embeddings multilingue
# (EMBEDDING_MODELE du .env, transmis par docker-compose) : le service n'a
# ainsi plus besoin d'Internet au démarrage ni après un redémarrage.
ARG EMBEDDING_MODELE=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('${EMBEDDING_MODELE}')"

COPY . .

EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]

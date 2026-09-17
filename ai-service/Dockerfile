# Sen Suivi — Microservice IA FastAPI
# Le code applicatif (app/main.py, requirements.txt) sera ajouté à l'étape
# dédiée au chatbot. Ce Dockerfile deviendra fonctionnel à ce moment-là.

FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]

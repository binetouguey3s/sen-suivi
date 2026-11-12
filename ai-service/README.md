---
title: Sen Suivi IA
emoji: 🌿
colorFrom: green
colorTo: blue
sdk: docker
app_port: 8001
pinned: false
---

# Sen Suivi — microservice IA

Titou (chatbot), modération du forum, transcription et RAG des ressources.
Ce dossier est publié tel quel sur un Space Hugging Face (Docker) par le
workflow GitHub `.github/workflows/deployer-ia.yml`.

Le bloc en tête de ce fichier est lu par Hugging Face : `sdk: docker` construit
le `Dockerfile`, `app_port` est le port sur lequel le service écoute.

Réglages à saisir dans **Settings > Variables and secrets** du Space :

| Nom | Type | Rôle |
| --- | --- | --- |
| `AI_SERVICE_CLE` | Secret | Clé partagée avec Django (la même des deux côtés) |
| `BACKEND_URL` | Variable | Adresse du back-end, ex. `https://sen-suivi-api.onrender.com` |
| `CHROMA_PERSIST_DIR` | Variable | `/data/chroma` |
| `LLM_*`, `MISTRAL_*`, `MODERATION_*`, `TRANSCRIPTION_*` | Secrets | Comme dans `.env.example` |

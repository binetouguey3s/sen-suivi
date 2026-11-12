---
title: Sen Suivi IA
emoji: 🌿
colorFrom: green
colorTo: blue
sdk: gradio
sdk_version: 5.9.1
python_version: "3.12"
app_file: lancer_space.py
pinned: false
---

# Sen Suivi — microservice IA

Titou (chatbot), modération du forum, transcription et RAG des ressources.
Ce dossier est publié tel quel sur un Space Hugging Face (Docker) par le
workflow GitHub `.github/workflows/deployer-ia.yml`.

Le bloc en tête de ce fichier est lu par Hugging Face. Les Spaces Docker étant
payants, le Space est déclaré `gradio` (gratuit) : Hugging Face installe
`requirements.txt` puis exécute `lancer_space.py`, qui démarre le service FastAPI
sur le port 7860. Le `Dockerfile` sert au développement local (docker compose).

Réglages à saisir dans **Settings > Variables and secrets** du Space :

| Nom | Type | Rôle |
| --- | --- | --- |
| `AI_SERVICE_CLE` | Secret | Clé partagée avec Django (la même des deux côtés) |
| `BACKEND_URL` | Variable | Adresse du back-end, ex. `https://sen-suivi-api.onrender.com` |
| `LLM_*`, `MISTRAL_*`, `MODERATION_*`, `TRANSCRIPTION_*` | Secrets | Comme dans `.env.example` |

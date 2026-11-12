"""Point d'entrée du Space Hugging Face (SDK Gradio, gratuit).

Les Spaces Docker sont payants : le Space est donc déclaré « Gradio » dans
README.md, et Hugging Face exécute ce fichier. Il démarre simplement le
service FastAPI sur le port attendu par Hugging Face (7860).
En local et avec Docker, rien ne change : uvicorn app.main:app.
"""

import os

# Pas de disque persistant gratuit : l'index du RAG est reconstruit à chaque
# démarrage à partir du back-end (BACKEND_URL), dans un dossier temporaire.
os.environ.setdefault('CHROMA_PERSIST_DIR', '/tmp/chroma')

import uvicorn  # noqa: E402

if __name__ == '__main__':
    uvicorn.run('app.main:app', host='0.0.0.0', port=int(os.environ.get('PORT', '7860')))

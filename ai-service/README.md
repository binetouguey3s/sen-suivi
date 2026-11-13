# Sen Suivi — microservice IA

Titou (chatbot), modération du forum, transcription et RAG des ressources.

## Deux façons de le lancer

| | Local (docker compose) | En ligne (Render, offre gratuite) |
| --- | --- | --- |
| Image | `Dockerfile` | `Dockerfile.render` |
| Dépendances | `requirements.txt` (avec PyTorch) | `requirements-render.txt` (sans PyTorch) |
| Vecteurs du RAG | modèle sentence-transformers local | API Mistral (`EMBEDDING_FOURNISSEUR=mistral`) |
| Index ChromaDB | volume `chroma_data` | `/tmp/chroma`, reconstruit à chaque démarrage depuis `BACKEND_URL` |

La version en ligne tient dans les 512 Mo de Render (environ 120 Mo mesurés).
Changer de fournisseur de vecteurs crée une nouvelle collection : l'index se
reconstruit tout seul.

## Réglages propres à la mise en ligne

| Nom | Rôle |
| --- | --- |
| `AI_SERVICE_CLE` | Clé partagée avec Django (la même des deux côtés) |
| `BACKEND_URL` | Adresse du back-end, ex. `https://sen-suivi-api.onrender.com` |
| `EMBEDDING_FOURNISSEUR` | `mistral` sur Render, `local` sinon |
| `MISTRAL_CLE_API`, `LLM_*`, `MODERATION_*`… | Comme dans `.env.example` |

Voir `DEPLOIEMENT.md` à la racine du dépôt.

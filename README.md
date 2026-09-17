# Sen Suivi

Plateforme sénégalaise de prévention, suivi et orientation vers le bien-être mental.
Projet de certification, Simplon Sénégal, Promo 9 (2025-2026). Autrice : Binetou Gueye.

Le contexte complet du projet (positionnement, stack, modèle de données, routes API,
charte graphique) est décrit dans la documentation de conception. Les spécifications
complémentaires (règles métier chiffrées, fixtures, correspondance écran → route →
endpoint) sont dans [`docs/SPECIFICATIONS.md`](./docs/SPECIFICATIONS.md).

---

## Prérequis

- Docker
- Docker Compose (plugin `docker compose`)

---

## Démarrer le projet en une commande

```bash
cp .env.example .env
docker compose up --build
```

Cette commande lance quatre services applicatifs et un moteur d'automatisation :

| Service | URL locale | Rôle |
|---|---|---|
| PostgreSQL | `localhost:5432` | Base de données |
| Django (back-end) | `http://localhost:8000` | API REST + authentification JWT |
| FastAPI (microservice IA) | `http://localhost:8001` | Chatbot à trois niveaux |
| Angular (front-end) | `http://localhost:4200` | Application web |
| n8n | `http://localhost:5678` | Automatisations (rappels, notifications, indexation RAG) |

Pour arrêter les services : `docker compose down`.
Pour arrêter et supprimer les données persistées (base de données, base vectorielle,
workflows n8n) : `docker compose down -v`.

> À ce stade du projet, seule l'ossature (dossiers, Dockerfile, configuration) existe.
> Le code applicatif est ajouté étape par étape ; `docker compose up --build` ne
> deviendra pleinement fonctionnel qu'une fois chaque service initialisé.

---

## Persistance des données

Trois volumes Docker nommés conservent les données entre deux redémarrages :

| Volume | Contenu |
|---|---|
| `postgres_data` | Base de données PostgreSQL |
| `chroma_data` | Base vectorielle ChromaDB du microservice IA, montée sur `CHROMA_PERSIST_DIR` |
| `n8n_data` | Workflows et identifiants n8n |

---

## Variables d'environnement

Toutes les variables sont documentées dans [`.env.example`](./.env.example). Copiez ce
fichier vers `.env` avant de lancer le projet ; `.env` n'est jamais versionné.

---

## Dépannage

**Port déjà utilisé**
Si un message indique qu'un port (5432, 8000, 8001, 4200 ou 5678) est déjà utilisé,
un autre service tourne déjà dessus sur votre machine. Arrêtez-le, ou modifiez le port
publié dans `docker-compose.yml` (partie gauche du mapping `"hôte:conteneur"`), par
exemple `"5433:5432"` pour PostgreSQL.

Ajoute dans la section Dépannage du README : le port 5432 de l'hôte peut
être occupé par un PostgreSQL installé localement. Dans ce cas, le service
db expose 5433 côté hôte ; la configuration interne reste inchangée
puisque les conteneurs communiquent par le réseau Docker.

**`.env` manquant**
Si Docker Compose signale des variables vides ou refuse de démarrer un service, vérifiez
que le fichier `.env` existe bien à la racine (`cp .env.example .env`). Le fichier
`.env.example` est versionné à titre de référence, mais Docker Compose lit `.env`.

**Le backend démarre avant que PostgreSQL soit prêt**
`depends_on` garantit seulement que le conteneur `db` est *démarré*, pas que PostgreSQL
*accepte déjà des connexions*. Si le backend échoue au lancement avec une erreur de
connexion à la base, relancez-le simplement :

```bash
docker compose up backend
```

Si le problème persiste régulièrement, une solution durable (à mettre en place lors de
l'étape back-end) consiste à ajouter un `healthcheck` sur le service `db` et une
condition `depends_on: condition: service_healthy` sur `backend`.

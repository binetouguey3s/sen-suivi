# Sen Suivi

Plateforme sénégalaise de prévention, suivi et orientation vers le bien-être mental.
Projet de certification, Simplon Sénégal, Promo 9 (2025-2026). Autrice : Binetou Gueye.

## Fonctionnalités

- **Journal d'humeur** et tableau de bord : suivi quotidien, courbe sur 7 jours, statistiques personnelles
- **Auto-évaluation** (stress, anxiété, fatigue) : score de tendance et suggestion de professionnels validés
- **Chatbot** accessible sans compte, qui oriente vers des ressources validées
- **Bibliothèque de ressources** (articles, exercices, podcasts) et **répertoire de lieux** de détente au Sénégal
- **Mise en relation** avec des professionnels, dont l'inscription est validée par un administrateur
- **Forum anonyme** (pseudonymes), avec modération a priori
- **Administration** : validation des professionnels, modération du forum, gestion des ressources
- **Ressources d'urgence** : numéros du Sénégal uniquement (800 805 805, 1515, 18)

Sen Suivi ne remplace pas un professionnel de santé.

### Le chatbot en trois niveaux

1. **Détection de détresse** (règles et mots-clés) : renvoi immédiat vers les ressources d'urgence.
2. **Classification d'intention** : réponse validée pour les intentions reconnues avec confiance.
3. **Recherche RAG** dans les ressources de la plateforme (ChromaDB) : le chatbot propose la ressource la plus proche.

La génération encadrée par un modèle de langage (Groq), à partir des seules ressources retrouvées, est en cours d'intégration.

---

## Structure du dépôt

```
sen-suivi/
├── frontend/          # Angular 22 : interface web (composants standalone, signals)
├── backend/           # Django 5.1 + DRF : API REST, JWT, 7 applications métier
├── ai-service/        # FastAPI : chatbot (détresse, intention, RAG avec ChromaDB)
├── automations/       # Workflows n8n exportés (JSON)
├── docs/              # Crédits et licences des images
├── docker-compose.yml # Orchestration des cinq services
└── .env.example       # Modèle des variables d'environnement
```

Les applications Django (`backend/apps/`) : `comptes`, `suivi`, `ressources`,
`relations`, `forum`, `chatbot`, `notifications`.

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
| PostgreSQL | `localhost:5433` | Base de données |
| Django (back-end) | `http://localhost:8000` | API REST + authentification JWT |
| FastAPI (microservice IA) | `http://localhost:8001` | Chatbot à trois niveaux |
| Angular (front-end) | `http://localhost:4200` | Application web |
| n8n | `http://localhost:5678` | Automatisations (rappels, notifications, indexation RAG) |

Pour arrêter les services : `docker compose down`.
Pour arrêter et supprimer les données persistées (base de données, base vectorielle,
workflows n8n) : `docker compose down -v`.

> **Clés externes** : le chatbot actuel fonctionne sans aucune clé (règles validées et
> recherche dans les ressources de la plateforme). La génération encadrée par un modèle de
> langage (Groq) est en cours d'intégration : ses variables `LLM_*` sont déjà prévues dans
> `.env.example`.
> Le seul secret à créer soi-même est `N8N_API_KEY`, une clé partagée entre Django et n8n
> pour leurs échanges internes : `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`,
> puis à coller dans `.env`.

### Premières commandes après le démarrage

Une fois les conteneurs lancés, préparez la base de données et l'index du chatbot :

```bash
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py seed_donnees
docker compose exec backend python manage.py reindexer_ressources
```

La commande de seed affiche le mot de passe commun à tous les comptes de
démonstration. Interface d'administration Django : `http://localhost:8000/admin/`.

Le front-end Angular se lance en développement avec `cd frontend && npm install && npm start`.

### Automatisations n8n

Les trois workflows (rappel d'inactivité après 3 jours, notification des administrateurs
à chaque inscription professionnelle, réindexation du RAG à chaque modification d'une
ressource) sont exportés dans [`automations/`](./automations). Pour les charger dans n8n :

```bash
docker compose exec n8n n8n import:workflow --separate --input=/automations
for id in $(docker compose exec -T n8n n8n list:workflow | cut -d'|' -f1); do
  docker compose exec -T n8n n8n publish:workflow --id=$id
done
docker compose restart n8n
```

### Tests

```bash
docker compose exec backend python manage.py test   # comptes (mots de passe, force brute, pro non validé), forum, score de tendance
cd ai-service && python -m venv .venv && .venv/bin/pip install -r requirements.txt && .venv/bin/python -m pytest   # détection de détresse, intentions
cd frontend && npm test -- --watch=false            # Vitest
```

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
Si un message indique qu'un port (5433, 8000, 8001, 4200 ou 5678) est déjà utilisé,
un autre service tourne déjà dessus sur votre machine. Le port 5432 de l'hôte est
souvent pris par un PostgreSQL déjà installé localement : c'est pourquoi le service
`db` publie son port sur **5433** côté hôte (`docker-compose.yml`). La configuration
interne reste inchangée, puisque les conteneurs communiquent entre eux par le réseau
Docker sur le port 5432. Si un autre port est occupé, modifiez la partie gauche du
mapping `"hôte:conteneur"` correspondant dans `docker-compose.yml`.

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

Si le problème persiste régulièrement, une solution durable (amélioration prévue)
consiste à ajouter un `healthcheck` sur le service `db` et une condition
`depends_on: condition: service_healthy` sur `backend`.

---

## Crédits des images

Les photographies proviennent de banques d'images libres de droits ; auteurs et licences
dans [`docs/CREDITS-IMAGES.md`](./docs/CREDITS-IMAGES.md).

---

## Branches

| Branche | Rôle |
|---|---|
| `main` | Version stable |
| `dev` | Intégration : reçoit chaque fonctionnalité terminée |
| `feat/<nom>` | Une branche par fonctionnalité, fusionnée dans `dev` |

Messages de commit en *conventional commits*, en français :
`feat(chatbot): ajoute la détection de détresse`.

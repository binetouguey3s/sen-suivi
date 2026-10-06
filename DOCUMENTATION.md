# Documentation technique complète — Sen Suivi

> Plateforme sénégalaise de prévention et de suivi du bien-être mental.
> Version au 6 octobre 2026.

---

## Table des matières

1. [Vision et contexte](#1-vision-et-contexte)
2. [Architecture globale](#2-architecture-globale)
3. [Infrastructure et déploiement (Docker Compose)](#3-infrastructure-et-déploiement-docker-compose)
4. [Service Backend — Django REST Framework](#4-service-backend--django-rest-framework)
   - 4.1 Choix techniques et pourquoi
   - 4.2 Configuration (`settings.py`)
   - 4.3 Modèle d'authentification
   - 4.4 App `comptes`
   - 4.5 App `suivi`
   - 4.6 App `chatbot`
   - 4.7 App `forum`
   - 4.8 App `orientation`
   - 4.9 App `relations`
   - 4.10 App `ressources`
   - 4.11 App `notifications`
5. [Service IA — FastAPI (ai-service)](#5-service-ia--fastapi-ai-service)
   - 5.1 Choix techniques et pourquoi
   - 5.2 Pipeline complet d'un message (`main.py`)
   - 5.3 Niveau 0 — Détection de détresse
   - 5.4 Niveau 1 — Classification d'intention
   - 5.5 Niveau 2a — Moteur RAG (ChromaDB)
   - 5.6 Niveau 2b — Génération encadrée (LLM)
   - 5.7 Validateur de réponse
   - 5.8 Modération du forum
   - 5.9 Chatbot vocal
6. [Service Frontend — Angular](#6-service-frontend--angular)
   - 6.1 Choix techniques et pourquoi
   - 6.2 Structure et routing
   - 6.3 Authentification côté client
   - 6.4 Intercepteur JWT
   - 6.5 Services principaux
7. [Service d'automatisation — n8n](#7-service-dautomatisation--n8n)
   - 7.1 Pourquoi n8n
   - 7.2 Les cinq workflows
   - 7.3 Endpoints internes Django
8. [Communications entre services](#8-communications-entre-services)
9. [Sécurité](#9-sécurité)
10. [Variables d'environnement (`.env`)](#10-variables-denvironnement-env)
11. [Guide de démarrage rapide](#11-guide-de-démarrage-rapide)

---

## 1. Vision et contexte

Sen Suivi est une plateforme de bien-être mental conçue pour le contexte sénégalais. Elle accompagne les utilisateurs à travers plusieurs fonctionnalités complémentaires :

- Un **chatbot empathique** nommé Titou, accessible sans compte, qui écoute, oriente et détecte les situations graves.
- Un **journal d'humeur** quotidien et des **auto-évaluations** (stress, anxiété, fatigue).
- Une **bibliothèque** d'articles, exercices et podcasts.
- Un **annuaire** de professionnels validés (psychologues, sophrologues, coachs, assistants sociaux, etc.) avec **mise en relation** directe.
- Un **forum anonyme** modéré automatiquement par l'IA.
- Un répertoire de **lieux de détente** au Sénégal.
- Des **rappels automatiques** doux (sans jamais culpabiliser l'utilisateur).

### Principes éthiques non négociables

Ces principes traversent tout le code et sont documentés dans chaque module concerné :

1. **Jamais de diagnostic** — aucun terme clinique, aucune maladie nommée, aucune promesse de guérison.
2. **Détresse avant tout** — la détection de détresse (niveau 0) s'applique en premier, avant toute autre logique IA. Une personne en détresse n'est jamais bloquée, jamais renvoyée vers un écran de paiement.
3. **Anonymat du forum** — les utilisateurs n'apparaissent que sous leur pseudonyme généré automatiquement.
4. **Confidentialité des échanges** — jamais le contenu des messages dans les notifications ou les logs. Seuls la nature et l'heure d'un signalement sont transmis à l'équipe.
5. **Gratuité permanente** — chatbot, urgence, journal, tests, bibliothèque, forum et consultation des profils restent gratuits pour toujours. Seule la mise en relation peut devenir payante après l'offre de lancement.
6. **Jeton d'urgence** — une personne en détresse obtient un jeton signé qui supprime tout écran de paiement pour la mise en relation.

---

## 2. Architecture globale

```
┌─────────────────────────────────────────────────────────────────┐
│                         RÉSEAU Docker                           │
│                      sensuivi_network                           │
│                                                                 │
│  ┌───────────────┐      ┌───────────────┐    ┌──────────────┐  │
│  │   Frontend    │      │    Backend    │    │  ai-service  │  │
│  │  Angular 22   │◄────►│  Django 5.x   │◄──►│  FastAPI     │  │
│  │  :4200        │      │  DRF + JWT    │    │  :8001       │  │
│  │               │      │  :8000        │    │  ChromaDB    │  │
│  └───────────────┘      └──────┬────────┘    └──────────────┘  │
│                                │                                │
│                    ┌───────────┼────────────┐                   │
│                    │           │            │                   │
│              ┌─────▼──┐  ┌────▼────┐  ┌────▼───┐              │
│              │  db    │  │  n8n    │  │(SMTP)  │              │
│              │Postgres│  │:5678    │  │externe │              │
│              │:5432   │  │         │  │        │              │
│              └────────┘  └─────────┘  └────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

**Cinq conteneurs** tournent en parallèle, tous sur le même réseau Docker bridge `sensuivi_network` :

| Conteneur | Technologie | Port | Rôle |
|---|---|---|---|
| `sensuivi_frontend` | Angular 22 | 4200 | Interface utilisateur |
| `sensuivi_backend` | Django 5 + DRF | 8000 | API REST, logique métier, base de données |
| `sensuivi_ai_service` | FastAPI + ChromaDB | 8001 | IA : chatbot, modération forum, vocal |
| `sensuivi_db` | PostgreSQL 16 | 5433 (hôte) | Base de données relationnelle |
| `sensuivi_n8n` | n8n | 5678 | Automatisation : rappels, notifications |

---

## 3. Infrastructure et déploiement (Docker Compose)

### Fichier `docker-compose.yml`

```yaml
services:
  db:        postgres:16-alpine   → base de données
  backend:   ./backend            → API Django
  ai-service:./ai-service         → microservice IA
  frontend:  ./frontend           → Angular compilé
  n8n:       n8nio/n8n            → automatisation
```

### Volumes persistants

- `postgres_data` — données PostgreSQL (ne jamais supprimer en prod)
- `chroma_data` — index vectoriel ChromaDB (reconstruit par `/reindexer`)
- `n8n_data` — données et identifiants n8n
- `./automations:/automations:ro` — workflows n8n exportés en lecture seule

### Pourquoi Docker Compose (et pas Kubernetes) ?

Le projet est à l'échelle d'un déploiement unique (un seul serveur). Docker Compose suffit, est bien plus simple à maintenir, et ne demande aucune expertise infrastructure avancée. Si l'application doit passer à l'échelle, la migration vers Kubernetes est possible car chaque service est déjà isolé dans son conteneur.

### Réseau Docker (`sensuivi_network`)

Tous les conteneurs s'appellent par leur nom de service (ex. `http://backend:8000`, `http://ai-service:8001`, `http://n8n:5678`). Aucun port n'est exposé entre eux sur l'hôte — uniquement les ports nécessaires à l'accès externe.

### Mapping des ports (hôte → conteneur)

```
5433:5432  →  PostgreSQL (5433 côté hôte pour éviter les conflits avec Postgres local)
8000:8000  →  Backend Django
8001:8001  →  Microservice IA FastAPI
4200:4200  →  Frontend Angular
5678:5678  →  Interface n8n
```

---

## 4. Service Backend — Django REST Framework

### 4.1 Choix techniques et pourquoi

| Technologie | Version | Pourquoi ce choix |
|---|---|---|
| **Django** | 5.x | Framework Python le plus complet, inclut l'ORM, l'admin, les migrations, les validateurs de mot de passe. Idéal pour une application avec des règles métier complexes. |
| **djangorestframework (DRF)** | 3.15 | Standard de facto pour les API REST en Python. Fournit serializers, views génériques, permissions. Évite de réinventer la roue. |
| **djangorestframework-simplejwt** | 5.3 | Authentification sans état (stateless) par JWT. Le frontend Angular peut vérifier le type de compte directement depuis le token, sans aller-retour supplémentaire. |
| **psycopg (v3)** | 3.2 | Driver PostgreSQL moderne, asynchrone-ready, plus performant que psycopg2. Version binaire (`psycopg[binary]`) pour simplifier l'installation. |
| **django-environ** | 0.11 | Lit les variables d'environnement du `.env` dans `settings.py`. Aucun secret en dur dans le code. |
| **django-cors-headers** | 4.4 | Le frontend Angular (port 4200) et le backend (port 8000) ont des origines différentes. Cette bibliothèque gère les en-têtes CORS de manière centralisée. |
| **httpx** | 0.28 | Client HTTP moderne (async-ready) pour appeler le microservice IA. Supporté nativement par FastAPI côté IA pour les tests. |
| **PostgreSQL 16** | — | Base de données relationnelle robuste. Le cache Django y est aussi stocké (table `cache_sen_suivi`), évitant d'ajouter Redis. |

### 4.2 Configuration (`settings.py`)

Le fichier `config/settings.py` est entièrement piloté par des variables d'environnement lues via `django-environ`. Aucune valeur sensible n'est codée en dur.

**Paramètres clés :**

```python
AUTH_USER_MODEL = 'comptes.CompteUtilisateur'
# CompteUtilisateur remplace le User Django natif : l'email est l'identifiant,
# pas le nom d'utilisateur.

CACHES = {'default': {'BACKEND': 'django.core.cache.backends.db.DatabaseCache', ...}}
# Le cache est stocké dans PostgreSQL (table cache_sen_suivi), créée par
# `python manage.py createcachetable`. Pas de Redis à gérer.

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ('rest_framework_simplejwt.authentication.JWTAuthentication',),
}

CORS_ALLOW_HEADERS = (*default_headers, 'x-jeton-urgence')
# L'en-tête X-Jeton-Urgence est ajouté pour le jeton de détresse du chatbot.

AI_SERVICE_URL = 'http://ai-service:8001'
# Communication interne Docker vers le microservice IA.

N8N_WEBHOOK_URL = 'http://n8n:5678'
# Communication interne Docker vers n8n.
```

**Validateurs de mot de passe** (directive sécurité) :
- Longueur minimale 8 caractères
- Similitude avec les attributs du compte
- Mots de passe courants interdits
- Numéros purs interdits
- Complexité (3 catégories sur 4) via `ComplexiteValidator`
- Suites évidentes (123456, azerty…) via `SuiteEvidenteValidator`

### 4.3 Modèle d'authentification

Django exige un `AUTH_USER_MODEL` concret (une vraie table). L'héritage multi-table est utilisé :

```
CompteUtilisateur (table comptes_compteutilisateur)
    ├── Utilisateur     (table comptes_utilisateur, lié par OneToOne)
    ├── Professionnel   (table comptes_professionnel, lié par OneToOne)
    └── Administrateur  (table comptes_administrateur, lié par OneToOne)
```

La propriété `type_compte` détecte dynamiquement le sous-type :
```python
@property
def type_compte(self):
    if hasattr(self, 'administrateur'): return 'administrateur'
    if hasattr(self, 'professionnel'): return 'professionnel'
    if hasattr(self, 'utilisateur'): return 'utilisateur'
```

Ce type est inclus comme **claim JWT** (`token['type_compte']`) au moment de la connexion, ce qui permet au frontend de connaître immédiatement le type de compte sans appel supplémentaire.

### 4.4 App `comptes`

**Modèles :**

| Modèle | Description |
|---|---|
| `CompteUtilisateur` | Base commune : email (identifiant), nom, mot de passe, préférences (JSONField), `is_active`, `is_staff`. |
| `Utilisateur` | Prénom, pseudonyme (généré automatiquement, unique, non modifiable), ville, `forum_suspendu_jusqu_au`. |
| `Professionnel` | Spécialité (6 valeurs fixées), ville, langue, tarif, présentation, domaines (JSONField), disponibilité, statut de validation (EN_ATTENTE / VALIDE / REFUSE). |
| `Administrateur` | Aucun champ supplémentaire, hérite tout de CompteUtilisateur. |
| `PersonneConfiance` | Proche optionnel, choisi par l'utilisateur. Jamais prévenu automatiquement sauf accord explicite (`alerte_automatique`). |
| `AlerteConfiance` | Trace d'une alerte envoyée à la personne de confiance (date et canal, jamais le contenu). |

**Pseudonyme :** généré à la création d'un Utilisateur depuis une liste de mots à consonance sénégalaise (`Teranga`, `Jamm`, `Baobab`, `Sahel`…) + un nombre entre 100 et 999. Unicité vérifiée en base. Non modifiable (`editable=False`).

**Endpoints :**

```
POST   /api/auth/register                 → inscription utilisateur
POST   /api/auth/login                    → connexion (JWT access + refresh)
POST   /api/auth/refresh                  → renouvellement du token
POST   /api/auth/mot-de-passe-oublie      → demande de réinitialisation (répond toujours 200)
POST   /api/auth/mot-de-passe-oublie/confirmer → confirmation du nouveau mdp
GET    /api/comptes/moi                   → profil du compte connecté
PATCH  /api/comptes/moi                   → mise à jour du profil
DELETE /api/comptes/moi                   → suppression avec confirmation par mdp
POST   /api/comptes/moi/mot-de-passe      → changement de mot de passe
GET/PUT/DELETE /api/comptes/moi/personne-confiance → gestion de la personne de confiance
POST   /api/comptes/moi/personne-confiance/alerte → prévenir manuellement la personne de confiance
POST   /api/professionnels/inscription    → création d'un compte professionnel (EN_ATTENTE)
GET    /api/professionnels/valides        → liste publique des pros validés
GET    /api/professionnels                → liste admin avec filtre statut et recherche
PATCH  /api/professionnels/moi            → le professionnel complète sa fiche
GET    /api/professionnels/{id}           → profil d'un professionnel
PATCH  /api/professionnels/{id}           → validation/refus par un admin
GET    /api/administration/vue-ensemble   → tableau de bord admin (actions en attente)
POST   /api/administration/signalements/{id}/suivi → marquer un signalement comme traité
```

**Permissions :**

```python
EstUtilisateur       # type_compte == 'utilisateur'
EstProfessionnelValide  # type_compte == 'professionnel' ET statut == VALIDE
EstAdministrateur    # type_compte == 'administrateur'
```

Ces trois classes sont réutilisées dans toutes les apps. Elles ne testent qu'une seule chose, ce qui les rend faciles à composer avec `|` (ex. `EstUtilisateur | EstProfessionnelValide`).

**Protection contre la force brute (`protection_connexion.py`) :**
- La vue `LoginView` utilise `LimitationTentativesConnexionMixin`
- Compteur par email et par IP stocké dans le cache PostgreSQL
- Blocage après `CONNEXION_TENTATIVES_MAX` (défaut 5) échecs
- Durée du blocage : `CONNEXION_BLOCAGE_MINUTES` (défaut 15 min)
- Renvoie HTTP 429 avec un message lisible

### 4.5 App `suivi`

**Modèles :**

| Modèle | Description |
|---|---|
| `SuiviHumeur` | Une entrée par jour par utilisateur (contrainte unique). Score d'humeur (TRES_MAL → TRES_BIEN), note libre, étiquettes (ex. "Travail,Sommeil"). |
| `QuestionEvaluation` | Questions d'auto-évaluation stockées en base (modifiables depuis l'admin sans redéployer). Liées à un type : STRESS, ANXIETE, FATIGUE. |
| `OptionReponse` | Options d'une question (valeur 0 à 4). Contrainte CHECK en base. |
| `AutoEvaluation` | Résultat d'un test : score sur 100 (arrondi). |

**Endpoints :**

```
GET/POST /api/suivi-humeur            → journal d'humeur (GET ?periode=7j, 30j…)
GET      /api/auto-evaluations/questions/{type} → questions d'un test
GET/POST /api/auto-evaluations        → historique et soumission d'un nouveau test
```

**Calcul du score (`services.py`) :**

```python
score = round((sum(valeurs) / sum(valeurs_max)) * 100)
# Ramené sur 100 depuis les valeurs réelles de chaque option,
# pour que l'ajout de questions ne fausse jamais le pourcentage.
```

Interprétation : ≤33 = faible, 33-66 = modéré, >66 = élevé. Au-delà de 33, des professionnels sont suggérés.

**Profil de tendance (`profil_tendance.py`) :**

Ce module produit une liste de mots-clés anonymes décrivant la tendance récente d'un utilisateur (ex. `["humeur en baisse sur 7 jours", "journal irrégulier", "niveau de stress modéré au dernier test"]`).

Ce profil est transmis au chatbot **uniquement si l'utilisateur y a consenti** (préférence `personnalisation_chatbot`). Il ne contient jamais de données brutes : ni texte du journal, ni réponses aux tests, ni identité.

### 4.6 App `chatbot`

**Modèles :**

| Modèle | Description |
|---|---|
| `ConversationChatbot` | Une conversation par session. Liée à un utilisateur (null = conversation anonyme). Conservée seulement si `consentement_conservation = True`. |
| `MessageChatbot` | Message d'une conversation : contenu, type (UTILISATEUR/BOT), source de la réponse (REGLE/RAG/GENERATION), flag d'urgence, ressource suggérée. |
| `SignalementRisque` | Situation grave signalée à l'équipe Sen Suivi. Jamais le contenu des messages — seulement la nature, l'heure, et si la personne de confiance a été prévenue. |

**Pipeline d'un message (`views.py` > `ChatbotMessageView`) :**

```
POST /api/chatbot/message
  ↓
1. Validation de l'entrée (message, historique, consentement, conversation_id)
2. Appel au microservice IA : services.traiter_message()
   → HTTP POST http://ai-service:8001/message
3. Si MicroserviceIAIndisponible → réponse de secours avec numéros d'urgence
4. Conservation de l'échange si consentement et utilisateur connecté
5. Orientation :
   - urgence → émettre_jeton() + alerter personne de confiance + signaler l'équipe
   - orientation_professionnel → suggerer() (algorithme d'orientation)
6. Ajout du jeton_vocal (signé) à la réponse
```

**Chatbot vocal (`ChatbotVocalView`) :**

L'audio ne touche jamais le disque. Le handler `AudioEnMemoireUploadHandler` surcharge le comportement Django par défaut (qui écrit sur disque au-delà de 2,5 Mo). Une fois transcrit par le microservice IA, le texte passe exactement dans le même pipeline que n'importe quel message tapé.

**Jeton vocal (`vocal.py`) :**

Seule une réponse produite par le chatbot peut être lue à voix haute. Un jeton signé (`django.core.signing.TimestampSigner`) est remis avec chaque réponse et vérifié avant la synthèse. Durée de validité : 1 heure. Si quelqu'un essaie de faire lire un texte arbitraire au bot, la requête est rejetée (403).

**Endpoints :**

```
POST   /api/chatbot/message           → message texte (AllowAny)
POST   /api/chatbot/message-vocal     → message vocal (AllowAny)
POST   /api/chatbot/reponse-vocale    → synthèse vocale d'une réponse validée (AllowAny)
GET    /api/chatbot/conversations     → historique conservé (EstUtilisateur)
POST   /api/chatbot/conversations     → enregistrer une conversation (consentement a posteriori)
GET    /api/chatbot/conversations/{id} → messages d'une conversation
DELETE /api/chatbot/conversations/{id} → droit à l'effacement
```

### 4.7 App `forum`

**Modèles :**

| Modèle | Description |
|---|---|
| `PublicationForum` | Titre, contenu, thématique (5 valeurs), statut de modération (EN_ATTENTE → VISIBLE/BLOQUE/MASQUE/SUPPRIME). |
| `CommentaireForum` | Réponse à une publication, même cycle de modération. |
| `ModerationMessage` | Trace complète de chaque décision : décision automatique, catégorie, gravité, extrait, niveau (REGLES/MODELE/REPLI), message à l'auteur, décision humaine, contestation. |

**Cycle de modération a priori :**

```
POST publication/commentaire
  ↓
Statut → EN_ATTENTE (invisible, l'auteur voit "en vérification")
  ↓
moderation.lancer(objet) → thread en arrière-plan
  ↓
Appel au microservice IA : POST http://ai-service:8001/moderer
  ↓
Décision appliquée :
  PUBLIER            → VISIBLE
  PUBLIER_ACCOMPAGNER → VISIBLE + notification à l'auteur + file admin
  BLOQUER            → BLOQUE + message pédagogique à l'auteur
  BLOQUER_PRIORITAIRE → BLOQUE + file admin prioritaire
  BLOQUER_SILENCIEUX  → BLOQUE sans message (spam)
  ATTENTE_HUMAINE     → reste EN_ATTENTE + file admin
```

**Règles éthiques du forum :**
- Une personne en détresse n'est jamais bloquée (catégorie DETRESSE → PUBLIER_ACCOMPAGNER).
- Les messages de détresse ne comptent jamais comme des infractions.
- Une décision automatique peut toujours être contestée (droit de réexamen).
- Un administrateur a toujours le dernier mot.
- Au-delà de 3 infractions en 30 jours → suspension de 7 jours (paramétrable).

**Endpoints :**

```
GET/POST   /api/forum/publications               → liste (VISIBLE seulement) et création
GET        /api/forum/publications/{id}           → détail avec commentaires
POST       /api/forum/publications/{id}/commentaires → commenter
GET        /api/forum/mes-messages               → suivi par l'auteur (30 derniers jours)
POST       /api/forum/mes-messages/{type}/{id}/contester → demande de réexamen
GET        /api/forum/moderation/file            → file des admin (doutes, détresses, contestations)
POST       /api/forum/moderation/file/{id}        → décision d'un admin (publier/bloquer/classer)
GET        /api/forum/moderation/statistiques     → taux de blocage et faux positifs (30j)
GET/PATCH  /api/forum/moderation/publications     → liste et modération manuelle
GET/PATCH  /api/forum/moderation/commentaires     → idem pour les commentaires
```

### 4.8 App `orientation`

**Algorithme de suggestion (`services.py`) :**

Un algorithme **déterministe**, jamais un LLM. Les critères sont appliqués dans cet ordre (le suivant ne sert qu'à départager les ex æquo) :

1. **Adéquation** — correspondance entre les besoins de la personne et la spécialité/domaines du pro (jusqu'à 3 × poids selon le rang du besoin).
2. **Langue commune** — langue détectée dans les messages (dont le wolof, détecté par marqueurs).
3. **Proximité** — même ville.
4. **Disponibilité** — `accepte_demandes = True`.
5. **Équité** — le moins sollicité des 30 derniers jours passe devant.

Les besoins sont inférés depuis : les messages de l'utilisateur, ses derniers tests (si score modéré/élevé), les thématiques des ressources que Titou lui a proposées.

**Modèle `AccesMiseEnRelation` :**

Après l'offre de lancement, l'accès à la mise en relation devient payant (mobile money). L'offre est configurable :
- `OFFRE_MODE=globale` : même date de fin pour tous (`OFFRE_DATE_FIN`)
- `OFFRE_MODE=individuelle` : `OFFRE_DUREE_JOURS` à partir de l'inscription de chacun

**Règle éthique absolue :** une personne en détresse (jeton d'urgence valide dans l'en-tête `X-Jeton-Urgence`) ne voit jamais de compteur, de verrou ni de tarif.

**Jeton d'urgence (`urgence.py`) :**

```python
def emettre_jeton(utilisateur) -> str:
    return signing.TimestampSigner(salt='sen-suivi.urgence').sign(str(utilisateur.pk))
```
Le jeton est signé avec la `SECRET_KEY` Django, lié au compte, et expire après `URGENCE_JETON_HEURES` (défaut 24h). Rien n'est enregistré côté serveur : la détresse d'une personne n'est jamais stockée.

**Endpoints :**

```
GET  /api/orientation/suggestion     → suggestion + liste complète des pros
GET  /api/acces/etat                 → état de l'offre (jours restants, verrou, tarif)
POST /api/acces/paiement             → initier un paiement mobile money (prestataire à brancher)
```

### 4.9 App `relations`

**Modèles :**

| Modèle | Description |
|---|---|
| `DemandeContact` | Demande d'un utilisateur vers un professionnel. Statuts : EN_ATTENTE → ACCEPTEE / REFUSEE. Méthodes `accepter()` et `refuser()` qui notifient et enregistrent la date de réponse. |
| `MessageRelation` | Message privé dans une demande acceptée. Champ `lu_le` pour les indicateurs de non-lu. Limité à 2000 caractères. |

**Règles :**
- La messagerie ne s'ouvre qu'une fois la demande ACCEPTEE.
- Aucun des deux ne partage son email ou son téléphone : tout passe dans Sen Suivi.
- L'administration ne peut pas lire les messages depuis l'interface.
- Une seule notification par lot de messages non lus (pas de spam).

**Endpoints :**

```
GET/POST /api/demandes-contact              → liste et création (POST = utilisateur, GET = les deux)
PATCH    /api/demandes-contact/{id}         → accepter ou refuser (professionnel)
GET/POST /api/demandes-contact/{id}/messages → messagerie privée
```

### 4.10 App `ressources`

**Modèles :**

| Modèle | Description |
|---|---|
| `Ressource` | Titre, type (ARTICLE/EXERCICE/PODCAST), contenu, thématique, durée de lecture, date de publication. |
| `Favori` | Association utilisateur ↔ ressource, unique. |
| `LieuDetente` | Lieu de détente au Sénégal avec coordonnées GPS (latitude/longitude), catégorie, accès libre. |

**Commande de réindexation :**

```bash
python manage.py reindexer_ressources
# Envoie toutes les ressources au microservice IA (POST /reindexer)
# pour reconstruire l'index ChromaDB après ajout ou modification.
```

**Endpoints :**

```
GET         /api/ressources                → liste avec filtres (type, thematique, q)
GET         /api/ressources/{id}           → détail d'une ressource
POST/DELETE /api/favoris                   → ajouter/retirer un favori
GET         /api/favoris                   → mes favoris
GET         /api/lieux                     → liste des lieux
GET         /api/lieux/{id}                → détail d'un lieu
```

### 4.11 App `notifications`

**Architecture (modèle abstrait) :**

```python
class Notification(models.Model):  # abstract = True
    destinataire, contenu, date_envoi, statut
    
class NotificationEmail(Notification):  # table concrète
    adresse_email, objet
    
class NotificationPush(Notification):   # table concrète
    device_token
```

Fidèle au diagramme de classes : `Notification` reste réellement abstraite.

**Service principal (`services.py`) :**

```python
def notifier(compte, objet, contenu, preference=None):
    # 1. Crée la NotificationEmail (visible dans la cloche de l'app)
    # 2. Si EMAIL_NOTIFICATIONS et préférence non désactivée :
    #    → envoyer_en_arriere_plan() (thread daemon, la page n'attend pas)
    
def declencher_workflow(nom, donnees=None):
    # POST http://n8n:5678/webhook/{nom}
    # Best-effort : si n8n est arrêté, ça ne bloque jamais l'action
```

**Envoi d'email (`courriel.py`) :**
- Utilise `django.core.mail.send_mail` avec le serveur SMTP du `.env`.
- Si `EMAIL_HOST` est vide : mode console (les emails s'affichent dans les logs Django).
- `EMAIL_ASYNCHRONE=True` (défaut) : l'envoi se fait dans un thread daemon. La page ne attend jamais le serveur SMTP.
- Jamais l'adresse ni le contenu dans les logs en cas d'erreur : seulement le type d'exception.
- Une signature pied-de-page est ajoutée à tous les emails (numéros d'urgence).

**Endpoints internes (appelés par n8n uniquement) :**

```
GET  /api/interne/utilisateurs-inactifs   → utilisateurs sans journal depuis N jours
GET  /api/interne/utilisateurs-a-retester → utilisateurs sans test depuis N jours
GET  /api/interne/administrateurs         → liste des admins
POST /api/interne/notifications-email     → créer une notification programmatiquement
```

Protégés par l'en-tête `X-Cle-Interne` = `N8N_API_KEY`. Pas de JWT, pas de compte : une clé partagée que l'équipe génère elle-même.

**Endpoints utilisateurs :**

```
GET   /api/notifications           → mes notifications (non lues en premier)
PATCH /api/notifications/{id}/lu   → marquer comme lue
```

---

## 5. Service IA — FastAPI (ai-service)

### 5.1 Choix techniques et pourquoi

| Technologie | Version | Pourquoi ce choix |
|---|---|---|
| **FastAPI** | 0.115 | Framework Python asynchrone, documentation automatique (OpenAPI), validation des entrées/sorties par Pydantic. Idéal pour un microservice orienté I/O (appels LLM, embeddings). |
| **Pydantic** | 2.10 | Validation stricte des données entrantes et sortantes. Chaque endpoint a un schéma exact : aucune donnée inattendue ne passe. |
| **ChromaDB** | 0.5 | Base de données vectorielle légère, intégrable directement dans le processus Python (pas de service séparé). Stockage persistant sur disque (`chroma_data`). Espace cosinus pour la similarité. |
| **sentence-transformers** | 3.3 | Modèle d'embeddings multilingue (`paraphrase-multilingual-MiniLM-L12-v2`). Le modèle par défaut de ChromaDB ne comprend que l'anglais. Ce modèle gère le français, le wolof et les mélanges. |
| **torch (CPU)** | 2.5 | Version CPU de PyTorch (bien plus légère que la version GPU, inutile pour les embeddings de phrases courtes). |
| **httpx** | 0.28 | Appels aux LLM externes (Groq, Mistral, OpenAI, etc.). Compatible avec le mode thread + pool de workers. |
| **uvicorn** | 0.34 | Serveur ASGI rapide pour FastAPI. Mode standard (avec boucle d'événements). |

### 5.2 Pipeline complet d'un message (`main.py`)

```
POST /message
  │
  ├─ Nettoyage de l'entrée (contrôles, espaces)
  │
  ├─ Crise en cours ? (derniers messages de l'historique)
  │   └─ Oui → _repondre_en_crise() → réponse courte + urgence=True
  │
  └─ Non → _repondre()
        │
        ├─ NIVEAU 0 : detecter_detresse(message)
        │   └─ Oui → REPONSE_URGENCE, urgence=True, stop
        │
        ├─ danger_autrui(message) → REPONSE_DANGER_AUTRUI, stop
        ├─ violences(message)    → REPONSE_VIOLENCES, stop
        │
        ├─ NIVEAU 1 : classifier(message)
        │   └─ intention reconnue + pas de LLM → réponse prédéfinie, stop
        │
        ├─ NIVEAU 2a : rechercher_plusieurs(message) → ressources RAG
        │
        └─ NIVEAU 2b : si LLM disponible
              ├─ generer() → mode ressources
              │   └─ Rejeté → ecouter() → mode écoute
              └─ Si toujours None → repli en cascade
                  (réponse prédéfinie → ressource RAG → REPONSE_REPLI)
```

### 5.3 Niveau 0 — Détection de détresse

**Fichier :** `app/detecteur_detresse.py`

Toujours exécuté EN PREMIER, avant tout le reste. Basé sur une liste de mots-clés (`config/mots_cles_detresse.py`) normalisés (sans accents, minuscules).

```python
def detecter_detresse(message: str) -> bool:
    normalise = _normaliser(message)  # sans accents, minuscules
    return any(_normaliser(mot_cle) in normalise for mot_cle in MOTS_CLES_DETRESSE)
```

Si déclenché → `REPONSE_URGENCE` avec les numéros sénégalais (800 805 805, 1515, 18) et l'Hôpital de Fann. Le LLM n'est jamais appelé pour une réponse d'urgence.

### 5.4 Niveau 1 — Classification d'intention

**Fichier :** `app/classificateur_intention.py`

Approche par **mots-clés pondérés** (pas un modèle entraîné). Délibérément simple, déterministe et explicable.

```python
_MOTS_CLES = {
    'STRESS': [('je suis stresse', 0.8), ('stress', 0.4), ...],
    'FATIGUE': [('je dors mal', 0.8), ('fatigue', 0.4), ...],
    'BESOIN_ECOUTE': [...],
    'QUESTION_RESSOURCE': [...],
    'URGENCE': [...],
}
# Score = somme des poids, plafonné à 1.0
# Seuil de confiance : 0.70 (configurable via .env)
```

Chaque intention reconnue avec confiance a une réponse validée prédéfinie (`REPONSE_PAR_INTENTION`). Si un LLM est disponible, cette réponse devient le **filet de sécurité** plutôt que la réponse principale.

### 5.5 Niveau 2a — Moteur RAG (ChromaDB)

**Fichier :** `app/moteur_rag.py`

RAG = Retrieval-Augmented Generation. Les ressources de la bibliothèque (articles, exercices, podcasts) sont vectorisées et stockées dans ChromaDB. Une recherche par similarité cosinus trouve les plus proches du message de l'utilisateur.

**Pourquoi ChromaDB :**
- Base vectorielle intégrée dans le processus Python (pas de service séparé à déployer).
- Stockage persistant sur volume Docker (`chroma_data`).
- Espace cosinus natif (la distance renvoyée est directement comparable au seuil).
- Une collection par modèle d'embeddings (nom incluant l'empreinte SHA1 du modèle) : changer de modèle ne mélange jamais les vecteurs.

**Seuil de similarité :** `SEUIL_SIMILARITE_RAG` (défaut 0.40). En dessous du seuil, la ressource n'est pas retournée.

**Réindexation :** déclenchée par `POST /reindexer` (workflow n8n) ou `python manage.py reindexer_ressources`. Elle synchronise l'index avec la liste complète des ressources Django : les ressources supprimées disparaissent aussi de l'index.

**Contexte conversationnel :** si le message seul est trop court (« et alors ? »), les 2 derniers messages de l'utilisateur sont ajoutés à la requête de recherche pour retrouver le sujet.

### 5.6 Niveau 2b — Génération encadrée (LLM)

**Fichier :** `app/generateur_reponse.py`

**Deux modes :**

- **Mode ressources** (`generer()`) : le LLM répond en s'appuyant UNIQUEMENT sur les ressources trouvées par le RAG. Il n'invente rien. Prompt `PROMPT_RESSOURCES` : 4 phrases max, dans l'ordre (reformulation → normalisation → conseil tiré de la ressource → question ou proposition).

- **Mode écoute** (`ecouter()`) : aucune ressource ne correspond (salutation, besoin de parler). Le LLM accueille, reformule, pose une question. Prompt `PROMPT_ECOUTE` : 3 phrases max. Aucun conseil.

**Cascade de fournisseurs :**
- Liste dans `LLM_FOURNISSEURS` (ex. `LLM,MISTRAL`).
- Si le premier ne répond pas → le suivant est essayé.
- Chaque fournisseur peut avoir un modèle principal et un modèle de secours.
- Budget de temps partagé : `LLM_DELAI_TOTAL_SECONDES` (défaut 20s). Au-delà → repli.

**Appels dans un ThreadPoolExecutor :**
La résolution DNS peut bloquer le thread principal même avec `httpx`. Tous les appels aux LLM se font dans un pool de 8 workers. L'attente est bornée avec `future.result(timeout=delai + 0.5)`.

**Profil de tendance :**
Si l'utilisateur a consenti, des mots-clés décrivant sa tendance récente (ex. "humeur en baisse sur 7 jours") sont transmis au LLM via un message système. Le LLM ne doit s'en servir que pour son ton, jamais pour le contenu.

**Caractéristiques du prompt système (`_CADRE`) :**
- Vouvoiement obligatoire
- Aucune liste à puces, aucun plan
- Formules interdites : "je comprends", "courage", "restez positif"
- Aucun vocabulaire clinique
- 3 numéros précis pour leurs usages précis (800 805 805, 1515, 18)
- Orientation vers les professionnels de l'annuaire Sen Suivi

### 5.7 Validateur de réponse

**Fichier :** `app/validateur_reponse.py`

Chaque réponse générée par le LLM passe par ce validateur **avant d'être montrée à l'utilisateur**. Si elle échoue → rejet, passage au modèle suivant ou au repli.

Règles vérifiées :
- Réponse non vide et achevée (se termine par une ponctuation finale)
- Aucune formule creuse (`FORMULES_CREUSES`)
- Aucun terme clinique (`TERMES_CLINIQUES`)
- Aucune promesse interdite (`PROMESSES_INTERDITES`)
- Aucun sujet payant (`TERMES_PAYANTS`)
- Aucun conseil interdit (`CONSEILS_INTERDITS`)
- Pas de tutoiement
- Pas de liste à puces
- Maximum de phrases respecté (4 en mode ressources, 3 en écoute)
- Maximum d'une question
- Numéros de téléphone : seulement les 3 autorisés
- Pas de répétition d'une réponse précédente (similarité Jaccard)

La raison du rejet est journalisée, jamais le message de l'utilisateur.

### 5.8 Modération du forum

**Fichier :** `app/moderateur_forum.py`

Même structure en niveaux que le chatbot :

**Niveau 0 (règles)** — sans modèle, immédiat :
- Email → DONNEES_PERSONNELLES
- Numéro de téléphone → DONNEES_PERSONNELLES
- Compte @réseau social → DONNEES_PERSONNELLES
- Lien externe ou spam → SPAM
- Insultes fortes (liste `INSULTES_FORTES`) → INSULTE
- Mots blessants ciblés avec marqueur de ciblage (`tu es`, `espèce de`…) → INSULTE

**Normalisation robuste** : chiffres-lettres (`0=o`, `1=i`, `3=e`…), lettres isolées séparées par des points (`s.a.l.o.p.e`), lettres répétées (`sooooot`), tout est normalisé pour déjouer les contournements.

**Niveau 1 (modèle)** — politique JSON stricte :
- Le modèle reçoit la politique de modération (9 catégories, avec exemples) et répond en JSON.
- Principe absolu : on sanctionne l'AGRESSION, jamais la SOUFFRANCE.
- Un récit de violence SUBIE est CONFORME.

**Niveau 2 (décision)** :

| Catégorie | Décision | Pourquoi |
|---|---|---|
| CONFORME | PUBLIER | Rien de problématique |
| DETRESSE | PUBLIER_ACCOMPAGNER | Jamais bloquer quelqu'un qui souffre |
| SPAM | BLOQUER_SILENCIEUX | Pas besoin d'expliquer à un spammeur |
| HARCELEMENT/HAINE/AGRESSION_SEXUELLE | BLOQUER_PRIORITAIRE | File admin en urgence |
| Insulte gravité ≥3 | BLOQUER_PRIORITAIRE | File admin en urgence |
| Insulte légère | BLOQUER | Message pédagogique |
| Modèle indisponible | ATTENTE_HUMAINE | On ne publie jamais sans contrôle |

**Cache LRU :** les décisions sont mises en cache (condensat SHA256 du texte normalisé). Taille configurable (`MODERATION_CACHE_TAILLE`, défaut 2000). Un message identique n'est analysé qu'une seule fois.

### 5.9 Chatbot vocal

**Fichier :** `app/transcription.py`, `app/synthese_vocale.py`

**Transcription :**
- `POST /transcrire` reçoit les octets audio dans le corps de la requête (jamais de fichier sur disque).
- Modèle Whisper (`TRANSCRIPTION_MODELE`, défaut `whisper-large-v3`) via l'API compatible OpenAI.
- Si le texte transcrit est trop court ou non compréhensible (`comprehensible()`) → réponse spéciale sans passer par le pipeline principal.

**Synthèse vocale :**
- `POST /reponse-vocale` renvoie un MP3.
- Tout fournisseur compatible OpenAI `/audio/speech` fonctionne.
- Si `SYNTHESE_URL_BASE` est vide → 503 (le frontend utilise la voix du navigateur, gratuite).

---

## 6. Service Frontend — Angular

### 6.1 Choix techniques et pourquoi

| Technologie | Version | Pourquoi ce choix |
|---|---|---|
| **Angular** | 22.x | Framework complet : routing, formulaires réactifs, DI, SSR, signaux. Structure imposée (modules ou standalone components) qui convient à une équipe. |
| **Standalone components** | — | Plus légers que les NgModules. Pas d'AppModule. Chaque composant déclare ses dépendances. |
| **Signaux Angular** | — | Réactivité fine sans Zone.js. `signal()`, `computed()`, `effect()`. Utilisés dans `AuthService` pour `estConnecte`, `typeCompte`, etc. |
| **Lazy loading** | — | Chaque route charge son composant à la demande (`loadComponent`). Le bundle initial est minimal. |
| **@lucide/angular** | 1.47 | Icônes SVG légères et accessibles. Pas de bibliothèque d'icônes lourde. |
| **@swimlane/ngx-charts** | 25.x | Graphiques D3 adaptés à Angular. Utilisé pour les statistiques d'humeur. |
| **leaflet** | 1.9 | Carte interactive pour les lieux de détente. Open source, sans clé API. |
| **Vitest** | 4.x | Remplace Karma/Jasmine. Plus rapide, compatible avec l'écosystème Vite. |
| **TypeScript** | 6.x | Typage strict. |

### 6.2 Structure et routing

```
src/app/
├── app.component.ts      ← racine (RouterOutlet + FenetreChatComponent)
├── app.routes.ts         ← toutes les routes
├── core/
│   ├── config/           ← API_BASE_URL, listes d'images
│   ├── guards/           ← estConnecteGuard, typeCompteGuard, ouvrirConversation
│   ├── interceptors/     ← jwtInterceptor
│   ├── models/           ← interfaces TypeScript par domaine
│   └── services/         ← AuthService, ChatbotService, ForumService…
├── features/             ← pages par fonctionnalité
│   ├── accueil/
│   ├── auth/             ← connexion, inscription, inscription-pro, mdp-oublié
│   ├── chatbot/
│   ├── forum/
│   ├── journal/
│   ├── admin/            ← vue-ensemble, professionnels, forum, ressources
│   ├── pro/              ← tableau de bord professionnel
│   └── …
└── shared/               ← composants réutilisables
    ├── layout-app/       ← shell avec navigation (utilisateur connecté)
    ├── layout-pro/       ← shell professionnel
    ├── layout-admin/     ← shell admin
    ├── layout-public/    ← shell page publique
    ├── fenetre-chat/     ← flottante, persiste entre les routes
    ├── mood-chart/       ← graphique d'humeur
    ├── modal-urgence/    ← affichée lors d'une détresse détectée
    └── …
```

**Layouts imbriqués :** la fenêtre de chat (`FenetreChatComponent`) est définie dans `AppComponent` et vit en dehors du router outlet. Elle reste ouverte quand l'utilisateur navigue.

**Routes protégées :**

| Guard | Ce qu'il vérifie |
|---|---|
| `estConnecteGuard` | Utilisateur authentifié, sinon → `/connexion` |
| `typeCompteGuard('utilisateur')` | Type de compte exact |
| `typeCompteGuard('professionnel')` | Type de compte exact |
| `typeCompteGuard('administrateur')` | Type de compte exact |
| `ouvrirConversation` | Ouvre la fenêtre de chat par-dessus la page en cours (ne charge pas de composant) |

### 6.3 Authentification côté client

**Fichier :** `core/services/auth.service.ts`

```typescript
@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly claims = signal<ClaimsJeton | null>(lireJetonValide());
  
  readonly estConnecte = computed(() => this.claims() !== null);
  readonly typeCompte  = computed(() => this.claims()?.type_compte ?? null);
  readonly nom         = computed(() => this.claims()?.nom ?? null);
  readonly prenom      = computed(() => this.claims()?.prenom ?? null);
  readonly identifiant = computed(() => this.claims()?.user_id ?? null);
}
```

- Les tokens sont stockés dans `localStorage` sous les clés `ss_acces` et `ss_rafraichissement`.
- Au démarrage, le token d'accès est lu et décodé. S'il est expiré, il est ignoré.
- `jetonAccesValide()` : si le token expire dans moins de 10 secondes → renouvellement automatique avec le refresh token. Une seule promesse de renouvellement à la fois (mutex par promesse).

### 6.4 Intercepteur JWT

**Fichier :** `core/interceptors/jwt.interceptor.ts`

Appliqué à toutes les requêtes HTTP sauf `/auth/login` et `/auth/refresh`.

```typescript
// 1. Récupérer le jeton d'accès valide (renouvellement si nécessaire)
// 2. Ajouter Authorization: Bearer <token>
// 3. Si X-Jeton-Urgence présent (détresse) → ajouter l'en-tête
// 4. En cas de 401 → tenter un renouvellement forcé, une seule fois
// 5. Si 401 à nouveau → déconnecter + rediriger vers /connexion si espace privé
```

Le jeton d'urgence (`UrgenceService`) est lu et ajouté automatiquement à chaque requête si présent.

### 6.5 Services principaux

| Service | Responsabilité |
|---|---|
| `AuthService` | Connexion, inscription, déconnexion, renouvellement token, signaux réactifs |
| `ChatbotService` | Envoyer un message texte ou vocal, lire à voix haute, gérer l'historique conservé |
| `ForumService` | Publications, commentaires, mes-messages, contestation |
| `SuiviHumeurService` | Journal d'humeur (lecture et écriture) |
| `AutoEvaluationService` | Questions et soumission des tests |
| `ConversationService` | Messagerie privée avec un professionnel |
| `DemandesService` | Liste et gestion des demandes de contact |
| `NotificationsService` | Panneau de notifications |
| `ThemeService` | Thème clair/sombre (préférence stockée localement) |
| `UrgenceService` | Stocker et exposer le jeton d'urgence reçu du chatbot |
| `LectureVocaleService` | Lecture à voix haute des réponses Titou |
| `EnregistreurVocalService` | Capture micro pour le chatbot vocal |
| `FicheProService` | Profil d'un professionnel |
| `AccesService` | État de l'offre de lancement |
| `PersonneConfianceService` | Gestion de la personne de confiance |

---

## 7. Service d'automatisation — n8n

### 7.1 Pourquoi n8n

n8n est un outil d'automatisation open source, auto-hébergé, avec interface visuelle. Il joue le rôle d'orchestrateur des tâches périodiques et des webhooks, sans ajouter de Celery, de Beat scheduler, ou d'un autre système de queue de tâches à maintenir côté Django.

- Django se concentre sur la logique métier.
- n8n gère : les planifications, les webhooks, l'appel aux endpoints internes Django, et l'envoi de notifications.
- Les workflows sont exportés en JSON dans `./automations/` et versionnés.

### 7.2 Les cinq workflows

#### `rappel-inactivite.json` — Rappel journal d'humeur

```
Déclencheur : chaque jour à 9h
→ GET /api/interne/utilisateurs-inactifs  (X-Cle-Interne)
→ Pour chaque utilisateur :
   POST /api/interne/notifications-email
```

Django retourne la liste des utilisateurs sans entrée depuis `RAPPEL_JOURNAL_JOURS` (défaut 3) jours, qui n'ont pas désactivé ce rappel et qui n'ont pas déjà reçu un rappel dans les `RAPPEL_FREQUENCE_MAX_JOURS` (défaut 7) jours.

#### `rappel-auto-evaluation.json` — Rappel test mensuel

Même structure, mais appelle `/api/interne/utilisateurs-a-retester` (dernier test > `RAPPEL_TEST_JOURS` jours).

#### `nouvelle-demande.json` — Notification nouvelle mise en relation

```
Déclencheur : webhook POST /webhook/nouvelle-demande
  (appelé par Django lors de la création d'une DemandeContact)
→ POST /api/interne/notifications-email
   (notifie le professionnel, avec la préférence 'nouvelle_demande')
```

#### `nouveau-professionnel.json` — Alerte nouvelle inscription pro

```
Déclencheur : webhook POST /webhook/nouveau-professionnel
  (appelé par Django lors de l'inscription d'un professionnel)
→ Notifie les administrateurs
```

#### `indexation-rag.json` — Réindexation des ressources

```
Déclencheur : webhook POST /webhook/indexation-rag
  (déclenché manuellement ou après modification de ressources)
→ GET /api/ressources  (liste complète)
→ POST http://ai-service:8001/reindexer
```

### 7.3 Endpoints internes Django

Tous sous `/api/interne/`, protégés par `X-Cle-Interne: <N8N_API_KEY>`.

```python
class EstAutomatisation(BasePermission):
    def has_permission(self, request, view):
        cle = settings.N8N_API_KEY
        return bool(cle) and request.headers.get('X-Cle-Interne') == cle
```

La clé est générée par l'équipe (`python3 -c "import secrets; print(secrets.token_urlsafe(32))"`). Ce n'est la clé d'aucun service externe.

---

## 8. Communications entre services

### Diagramme complet des communications

```
Browser/App (Angular)
  │  HTTPS (prod) / HTTP (dev)
  │  JWT dans Authorization: Bearer
  │  X-Jeton-Urgence si détresse
  ▼
Backend Django :8000
  │
  ├─────► ai-service :8001 (réseau Docker interne)
  │       HTTP POST /message        → traitement chatbot
  │       HTTP POST /message-vocal  → (via ChatbotVocalView → transcrire)
  │       HTTP POST /moderer        → modération forum
  │       HTTP POST /reindexer      → réindexation RAG
  │       HTTP POST /transcrire     → transcription audio
  │       HTTP POST /reponse-vocale → synthèse vocale
  │
  ├─────► n8n :5678 (réseau Docker interne)
  │       HTTP POST /webhook/nouvelle-demande
  │       HTTP POST /webhook/nouveau-professionnel
  │       HTTP POST /webhook/indexation-rag
  │       (best-effort : échec silencieux)
  │
  └─────► SMTP externe (Gmail, Brevo…)
          Notifications, réinitialisation mdp, personne de confiance

n8n :5678
  ├─────► Backend :8000 (réseau Docker interne)
  │       GET  /api/interne/utilisateurs-inactifs
  │       GET  /api/interne/utilisateurs-a-retester
  │       GET  /api/interne/administrateurs
  │       POST /api/interne/notifications-email
  │       (clé X-Cle-Interne)
  │
  └─────► ai-service :8001 (via workflow indexation)
          POST /reindexer

ai-service :8001
  └─────► LLM externes (Groq, Mistral, OpenAI, OpenRouter…)
          HTTPS POST /chat/completions
          HTTPS POST /audio/transcriptions
          HTTPS POST /audio/speech
          (cascade de fournisseurs, LLM_FOURNISSEURS)
```

### Règles de communication

1. **Django → ai-service** : synchrone pour le chatbot (attente bornée par `AI_SERVICE_DELAI_SECONDES`). Asynchrone (thread) pour la modération du forum.
2. **Django → n8n** : toujours best-effort. Un webhook n8n qui échoue ne bloque jamais l'action de l'utilisateur.
3. **n8n → Django** : requêtes HTTP classiques avec la clé interne.
4. **ai-service → LLM** : cascade avec budget de temps partagé (`LLM_DELAI_TOTAL_SECONDES`). Chaque appel dans un thread (ThreadPoolExecutor) pour éviter que la résolution DNS bloque le processus.
5. **Frontend → Backend** : toutes les requêtes passent par l'intercepteur JWT. Les routes publiques (`/auth/login`, chatbot) n'ont pas besoin de token.

---

## 9. Sécurité

### Authentification et autorisation

- **JWT** (access token 60 min, refresh token 7 jours). Le type de compte est un claim dans le token.
- Les tokens sont stockés dans `localStorage` (compromis choisi pour la simplicité, acceptable pour ce contexte). En production à fort enjeu, `httpOnly cookies` seraient préférables.
- **Permissions DRF** granulaires : `EstUtilisateur`, `EstProfessionnelValide`, `EstAdministrateur`, composables.
- Les professionnels en attente ou refusés ne peuvent pas se connecter (vérification dans `LoginSerializer`).

### Protection contre la force brute

- Compteur par email ET par IP, stocké dans le cache PostgreSQL.
- Blocage après `CONNEXION_TENTATIVES_MAX` (défaut 5) avec retour HTTP 429.
- Durée configurable (`CONNEXION_BLOCAGE_MINUTES`).

### Mots de passe

6 validateurs Django appliqués en cascade :
1. Similitude avec les attributs du compte
2. Longueur minimale (8 caractères)
3. Liste de mots de passe courants (liste intégrée Django, sans service externe)
4. Numéros purs interdits
5. Complexité (3 catégories sur 4) — `ComplexiteValidator`
6. Suites évidentes (azerty, 123456…) — `SuiteEvidenteValidator`

### Réinitialisation du mot de passe

La vue `DemandeReinitialisationView` répond **toujours HTTP 200**, qu'un compte avec cet email existe ou non. Cela empêche l'énumération des comptes.

### Jeton d'urgence

Signé avec `django.core.signing.TimestampSigner` (utilise `SECRET_KEY` Django). Lié au `pk` du compte. Expire après `URGENCE_JETON_HEURES`. Rien n'est stocké côté serveur (la détresse ne doit jamais être enregistrée).

### Jeton vocal

Même mécanisme. Seul le condensat SHA256 du texte de la réponse est signé. Empêche de faire lire un texte arbitraire au bot.

### CORS

Seules les origines listées dans `CORS_ALLOWED_ORIGINS` peuvent faire des requêtes cross-origin. L'en-tête `X-Jeton-Urgence` est explicitement autorisé.

### Endpoints internes n8n

Protégés par une clé partagée `N8N_API_KEY` dans l'en-tête `X-Cle-Interne`. Jamais de JWT, jamais d'identité utilisateur côté n8n.

### Confidentialité des données

- **Logs** : jamais d'adresse email, jamais de contenu de message dans les logs. Seulement le type d'erreur.
- **Signalements** : jamais le contenu des messages, seulement la nature et l'heure.
- **Profil de tendance** : seulement des mots-clés anonymes, transmis au LLM uniquement avec consentement explicite.
- **Audio** : jamais écrit sur disque (handler `AudioEnMemoireUploadHandler`).
- **Messagerie privée** : pas accessible à l'administration via l'interface.

---

## 10. Variables d'environnement (`.env`)

Le fichier `.env.example` documente toutes les variables. Voici les groupes principaux :

### Base de données

```env
POSTGRES_DB=sensuivi
POSTGRES_USER=sensuivi
POSTGRES_PASSWORD=change_moi
POSTGRES_HOST=db
POSTGRES_PORT=5432
```

### Django

```env
DJANGO_SECRET_KEY=change_moi          # clé secrète, générer avec secrets.token_urlsafe(50)
DJANGO_DEBUG=True                      # False en production
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,backend
JWT_ACCESS_MINUTES=60
JWT_REFRESH_DAYS=7
CONNEXION_TENTATIVES_MAX=5
CONNEXION_BLOCAGE_MINUTES=15
```

### Microservice IA

```env
AI_SERVICE_URL=http://ai-service:8001
AI_SERVICE_DELAI_SECONDES=25
SEUIL_CONFIANCE_INTENTION=0.70
SEUIL_SIMILARITE_RAG=0.40
CHROMA_PERSIST_DIR=/data/chroma
EMBEDDING_MODELE=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
```

### LLM (modèle de langage)

```env
LLM_ACTIVE=true
LLM_FOURNISSEURS=LLM,MISTRAL         # cascade dans cet ordre
LLM_URL_BASE=https://api.groq.com/openai/v1
LLM_CLE_API=gsk_…
LLM_MODELE=qwen/qwen3.8-27b
LLM_MODELE_SECOURS=openai/gpt-oss-120b
LLM_EFFORT_RAISONNEMENT=none          # pour les modèles qui "réfléchissent"
LLM_DELAI_MAX_SECONDES=8
LLM_DELAI_TOTAL_SECONDES=20
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=300
LLM_HISTORIQUE_MAX=6
```

### Modération forum

```env
MODERATION_MODELE=openai/gpt-oss-safeguard-20b
MODERATION_EFFORT_RAISONNEMENT=low
MODERATION_ASYNCHRONE=true
MODERATION_SEUIL_INFRACTIONS=3
MODERATION_FENETRE_JOURS=30
MODERATION_SUSPENSION_JOURS=7
```

### Chatbot vocal

```env
TRANSCRIPTION_MODELE=whisper-large-v3
VOCAL_DUREE_MAX_SECONDES=60
VOCAL_TAILLE_MAX_MO=10
# Synthèse vocale (laisser vide = voix du navigateur)
SYNTHESE_URL_BASE=
SYNTHESE_CLE_API=
SYNTHESE_MODELE=
SYNTHESE_VOIX=
```

### E-mails

```env
EMAIL_HOST=smtp.gmail.com              # vide = mode console (logs Django)
EMAIL_PORT=587
EMAIL_USE_TLS=true
EMAIL_HOST_USER=ton.adresse@gmail.com
EMAIL_HOST_PASSWORD=mot_de_passe_d_application
DEFAULT_FROM_EMAIL=Sen Suivi <no-reply@sensuivi.sn>
EMAIL_NOTIFICATIONS=true
EMAIL_ASYNCHRONE=true                  # ne jamais bloquer la page sur l'SMTP
```

### n8n et automatisation

```env
N8N_WEBHOOK_URL=http://n8n:5678
N8N_API_KEY=change_moi                 # générer avec secrets.token_urlsafe(32)
RAPPEL_JOURNAL_JOURS=3
RAPPEL_TEST_JOURS=30
RAPPEL_FREQUENCE_MAX_JOURS=7
```

### Offre de lancement et paiement

```env
OFFRE_MODE=globale                     # ou individuelle
OFFRE_DATE_FIN=2026-11-30              # vide = offre sans fin
OFFRE_DUREE_JOURS=60
ACCES_TARIF_FCFA=2000
ACCES_DUREE_JOURS=30
URGENCE_JETON_HEURES=24
```

---

## 11. Guide de démarrage rapide

### Prérequis

- Docker Desktop ou Docker Engine + Docker Compose v2
- Git

### Installation

```bash
# 1. Cloner le projet
git clone <url_du_dépôt>
cd sen-suivi

# 2. Copier et personnaliser le .env
cp .env.example .env
# Éditer .env : changer POSTGRES_PASSWORD, DJANGO_SECRET_KEY, N8N_API_KEY
# Ajouter les clés LLM si souhaité

# 3. Construire et démarrer tous les services
docker compose up --build -d

# 4. Initialiser la base de données
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py createcachetable

# 5. (Optionnel) Créer un superutilisateur admin
docker compose exec backend python manage.py createsuperuser

# 6. (Optionnel) Charger des données de démonstration
docker compose exec backend python manage.py seed_donnees

# 7. Indexer les ressources dans ChromaDB
docker compose exec backend python manage.py reindexer_ressources
```

### Accès

| Service | URL locale |
|---|---|
| Frontend Angular | http://localhost:4200 |
| API Django (Swagger via DRF) | http://localhost:8000/api/ |
| Interface admin Django | http://localhost:8000/admin/ |
| Interface n8n | http://localhost:5678 |
| Microservice IA (docs FastAPI) | http://localhost:8001/docs |

### Importer les workflows n8n

```bash
# Dans l'interface n8n (localhost:5678) :
# Settings → Import Workflow → importer chacun des fichiers dans ./automations/

# Ou via CLI (si n8n est accessible) :
docker compose exec n8n n8n import:workflow --separate --input=/automations
```

### Commandes utiles

```bash
# Voir les logs d'un service
docker compose logs -f backend
docker compose logs -f ai-service

# Relancer un service après modification du code
docker compose restart backend

# Reconstruire un service après modification du Dockerfile
docker compose up --build -d ai-service

# Lancer les tests backend
docker compose exec backend python manage.py test

# Lancer les tests du microservice IA
docker compose exec ai-service python -m pytest

# Lancer les tests frontend
docker compose exec frontend npm run test

# Réinitialiser l'index ChromaDB (après changement de modèle d'embeddings)
docker compose exec backend python manage.py reindexer_ressources
```

### Architecture des branches Git

Le projet utilise une convention de branches organisée :

```
main          → version stable
dev           → intégration continue
feat/xxx      → nouvelles fonctionnalités
fix/xxx       → corrections
style/xxx     → ajustements visuels
```

Branches présentes dans le dépôt :
- `feat/chatbot-empathique`, `feat/chatbot-vocal`, `feat/ia-contextuelle`
- `feat/moderation-forum`, `feat/supervision-ia`
- `feat/tableau-de-bord-pro`, `feat/orientation-pro`
- `feat/aide-urgence`, `feat/securite-authentification`
- `feat/images-lieux`, `feat/courriels`, `feat/onboarding-animations`
- `fix/forum-clignotement`, `fix/message-moderation`
- `style/contrastes-clair`, `style/fiche-professionnel`, etc.

---

*Documentation générée le 6 octobre 2026 à partir du code source complet du projet Sen Suivi.*

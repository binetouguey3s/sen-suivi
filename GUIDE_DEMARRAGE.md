# Sen Suivi — Démarrer le code avec Claude Code

Guide pas à pas : initialisation du dépôt, mise en place du back-end, du front-end et du microservice IA, dépôt sur GitHub.

---

## Étape 0 — Préparer le terrain (10 minutes, sans Claude Code)

```bash
mkdir sen-suivi && cd sen-suivi
git init
mkdir -p docs/maquettes
```

Copie le fichier **CLAUDE.md** à la racine, et dézippe tes 68 écrans dans `docs/maquettes/`.

Crée ensuite le dépôt GitHub. Si tu as la CLI GitHub :

```bash
gh repo create sen-suivi --private --source=. --remote=origin
```

Sinon, crée le dépôt vide sur github.com, puis :

```bash
git remote add origin https://github.com/binetouguey3s/sen-suivi.git
```

Premier commit :

```bash
git add . && git commit -m "chore: initialise le dépôt avec le contexte projet et les maquettes"
git branch -M main && git push -u origin main
git checkout -b dev && git push -u origin dev
```

Ouvre maintenant le dossier dans VS Code et lance Claude Code dans le terminal intégré.

---

## Les trois règles d'un bon prompt Claude Code

| Règle | Pourquoi |
|---|---|
| **Une étape par prompt** | Un prompt qui demande « fais tout le backend » produit du code générique que tu ne comprendras pas et que tu ne pourras pas défendre en soutenance |
| **Demande un plan avant le code** | Termine tes prompts par « Propose-moi d'abord un plan, attends ma validation. » Tu corriges une erreur d'architecture en une phrase plutôt qu'en trente fichiers |
| **Fais-lui lire les fichiers** | « Lis CLAUDE.md », « ouvre docs/maquettes/X.png ». Claude Code ne devine pas, il lit |

Et après chaque étape validée : `git add . && git commit` puis `git push`. Un commit par étape te donne un historique lisible par le jury.

---

## Étape 1 — Squelette du monorepo

```
Lis CLAUDE.md à la racine, c'est le contexte complet du projet.

Crée le squelette du monorepo tel qu'il est décrit dans la section 3 :
les dossiers backend/, ai-service/, frontend/, un docker-compose.yml qui
orchestre postgres, backend, ai-service et frontend, un .env.example, un
.gitignore adapté à Python et Node, et un README.md qui explique comment
lancer le projet en une commande.

Ne crée pas encore de code applicatif : uniquement l'ossature, les
Dockerfile et la configuration.

Propose-moi d'abord un plan et attends ma validation.
```

---

## Étape 2 — Modèles Django

```
Lis CLAUDE.md, en particulier la section 4 sur le modèle de données.

Initialise le projet Django dans backend/ avec la configuration décrite
(PostgreSQL, Django REST Framework, JWT) et crée les applications listées
dans la section 3.

Écris ensuite les modèles de la section 4, avec les énumérations en
TextChoices, en gardant les noms français du diagramme UML. CompteUtilisateur
est un modèle utilisateur personnalisé ; Utilisateur, Professionnel et
Administrateur en héritent.

Génère les migrations et enregistre tout dans l'admin Django.

Propose-moi d'abord un plan et attends ma validation.
```

Une fois validé, demande-lui d'expliquer :

```
Explique-moi simplement, en français, comment tu as traduit l'héritage
UML de CompteUtilisateur en modèles Django, et pourquoi tu as choisi
cette approche plutôt qu'une autre. Je dois pouvoir le défendre devant
un jury.
```

---

## Étape 3 — API REST et authentification

```
Lis CLAUDE.md, section 5 sur les routes API.

Implémente les sérialiseurs, les vues et les routes de la section 5 avec
Django REST Framework.

Points d'attention :
- POST /api/chatbot/message est accessible SANS authentification
- POST /api/auth/login refuse la connexion d'un professionnel dont le
  statutValidation n'est pas VALIDE, avec un message d'erreur clair
- POST /api/auto-evaluations calcule un score de tendance puis renvoie
  les professionnels correspondants ; si aucun ne correspond, renvoie une
  liste vide et un message
- Les permissions distinguent Utilisateur, Professionnel et Administrateur

Ajoute un fichier de données de test (fixtures) avec des professionnels,
des ressources et des lieux sénégalais issus de CLAUDE.md.

Propose-moi d'abord un plan et attends ma validation.
```

---

## Étape 4 — Microservice IA

```
Lis CLAUDE.md, section 2, l'architecture du chatbot en 3 niveaux.

Crée le microservice FastAPI dans ai-service/ avec un seul endpoint
POST /traiter-message qui applique les trois niveaux DANS CET ORDRE :

1. DetecteurDetresse : liste de mots-clés. Si déclenché, renvoie
   immédiatement une redirection vers les ressources d'urgence et
   s'arrête. Ne passe jamais aux niveaux suivants.
2. ClassificateurIntention : renvoie un TypeIntention avec un score de
   confiance. Au-dessus du seuil, renvoie une réponse validée prédéfinie.
3. MoteurRAG : recherche par similarité dans ChromaDB sur les ressources
   vectorisées de la plateforme.

Aucun appel à un LLM génératif libre : le chatbot ne répond qu'à partir
de contenus validés.

Écris des tests unitaires pour le détecteur de détresse : c'est la partie
la plus sensible du produit.

Propose-moi d'abord un plan et attends ma validation.
```

---

## Étape 5 — Base du front-end Angular

```
Lis CLAUDE.md, sections 6 et 7.

Initialise le projet Angular dans frontend/ en composants standalone.

Crée dans cet ordre :
1. frontend/src/app/styles/tokens.scss avec TOUS les tokens de la section 6
   (couleurs, typographie, rayons, ombres, espacements). Aucune valeur
   hexadécimale ne devra jamais apparaître ailleurs.
2. Le registre d'icônes core/icons/icons.ts et le composant ss-icon, que je
   te fournis dans le dossier sen-suivi-icons.
3. Le service d'authentification, l'intercepteur JWT et les guards de route
   pour Utilisateur, Professionnel et Administrateur.
4. Le routing complet de l'application, avec les routes publiques
   (accueil, ressources, lieux, chatbot) et les routes protégées.
5. Les deux layouts : layout public avec header et footer complet, layout
   application avec barre latérale desktop et navigation basse mobile.

Ne code encore aucun écran métier.

Propose-moi d'abord un plan et attends ma validation.
```

Pense à copier `icons.ts` et `icon.component.ts` dans le projet avant de lancer ce prompt.

---

## Étape 6 — Les écrans, par lot

Un lot par prompt. Modèle à réutiliser :

```
Lis CLAUDE.md et ouvre les maquettes suivantes dans docs/maquettes/ :
- "Sen Suivi - Tableau de bord Desktop.png"
- "Sen Suivi - Tableau de bord Mobile.png"

Implémente cet écran en Angular standalone, en respectant la mise en page,
les libellés et les espacements des maquettes.

Contraintes :
- tous les styles passent par les tokens de tokens.scss
- toutes les icônes passent par <ss-icon>
- les données viennent de l'API, pas de valeurs codées en dur
- prévois les états de chargement et l'état vide
- responsive : la grille bento desktop devient une pile sur mobile

Propose-moi d'abord un plan et attends ma validation.
```

Ordre conseillé, du plus structurant au plus secondaire :

| Lot | Écrans |
|---|---|
| 1 | Accueil, page 404, états vides |
| 2 | Connexion, inscription particulier, inscription professionnel, mot de passe oublié |
| 3 | Tableau de bord, journal d'humeur, statistiques |
| 4 | Auto-évaluation (question, résultats avec et sans pros) |
| 5 | Chatbot et modale d'urgence |
| 6 | Bibliothèque, détail d'article, répertoire des lieux, détail d'un lieu |
| 7 | Profil professionnel, modales de mise en relation, forum |
| 8 | Tableau de bord professionnel, paramètres, notifications |
| 9 | Administration : validation, modération, ressources, supervision |

---

## Étape 7 — Automatisations n8n et finitions

```
Lis CLAUDE.md, section 2.

Crée les trois workflows n8n décrits dans le mémoire, exportés en JSON
dans un dossier automations/ :
1. rappel quotidien aux utilisateurs sans entrée de journal depuis 3 jours
2. notification à l'administrateur lors d'une nouvelle inscription
   professionnelle en attente
3. vectorisation automatique d'une nouvelle ressource pour le RAG

Documente dans le README comment les importer dans n8n.
```

---

## Le piège à éviter

Ne demande jamais « génère toute l'application ». Tu obtiendrais des milliers de lignes que tu ne pourrais ni relire, ni corriger, ni expliquer en soutenance. Le jury te posera des questions sur **ton** code : chaque étape doit être comprise avant de passer à la suivante.

Si une réponse de Claude Code te dépasse, arrête-toi et demande :

```
Explique-moi ce fichier ligne par ligne, en français, comme si je
découvrais ce concept. Je dois pouvoir le défendre devant un jury.
```

---

## Rythme de commits conseillé

| Après | Message |
|---|---|
| Étape 1 | `chore: initialise le monorepo et docker compose` |
| Étape 2 | `feat(backend): ajoute les modèles issus du diagramme de classes` |
| Étape 3 | `feat(api): expose les routes REST et l'authentification JWT` |
| Étape 4 | `feat(ia): ajoute le microservice chatbot à trois niveaux` |
| Étape 5 | `feat(frontend): initialise Angular, les tokens et le routing` |
| Étape 6 | `feat(frontend): intègre l'écran <nom>` — un commit par écran |
| Étape 7 | `feat(automations): ajoute les workflows n8n` |

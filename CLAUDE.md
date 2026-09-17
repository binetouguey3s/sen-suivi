# Sen Suivi — Contexte projet

Plateforme web et mobile sénégalaise de **prévention, suivi et orientation vers le bien-être mental**.
Projet de certification, Simplon Sénégal, Promo 9 (2025-2026). Autrice : Binetou Gueye.

> Ce fichier est la source de vérité du projet. En cas de doute sur un choix technique, une couleur, un libellé ou une règle métier, il prime sur toute supposition.

---

## 1. Positionnement — à ne jamais contredire

| Règle | Détail |
|---|---|
| Vocabulaire | **Bien-être mental** et **prévention**. Jamais : patient, trouble, diagnostic, thérapie, TCC, psychothérapie, clinicien, addictologue |
| Ton de l'interface | Vouvoiement systématique. Phrases courtes, voix active |
| Modèle économique | **Entièrement gratuit** dans cette version. Le freemium est en *perspectives* du mémoire, jamais dans le produit. Aucune mention de « Premium », d'abonnement ou de paiement |
| Chiffres | Aucun chiffre d'usage ou de performance dans l'interface. Seul le coût d'une consultation classique (25 000 à 50 000 FCFA) est autorisé |
| Sécurité | Le chatbot ne remplace jamais un professionnel. La mention « Sen Suivi ne remplace pas un professionnel de santé » figure sur le chatbot et la page d'accueil |
| Urgence | Numéros du Sénégal uniquement : **800 805 805** (numéro vert d'écoute AJS), **1515** (SAMU), **18** (sapeurs-pompiers), Service de psychiatrie de l'Hôpital de Fann à Dakar. Ne jamais écrire 15, 112 ni aucun autre numéro |
| Contenu | Prénoms, villes, lieux et photos sénégalais uniquement. Tarifs en FCFA |

---

## 2. Stack technique — décidée, non négociable

| Couche | Techno |
|---|---|
| Back-end | Django + Django REST Framework, authentification JWT |
| Front-end | Angular (composants standalone, TypeScript) |
| Microservice IA | FastAPI, séparé du back-end |
| Base vectorielle | ChromaDB ou FAISS |
| Base de données | PostgreSQL |
| Automatisation | n8n (rappels d'inactivité, notification d'inscription pro, indexation RAG) |
| Conteneurisation | Docker + Docker Compose, un conteneur par service |
| Icônes | `lucide-angular`, registre figé dans `frontend/src/app/core/icons/icons.ts` |

### Architecture du chatbot — 3 niveaux, dans cet ordre

1. **Détection de détresse** (sécurité) — mots-clés. Si déclenché : renvoi immédiat des ressources d'urgence, on s'arrête là.
2. **Classification d'intention** — si l'intention est reconnue avec confiance, réponse validée prédéfinie.
3. **RAG** — sinon, recherche par similarité dans la base de ressources vectorisée.

**Jamais de LLM génératif libre.** Le chatbot ne répond qu'à partir de contenus validés de la plateforme.

---

## 3. Structure du dépôt

```
sen-suivi/
├── CLAUDE.md
├── README.md
├── docker-compose.yml
├── .env.example
├── backend/            # Django + DRF
│   ├── config/         # settings, urls, wsgi
│   ├── apps/
│   │   ├── comptes/        # CompteUtilisateur, Utilisateur, Professionnel, Administrateur
│   │   ├── suivi/          # SuiviHumeur, AutoEvaluation
│   │   ├── ressources/     # Ressource, Favori, LieuDetente
│   │   ├── relations/      # DemandeContact
│   │   ├── forum/          # PublicationForum
│   │   ├── chatbot/        # ConversationChatbot, MessageChatbot
│   │   └── notifications/  # Notification, NotificationEmail, NotificationPush
│   └── Dockerfile
├── ai-service/         # FastAPI
│   ├── app/
│   │   ├── detecteur_detresse.py
│   │   ├── classificateur_intention.py
│   │   ├── moteur_rag.py
│   │   └── main.py
│   └── Dockerfile
├── frontend/           # Angular
│   ├── src/app/
│   │   ├── core/       # icons, services, guards, intercepteurs
│   │   ├── shared/     # composants réutilisables
│   │   ├── features/   # une dossier par domaine fonctionnel
│   │   └── styles/     # tokens.scss
│   └── Dockerfile
└── docs/
    └── maquettes/      # les 68 écrans PNG
```

---

## 4. Modèle de données

Issu du diagramme de classes UML du mémoire. Noms de classes en français, comme dans le diagramme.

| Bloc | Classes |
|---|---|
| Comptes | `CompteUtilisateur` (abstrait : id, nom, email, motDePasse, dateCreation), `Utilisateur` (prenom), `Professionnel` (specialite, ville, langue, tarifIndicatif, statutValidation), `Administrateur` |
| Suivi | `SuiviHumeur` (date, scoreHumeur, note), `AutoEvaluation` (date, typeEvaluation, scoreDeTendance) |
| Ressources | `Ressource` (titre, typeRessource, contenu, thematique), `Favori` (dateAjout), `LieuDetente` (nom, ville, description, categorie) |
| Mise en relation | `DemandeContact` (date, statut, message) |
| Forum | `PublicationForum` (contenu, date, statutModeration) |
| Chatbot | `ConversationChatbot` (date), `MessageChatbot` (contenu, typeExpediteur, sourceReponse, dateEnvoi) |
| Service IA | `RessourceVectorisee` (vecteurEmbedding) |
| Notifications | `Notification` (abstrait : contenu, dateEnvoi, statut), `NotificationEmail` (adresseEmail, objet), `NotificationPush` (deviceToken) |
| Automatisation | `WorkflowAutomatisation` (nom, declencheur, actionDeclenchee) |

### Énumérations

`StatutValidationPro` EN_ATTENTE · VALIDE · REFUSE
`NiveauHumeur` TRES_MAL · MAL · NEUTRE · BIEN · TRES_BIEN
`TypeEvaluation` STRESS · ANXIETE · FATIGUE
`TypeRessource` ARTICLE · EXERCICE · PODCAST
`StatutDemandeContact` EN_ATTENTE · ACCEPTEE · REFUSEE
`StatutModeration` VISIBLE · MASQUE · SUPPRIME
`TypeExpediteur` UTILISATEUR · BOT
`SourceReponse` REGLE · RAG
`TypeIntention` STRESS · FATIGUE · BESOIN_ECOUTE · QUESTION_RESSOURCE · URGENCE · AUTRE
`StatutNotification` ENVOYEE · LUE · ECHOUEE

### Les six spécialités de professionnel — exactement celles-ci

Psychologue · Assistant social · Coach en développement personnel · Sophrologue · Médiateur familial · Coach sportif

---

## 5. Routes API

Issues des diagrammes de séquence.

| Méthode | Route | Note |
|---|---|---|
| POST | `/api/auth/register` | inscription utilisateur |
| POST | `/api/auth/login` | retourne un JWT ; refuse un pro non validé |
| POST | `/api/professionnels/inscription` | crée le compte en `EN_ATTENTE` |
| GET | `/api/professionnels?statut=EN_ATTENTE` | admin |
| PATCH | `/api/professionnels/{id}` | admin, passe à `VALIDE` ou `REFUSE` |
| POST | `/api/suivi-humeur` | enregistre une entrée du journal |
| GET | `/api/suivi-humeur?periode=7j` | données du tableau de bord |
| POST | `/api/auto-evaluations` | calcule le score de tendance et suggère des pros |
| POST | `/api/demandes-contact` | crée une `DemandeContact` en `EN_ATTENTE` |
| GET | `/api/ressources` | filtres thématique et format |
| GET | `/api/lieux` | filtres ville et catégorie |
| POST | `/api/chatbot/message` | **accessible sans authentification** |
| GET/POST | `/api/forum/publications` | modération avant publication |

### Accès public, sans compte

Chatbot, bibliothèque de ressources, répertoire des lieux, ressources d'urgence. Tout le reste exige une authentification.

---

## 6. Charte graphique

### Couleurs — aucune autre

| Rôle | Hex |
|---|---|
| Bleu Sen Suivi | `#1B4B6E` |
| Bleu profond | `#12354F` |
| Menthe | `#A9D6C4` |
| Menthe pâle | `#E9F4EF` |
| Menthe très pâle | `#F4FAF7` |
| Sable | `#FBF8F3` |
| Blanc | `#FFFFFF` |
| Gris ardoise | `#6B7280` |
| Gris clair | `#EDEEF1` |
| Rouge alerte | `#E4572E` — urgence et suppression de compte uniquement |

Jamais de noir pur. Jamais de texte blanc sur le menthe. Ombres teintées bleu, jamais grises.

### Fond par zone

| Zone | Fond |
|---|---|
| Pages publiques (accueil, ressources, auth) | Blanc |
| Application connectée | Sable `#FBF8F3`, cartes blanches |
| Administration | Blanc pur, aucun dégradé |

### Typographie

Titres **Schibsted Grotesk** 700/600 · Texte **Inter** 400/500.
Interlettrage -0,03em au-delà de 40px, -0,02em de 20 à 40px. Hauteur de ligne 1,1 sur les grands titres, 1,6 sur le texte. Chiffres tabulaires dans les statistiques et les tarifs. Rien en dessous de 13px.

### Formes

Rayons : boutons et champs 12px, cartes 20 à 24px, grandes cartes et modales 28 à 32px, chips en pilule.
Espacement base 8. Desktop 1440 (12 colonnes, gouttière 24, marges 80). Mobile 375 (4 colonnes, gouttière 16, marges 20).

### Signature de marque

Une courbe d'humeur menthe, trait plein 3px, extrémités arrondies, traverse les pages publiques comme fil conducteur. Absente des écrans de données (le graphique réel la remplace), de l'administration et de la modale d'urgence.

---

## 7. Règles de code

### Environnement

Angular CLI 22.1.2 · Node.js 24.16 · npm 11.17 · Linux x64
Image Docker du front-end : node:24-alpine

### Angular 22 — approche signal-first obligatoire

Angular 22 est la version signal-first. N'écris jamais de code au style
Angular 16-19 : il serait obsolète dans un projet daté de 2026.

| À utiliser | À ne jamais utiliser |
|---|---|
| Zoneless (défaut) | zone.js, provideZoneChangeDetection, ngZone |
| OnPush (défaut sur les nouveaux composants) | ChangeDetectionStrategy.Eager sauf raison explicite |
| signal(), computed(), linkedSignal(), effect() | propriétés de classe mutables pour l'état |
| input(), output(), model() | décorateurs @Input() et @Output() |
| httpResource() pour la lecture de données | HttpClient + subscribe + switchMap |
| Signal Forms (@angular/forms/signals) | ReactiveFormsModule, FormBuilder, ControlValueAccessor |
| @if, @for, @switch, @defer | *ngIf, *ngFor, *ngSwitch, NgIf, NgForOf |
| inject() | injection par constructeur |
| @Service() pour les services applicatifs simples | @Injectable({providedIn:'root'}) par réflexe |
| Composants standalone | NgModule |
| Vitest | Karma, Jasmine |

Notes de version :
- `paramsInheritanceStrategy` vaut `'always'` par défaut en v22 : vérifie
  le comportement des routes imbriquées.
- `httpResource()` reste réactif : si un signal utilisé dans sa lambda
  change, la requête repart automatiquement. C'est ce qu'on veut pour les
  filtres de la bibliothèque et du répertoire des lieux.
- Utilise `@defer (on viewport)` pour les sections lourdes de la page
  d'accueil : la galerie de lieux et la section professionnels.
- `injectAsync` est en developer preview : ne l'utilise pas en v1.

### Conventions du projet

| Sujet | Règle |
|---|---|
| Langue du code | Noms de modèles et de champs en français, cohérents avec le diagramme UML. Commentaires en français |
| Styles | Tous les tokens dans frontend/src/app/styles/tokens.scss. Aucune valeur hexadécimale en dur dans un composant |
| Icônes | Toujours <ss-icon>, jamais <lucide-icon> directement, jamais d'import Lucide hors de core/icons/icons.ts |
| Secrets | Jamais dans le code. Toujours via .env, avec un .env.example à jour |
| Tests | Vitest. Au minimum : détection de détresse, calcul du score de tendance, refus de connexion d'un professionnel non validé |

### Git

Branches : `main` (stable) et `dev` (intégration). Une branche `feat/<nom>`
par fonctionnalité.
Commits en conventional commits, en français :
`feat(chatbot): ajoute la détection de détresse`
Aucune ligne de signature d'outil (type `Co-Authored-By`) dans les messages de
commit : le dépôt est évalué en certification, l'historique doit refléter le
travail de l'autrice.

## 8. Maquettes

Les 68 écrans sont dans `docs/maquettes/`, nommés en français avec le suffixe `- Desktop` ou `- Mobile`.
Avant d'intégrer un écran, **ouvre le PNG correspondant** et respecte sa mise en page, ses libellés et ses espacements.

---

## 9. Comment travailler avec moi

- Propose un **plan** avant d'écrire du code sur toute tâche qui touche plus de deux fichiers, et attends ma validation.
- Une tâche à la fois. Ne pars pas en avant sur des fonctionnalités que je n'ai pas demandées.
- Si une consigne que je te donne contredit ce fichier, **signale-le-moi** avant de l'appliquer.
- Explique-moi simplement les parties techniques : je maîtrise mieux la rédaction que la modélisation.
- Réponds toujours en français.

### Style de code back-end

| Sujet | Règle |
|---|---|
| Vues DRF | Vues basées sur les classes uniquement. Jamais de @api_view ni de vue fonction |
| Génériques | ModelViewSet quand le CRUD complet est pertinent, sinon les vues génériques (ListAPIView, RetrieveAPIView, CreateAPIView...) |
| Mixins | Factoriser la logique transverse en mixins réutilisables plutôt qu'en dupliquant du code entre vues |
| Permissions | Classes de permission dédiées (EstProprietaire, EstProfessionnelValide, EstAdministrateur) dans un module permissions.py par app, jamais de test de rôle en dur dans une vue |
| Sérialiseurs | Un sérialiseur par usage quand la lecture et l'écriture diffèrent (ex. ProfessionnelLectureSerializer et ProfessionnelEcritureSerializer) |
| Routage | Routeur DRF pour les ViewSets, chemins explicites pour les vues génériques |
| Logique métier | Dans les modèles ou des services dédiés, jamais dans les vues. Une vue orchestre, elle ne calcule pas |

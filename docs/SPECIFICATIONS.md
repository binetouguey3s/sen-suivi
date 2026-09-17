# Sen Suivi — Spécifications complémentaires

À placer dans `docs/SPECIFICATIONS.md`. Complète `CLAUDE.md` : celui-ci dit **quoi** construire, celui-là dit **avec quelles valeurs**.

> Les points marqués **Décidé** sont des propositions. Tranche-les avant de lancer le code : ce sont des décisions produit, pas techniques, et le jury peut t'interroger dessus.

---

## 1. Décisions encore ouvertes

| Sujet | Proposition | Statut |
|---|---|---|
| Durée du token JWT | 60 minutes, refresh 7 jours | Décidé |
| Seuil d'inactivité déclenchant un rappel | 3 jours sans entrée de journal | Décidé |
| Nombre de questions par auto-évaluation | 8 | Décidé |
| Fréquence maximale d'une auto-évaluation | Une fois par semaine par type | Décidé |
| Anonymat du forum | Pseudonyme généré à l'inscription, non modifiable | Décidé |
| Modération du forum | A priori : rien n'est visible avant validation | Décidé |
| Conservation de l'historique du chatbot | Uniquement si l'utilisateur est connecté et l'accepte | Décidé |
| Langue de l'interface | Français uniquement en v1 | Décidé |

---

## 2. Règles métier chiffrées

### Journal d'humeur

| Niveau | Valeur numérique |
|---|---|
| TRES_MAL | 1 |
| MAL | 2 |
| NEUTRE | 3 |
| BIEN | 4 |
| TRES_BIEN | 5 |

Une seule entrée par jour et par utilisateur. Une seconde saisie le même jour **met à jour** l'entrée existante.
La courbe du tableau de bord affiche les 7 derniers jours ; les jours sans saisie sont des trous dans la courbe, jamais des zéros.
La « série en cours » compte les jours consécutifs avec une entrée, et se remet à zéro après un jour manqué.

### Auto-évaluation

**Important** : n'utilise aucune échelle clinique existante (type PHQ-9 ou GAD-7). Ce sont des instruments de diagnostic, protégés, et leur usage contredirait le positionnement non clinique de Sen Suivi. Le questionnaire est propre à la plateforme.

- 8 questions par type (STRESS, ANXIETE, FATIGUE)
- 5 réponses possibles par question, cotées de 0 à 4
- Score brut de 0 à 32, ramené sur 100 : `score = (brut / 32) * 100`
- Le `scoreDeTendance` stocké est le score sur 100, arrondi à l'entier

| Score sur 100 | Libellé affiché | Suggestion |
|---|---|---|
| 0 à 33 | Niveau faible | Ressources uniquement |
| 34 à 66 | Niveau modéré | Ressources + professionnels suggérés |
| 67 à 100 | Niveau élevé | Professionnels suggérés en premier + rappel des lignes d'écoute |

La jauge n'est **jamais rouge**, quel que soit le score. Le texte d'interprétation se termine toujours par « Ce résultat n'est pas un diagnostic. »

### Suggestion de professionnels

Après une auto-évaluation, on filtre les `Professionnel` avec `statutValidation = VALIDE`, on priorise ceux de la même ville que l'utilisateur, puis on retient au maximum 3 profils. Si le résultat est vide, l'API renvoie une liste vide et un message : l'interface bascule alors sur la variante « Sans Pros » de la maquette.

### Chatbot — les trois niveaux

**Niveau 0, détection de détresse.** Liste de mots-clés et d'expressions stockée dans un fichier de configuration versionné, `ai-service/app/config/mots_cles_detresse.py`, relu et validé par l'autrice du projet. Elle couvre les expressions de désespoir, de perte de sens et de mise en danger de soi. Dès qu'une correspondance est trouvée, la réponse est **uniquement** la redirection vers les ressources d'urgence : on ne passe jamais aux niveaux suivants, on ne propose aucune ressource, aucun exercice. Ce comportement est couvert par des tests unitaires.

**Niveau 1, classification d'intention.** Seuil de confiance **0,70** (Décidé). Au-dessus, on renvoie la réponse validée associée au `TypeIntention`. En dessous, on passe au niveau 2.

**Niveau 2, RAG.** Recherche par similarité dans ChromaDB, seuil de similarité minimal **0,65** (Décidé), 3 ressources maximum. Si rien ne dépasse le seuil, réponse de repli : proposer la bibliothèque de ressources ou une mise en relation.

Chaque `MessageChatbot` du bot enregistre sa `sourceReponse` : `REGLE` pour les niveaux 0 et 1, `RAG` pour le niveau 2. C'est ce qui rend l'IA **explicable**, un argument central de ton mémoire.

### Validation des professionnels

Un professionnel s'inscrit en `EN_ATTENTE`. Il peut se connecter mais n'accède qu'à un écran d'attente : son profil n'apparaît dans aucune recherche et il ne reçoit aucune demande. Le passage à `VALIDE` déclenche une notification. Le passage à `REFUSE` est définitif pour ce compte.

---

## 3. Inventaire des composants partagés

À créer **avant** le premier écran, dans `frontend/src/app/shared/`. Sans cet inventaire, Claude Code recrée un bouton différent à chaque écran.

| Composant | Variantes | Où il apparaît |
|---|---|---|
| `ss-button` | primaire, secondaire (contour), tertiaire (texte), danger | Partout |
| `ss-icon` | 4 tailles, couleur héritée | Partout |
| `ss-input` | texte, email, mot de passe avec œil, zone de texte, avec compteur | Formulaires |
| `ss-select` | simple, multiple (chips) | Inscription pro, filtres |
| `ss-chip` | filtre, thématique, langue, retirable | Bibliothèque, lieux, profils |
| `ss-badge` | spécialité, statut, format de ressource | Profils, tableaux admin |
| `ss-card` | blanche, menthe, bleu profond, mise en avant | Partout |
| `ss-modal` | centrée desktop, feuille remontante mobile | 6 modales |
| `ss-mood-selector` | 5 émojis, sélection avec anneau menthe | Accueil, tableau de bord, journal |
| `ss-mood-chart` | courbe menthe, aire dégradée, points bleus | Tableau de bord, statistiques |
| `ss-gauge` | jauge circulaire, jamais rouge | Résultat d'auto-évaluation |
| `ss-pro-card` | compacte, étendue | Résultats, profils, forum |
| `ss-place-card` | verticale, horizontale | Accueil, répertoire |
| `ss-resource-card` | grille, mise en avant, horizontale | Bibliothèque, chatbot |
| `ss-empty-state` | avec illustration courbe + bouton | Toutes les listes |
| `ss-skeleton` | carte, ligne, graphique | Tous les chargements |
| `ss-toast` | succès, information, erreur | Confirmations |
| `ss-emergency-banner` | bandeau, modale | Footer, chatbot |
| `ss-header-public` / `ss-footer-full` | — | Pages publiques |
| `ss-sidebar` / `ss-bottom-nav` / `ss-footer-compact` | — | Application connectée |

---

## 4. Correspondance écran → route → endpoint

C'est le document que Claude Code doit avoir sous les yeux pour intégrer les maquettes.

| Maquette | Route Angular | Accès | Endpoints |
|---|---|---|---|
| Accueil | `/` | Public | — |
| Bibliothèque de ressources | `/ressources` | Public | `GET /api/ressources` |
| Détail de l'article | `/ressources/:id` | Public | `GET /api/ressources/:id` |
| Répertoire des lieux | `/lieux` | Public | `GET /api/lieux` |
| Détail d'un lieu | `/lieux/:id` | Public | `GET /api/lieux/:id` |
| Conversation Chatbot | `/chatbot` | Public | `POST /api/chatbot/message` |
| Modale Urgence | superposée | Public | — (données statiques) |
| Connexion | `/connexion` | Public | `POST /api/auth/login` |
| Inscription Particulier | `/inscription` | Public | `POST /api/auth/register` |
| Inscription Professionnel | `/inscription-professionnel` | Public | `POST /api/professionnels/inscription` |
| Mot de passe oublié / Lien envoyé | `/mot-de-passe-oublie` | Public | `POST /api/auth/mot-de-passe-oublie` |
| Onboarding 1-2-3 | `/bienvenue` | Utilisateur | — |
| Tableau de bord | `/app` | Utilisateur | `GET /api/suivi-humeur?periode=7j`, `GET /api/ressources/suggestion` |
| Journal d'humeur | `/app/journal` | Utilisateur | `POST /api/suivi-humeur`, `GET /api/suivi-humeur` |
| Statistiques | `/app/statistiques` | Utilisateur | `GET /api/suivi-humeur?periode=`, `GET /api/auto-evaluations` |
| Auto-évaluation question | `/app/evaluation/:type` | Utilisateur | `GET /api/auto-evaluations/questions/:type` |
| Résultats (avec / sans pros) | `/app/evaluation/:type/resultat` | Utilisateur | `POST /api/auto-evaluations` |
| Profil professionnel | `/professionnels/:id` | Utilisateur | `GET /api/professionnels/:id` |
| Modales mise en relation | superposées | Utilisateur | `POST /api/demandes-contact` |
| Forum liste | `/app/forum` | Utilisateur | `GET /api/forum/publications` |
| Forum détail | `/app/forum/:id` | Utilisateur | `GET`, `POST /api/forum/publications/:id/commentaires` |
| Modale création publication | superposée | Utilisateur | `POST /api/forum/publications` |
| Paramètres du compte | `/app/parametres` | Utilisateur | `GET`, `PATCH /api/comptes/moi` |
| Panneau de notifications | superposé | Utilisateur | `GET /api/notifications` |
| Tableau de bord professionnel | `/pro` | Professionnel validé | `GET /api/demandes-contact` |
| Validation des professionnels | `/admin/professionnels` | Administrateur | `GET`, `PATCH /api/professionnels` |
| Administration Forum | `/admin/forum` | Administrateur | `GET`, `PATCH /api/forum/publications` |
| Gestion des ressources | `/admin/ressources` | Administrateur | CRUD `/api/ressources` |
| Supervision générale | `/admin` | Administrateur | `GET /api/statistiques` |
| États vides, squelettes | composants | — | — |
| Page 404 | `**` | Public | — |

---

## 5. Contenu de départ (fixtures)

Sans ces données, chaque écran s'affiche vide et tu ne peux rien montrer en soutenance.

**Professionnels** (tous en `VALIDE` sauf deux en `EN_ATTENTE` pour démontrer l'écran d'administration) :
Aminata Ba, Psychologue, Dakar Point E, français et wolof, 15 000 FCFA · Moussa Diop, Médiateur familial, Thiès, français et sérère, 12 000 FCFA · Sokhna Mbaye, Sophrologue, Mbour, français et wolof, 10 000 FCFA · Ousmane Sow, Coach sportif, Dakar Ouakam, 8 000 FCFA · Ndèye Coumba Diallo, Assistant social, Saint-Louis, en attente · Ibrahima Kane, Coach en développement personnel, Ziguinchor, en attente.

**Lieux** : Plage de Ngor (Dakar, Plage) · Île de Gorée (Dakar, Île) · Lac Rose (Niayes, Site naturel) · Parc Forestier de Hann (Dakar, Parc) · Lagune de la Somone (Mbour, Lagune) · Corniche Ouest (Dakar, Site naturel) · Popenguine (Thiès, Plage) · Toubab Dialaw (Thiès, Plage).

**Ressources**, au moins deux par thématique : « Cinq minutes pour respirer avant un examen », « Gérer la pression familiale sans culpabiliser », « Dormir mieux quand on travaille en horaires décalés », « Parler de ce qu'on ressent, même quand ça ne se fait pas », « La charge mentale des étudiantes à l'UCAD », « Retrouver le calme après une journée dans les embouteillages », « Exercice de respiration guidée, 4 minutes », « Podcast : la teranga commence par soi-même ».

**Comptes de démonstration** : un utilisateur (Awa Ndiaye) avec 14 jours d'historique d'humeur et 2 auto-évaluations, un professionnel validé, un administrateur.

**Forum** : 6 publications sous pseudonymes — Teranga221, Jàmm_rekk, Etudiante_UCAD, Soleil_de_Thiès, Sama_xel, Anonyme_Dakar — dont une masquée et une en attente de modération.

---

## 6. Environnement et ports

`.env.example` à la racine :

```
# Base de données
POSTGRES_DB=sensuivi
POSTGRES_USER=sensuivi
POSTGRES_PASSWORD=change_moi
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Django
DJANGO_SECRET_KEY=change_moi
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
JWT_ACCESS_MINUTES=60
JWT_REFRESH_DAYS=7

# Microservice IA
AI_SERVICE_URL=http://ai-service:8001
SEUIL_CONFIANCE_INTENTION=0.70
SEUIL_SIMILARITE_RAG=0.65
CHROMA_PERSIST_DIR=/data/chroma

# Front-end
API_BASE_URL=http://localhost:8000/api

# n8n
N8N_WEBHOOK_URL=http://n8n:5678
```

| Service | Port |
|---|---|
| PostgreSQL | 5432 |
| Django | 8000 |
| FastAPI | 8001 |
| Angular | 4200 |
| n8n | 5678 |

Aucun secret dans le dépôt. Le `.env` est dans le `.gitignore`, le `.env.example` est versionné.

---

## 7. Polices

Schibsted Grotesk et Inter sont sur Google Fonts. **Héberge-les localement** dans `frontend/src/assets/fonts/` plutôt que via un CDN : la maquette doit s'afficher correctement même avec une connexion instable, ce qui est un argument d'accessibilité valable au Sénégal et défendable en soutenance.

---

## 8. Confidentialité — à respecter dans le code

| Règle | Implication technique |
|---|---|
| Le forum est anonyme | Ne jamais exposer `nom`, `prenom` ni `email` dans un sérialiseur de publication. Uniquement le pseudonyme |
| L'identité reste masquée avant acceptation | Le sérialiseur de `DemandeContact` ne révèle le nom de l'utilisateur au professionnel qu'une fois le statut passé à `ACCEPTEE` |
| Le chatbot est utilisable sans compte | Aucune donnée personnelle n'est requise sur `POST /api/chatbot/message` |
| Données de bien-être | `SuiviHumeur` et `AutoEvaluation` ne sont lisibles que par leur propriétaire. Un administrateur ne voit que des statistiques agrégées, jamais une entrée individuelle |

---

## 9. Définition de « terminé » pour un écran

Un écran n'est intégré que si les six points sont vrais :

1. La mise en page correspond à la maquette, desktop **et** mobile
2. Aucune valeur hexadécimale en dur : tout passe par `tokens.scss`
3. Toutes les icônes passent par `<ss-icon>`
4. Les données viennent de l'API, rien n'est codé en dur
5. Les trois états sont gérés : chargement, vide, erreur
6. Navigation au clavier possible, focus visible sur chaque élément interactif

---

## 10. À déposer dans `docs/` avant de commencer

| Fichier | Pourquoi |
|---|---|
| `maquettes/` (68 PNG) | Claude Code ouvre les images et lit la mise en page |
| `SPECIFICATIONS.md` | Ce fichier |
| `diagramme-classes.png` | Vérifier la fidélité des modèles au mémoire |
| `diagramme-cas-utilisation.png` | Vérifier les permissions par acteur |
| `sequence-chatbot.png` | Vérifier l'ordre des trois niveaux |
| `sequence-validation-pro.png` | Vérifier le blocage de connexion d'un pro non validé |
| `sequence-mise-en-relation.png` | Vérifier le parcours d'auto-évaluation |
| `sequence-n8n.png` | Vérifier les automatisations |

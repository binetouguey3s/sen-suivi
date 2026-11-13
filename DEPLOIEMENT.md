# Déployer Sen Suivi gratuitement

Ce guide met Sen Suivi en ligne sans rien payer, en attendant un hébergement
LWS et un nom de domaine. Compter une après-midi la première fois.

## Les noms à utiliser partout

Utiliser exactement ces noms : les adresses en découlent, et les fichiers du
dépôt (`render.yaml`, workflows GitHub) les attendent.

| Partie | Service gratuit | Nom à créer | Adresse obtenue |
| --- | --- | --- | --- |
| Base de données | Neon | projet `sen-suivi`, base `sensuivi` | (adresse secrète `DATABASE_URL`) |
| Fichiers envoyés | Supabase Storage | projet `sen-suivi`, bucket `sen-suivi-fichiers` | (clés secrètes) |
| E-mails | Brevo | expéditeur `Sen Suivi` | — |
| Service IA (Titou) | Render | service `sen-suivi-ia` | `https://sen-suivi-ia.onrender.com` |
| API Django | Render | service `sen-suivi-api` | `https://sen-suivi-api.onrender.com` |
| Site | Vercel | projet `sen-suivi` | `https://sen-suivi.vercel.app` |

Plus tard, avec LWS : `sensuivi.com` (ou `sensuivi.sn`) pour le site et
`api.sensuivi.com` pour l'API. Ces deux noms étaient libres le 12 novembre 2026.

Chaque service se crée avec le bouton « Continue with GitHub » : un seul mot de
passe à retenir.

## Ce qu'il faut savoir avant

- **Mise en veille.** Sur Render, un service s'endort après 15 minutes sans
  visite et met environ une minute à se réveiller. L'étape 9 garde l'API
  éveillée en journée ; Titou se réveille quand quelqu'un lui écrit.
- **750 heures par mois.** C'est le total gratuit de Render, pour tous les
  services réunis. Deux services éveillés jour et nuit le dépasseraient (Render
  suspendrait alors tout jusqu'au mois suivant) : d'où le réveil limité à la
  journée de l'étape 9.
- **Hugging Face n'est pas utilisé.** Ses Spaces gratuits demandent désormais un
  abonnement. Titou tourne sur Render dans une version allégée : sans PyTorch,
  les vecteurs de recherche viennent de l'API Mistral (même clé que la
  génération).
- **Usage.** L'offre gratuite de Vercel est réservée à un usage non commercial :
  parfait pour tester et montrer, à remplacer avant d'encaisser des paiements.
- **n8n n'est pas déployé.** Django envoie lui-même les notifications
  (nouvelle demande, nouvelle inscription) et met à jour l'index de Titou. Les
  rappels (journal, tests) partent grâce à une tâche planifiée GitHub (étape 10).
- **Secrets.** Ne jamais écrire une clé dans un fichier du dépôt : elles se
  saisissent uniquement dans le tableau de bord de chaque service.

## Étape 0 — Préparer deux clés secrètes

Dans le terminal, lancer deux fois cette commande et noter les deux résultats :

```
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

- la première sera `AI_SERVICE_CLE` (la même sur les deux services Render) ;
- la seconde sera la **clé interne des rappels** : `N8N_API_KEY` sur Render et
  `CLE_INTERNE` sur GitHub (étape 10).

`DJANGO_SECRET_KEY` n'est pas à préparer : Render la génère seul.

## Étape 1 — La base de données (Neon) — déjà faite

Le projet Neon `sen-suivi` existe (Francfort, PostgreSQL 16, base `sensuivi`)
et contient déjà les tables et les données de démonstration : 98 lieux,
21 ressources, 7 professionnels, les questions des tests et 15 comptes de
démonstration.

Il reste à copier son adresse, `DATABASE_URL` :

1. Sur [console.neon.tech](https://console.neon.tech), ouvrir le projet `sen-suivi`.
2. Bouton **Connect** : base `sensuivi`, rôle `sensuivi`, et **désactiver
   « Connection pooling »** (l'adresse ne doit pas contenir `-pooler`).
3. Copier l'adresse. Elle ressemble à
   `postgresql://sensuivi:…@ep-young-art-….eu-central-1.aws.neon.tech/sensuivi?sslmode=require`.

Pour repartir d'une base neuve un jour : créer un projet comme ci-dessus,
puis lancer les commandes de l'étape 6.

## Étape 2 — Le stockage des fichiers (Supabase Storage)

Sans cette étape, l'audio des podcasts et les photos envoyées depuis
l'administration disparaissent à chaque redémarrage de l'API.

1. Sur [supabase.com](https://supabase.com), créer un projet `sen-suivi`,
   région **Central EU (Frankfurt)**.
2. Dans **Storage**, créer un bucket `sen-suivi-fichiers`, **privé**.
3. Dans **Project Settings > Storage > S3 Connection**, noter :
   - l'**Endpoint** → `STOCKAGE_URL` ;
   - la **Region** → `STOCKAGE_REGION` ;
   - créer une clé d'accès : **Access key ID** → `STOCKAGE_CLE_ACCES`,
     **Secret access key** → `STOCKAGE_CLE_SECRETE`.

## Étape 3 — Les e-mails (Brevo)

1. Sur [brevo.com](https://www.brevo.com), créer un compte (300 e-mails par jour gratuits).
2. Ajouter et vérifier l'adresse d'expédition (par exemple ton Gmail en attendant le domaine).
3. Dans **SMTP & API > SMTP**, noter le login et créer une clé SMTP :
   - `EMAIL_HOST` = `smtp-relay.brevo.com`
   - `EMAIL_HOST_USER` = le login SMTP
   - `EMAIL_HOST_PASSWORD` = la clé SMTP
   - `DEFAULT_FROM_EMAIL` = `Sen Suivi <adresse-vérifiée>`

## Étape 4 — Préparer les réglages de Titou

Rien à créer ici : le service IA naît en même temps que l'API à l'étape 5.
Préparer seulement, dans un bloc-notes **qui ne sera pas enregistré dans le
dépôt**, les lignes de ton `.env` qui commencent par `LLM_`, `MISTRAL_`,
`MODERATION_`, `TRANSCRIPTION_` et `SYNTHESE_` (copier-coller tel quel).

## Étape 5 — L'API Django et Titou (Render)

1. Sur [render.com](https://render.com), **New > Blueprint**, choisir le dépôt
   `sen-suivi`. Render lit `render.yaml` et prépare **deux** services :
   `sen-suivi-api` (Django) et `sen-suivi-ia` (Titou).
2. Remplir les valeurs demandées pour `sen-suivi-api` :

   | Nom | Valeur |
   | --- | --- |
   | `DATABASE_URL` | l'adresse Neon de l'étape 1 |
   | `DJANGO_ALLOWED_HOSTS` | `sen-suivi-api.onrender.com` |
   | `CORS_ALLOWED_ORIGINS` | `https://sen-suivi.vercel.app` |
   | `CSRF_TRUSTED_ORIGINS` | `https://sen-suivi-api.onrender.com` |
   | `FRONTEND_URL` | `https://sen-suivi.vercel.app` |
   | `AI_SERVICE_URL` | `https://sen-suivi-ia.onrender.com` |
   | `AI_SERVICE_CLE` | la clé de l'étape 0 |
   | `EMAIL_*`, `DEFAULT_FROM_EMAIL` | les valeurs de l'étape 3 |
   | `STOCKAGE_*` | les valeurs de l'étape 2 (`STOCKAGE_BUCKET` `sen-suivi-fichiers`) |
   | `N8N_API_KEY` | la clé interne des rappels (étape 0) |

   Et pour `sen-suivi-ia` :

   | Nom | Valeur |
   | --- | --- |
   | `AI_SERVICE_CLE` | la **même** clé de l'étape 0 |
   | `BACKEND_URL` | `https://sen-suivi-api.onrender.com` |
   | `MISTRAL_CLE_API`, `LLM_CLE_API` | les valeurs de ton `.env` |

3. Valider. Le premier déploiement prend quelques minutes ; il crée les tables
   dans Neon.
4. Ouvrir le service **sen-suivi-ia > Environment > Add from .env** et coller
   le bloc préparé à l'étape 4, puis **Save, rebuild and deploy**.
5. Vérifier :
   - `https://sen-suivi-api.onrender.com/api/sante` affiche `{"statut":"ok"}` ;
   - `https://sen-suivi-ia.onrender.com/health` affiche `{"statut":"ok"}`.

   Si une adresse Render est différente (nom déjà pris), la reporter dans
   `AI_SERVICE_URL`, `BACKEND_URL` et les étapes suivantes.

## Étape 6 — Ton compte administrateur

Les données sont déjà dans Neon (étape 1). Il reste à créer **ton** compte
administrateur, avec ton e-mail et un mot de passe personnel. L'offre gratuite
de Render ne donne pas de terminal : la commande se lance depuis ton
ordinateur, Docker démarré, en visant la base Neon.

```
docker compose build backend
docker compose run --rm -e DATABASE_URL="adresse-neon-de-l-etape-1" backend python manage.py creer_administrateur
```

La première commande installe les nouvelles dépendances (une seule fois). La
seconde pose trois questions : e-mail, nom affiché, mot de passe (rien ne
s'affiche quand on tape le mot de passe, c'est normal).

Pour recharger les données de démonstration dans une base neuve, remplacer
`creer_administrateur` par `seed_donnees`.

### Avant d'ouvrir le site au public : les comptes de démonstration

Les 15 comptes de démonstration (`…@sensuivi.sn`) ont tous le mot de passe
`SenSuivi2026!`, écrit dans le code et la documentation : quiconque le lit pourrait s'y
connecter, y compris sur l'administrateur de démonstration. Garde-les tant que
tu testes ; avant d'ouvrir le site à de vrais utilisateurs, lance :

```
docker compose run --rm -e DATABASE_URL="adresse-neon-de-l-etape-1" backend python manage.py securiser_comptes_demo
```

Chaque compte de démonstration reçoit un mot de passe aléatoire que personne ne
connaît : les profils restent visibles (annuaire, forum, ressources), mais plus
personne ne peut s'y connecter. Pour les faire aussi disparaître du site,
ajouter `--desactiver` à la fin. Ton propre compte n'est jamais touché.

## Étape 7 — Le site (Vercel)

1. Sur [vercel.com](https://vercel.com), **Add New > Project**, importer le dépôt `sen-suivi`.
2. Nom du projet : `sen-suivi`. **Root Directory** : `frontend`.
   Les autres réglages viennent de `frontend/vercel.json`.
3. **Environment Variables** : `API_BASE_URL` = `https://sen-suivi-api.onrender.com/api`
4. **Deploy**. Le site est en ligne sur `https://sen-suivi.vercel.app`.

## Étape 8 — Vérifier que tout marche

- [ ] Le site s'ouvre et la liste des lieux s'affiche.
- [ ] Connexion avec le compte administrateur.
- [ ] Un message à Titou reçoit une réponse (la première peut prendre une minute).
- [ ] Un test de stress va jusqu'au résultat.
- [ ] Une inscription de professionnel envoie un e-mail à l'administrateur.
- [ ] Mot de passe oublié : l'e-mail arrive, le lien ouvre bien `sen-suivi.vercel.app`.

## Étape 9 — Garder l'API éveillée en journée

Sur [cron-job.org](https://cron-job.org) (gratuit), **Create cronjob** :

- **URL** : `https://sen-suivi-api.onrender.com/api/sante`
- **Execution schedule** : *Custom*, toutes les **10 minutes**, heures **7 à 22**,
  fuseau **Africa/Dakar**
- **Notifications** : cocher « en cas d'échec » pour être prévenue par e-mail

Ne pas ajouter Titou : il se réveille seul au premier message (une minute
d'attente au plus), et rester sous les 750 heures de Render est plus important.

## Étape 10 — Les rappels (journal, tests)

Une tâche planifiée GitHub (`.github/workflows/rappels.yml`) appelle l'API à
8 h, 12 h 30, 18 h et 21 h, heure de Dakar, avec les mêmes règles que n8n :
moment choisi dans l'onboarding, fréquence, rappels désactivables.

Dans le dépôt **sen-suivi > Settings > Secrets and variables > Actions** :

- onglet *Variables* : `API_URL` = `https://sen-suivi-api.onrender.com`
- onglet *Secrets* : `CLE_INTERNE` = la clé interne des rappels (étape 0), la
  même que `N8N_API_KEY` sur Render.

Pour essayer tout de suite : onglet **Actions**, **Rappels**, « Run workflow ».

## Ensuite, à chaque mise à jour

Il suffit de fusionner dans `main` sur GitHub :

- Vercel et Render (API et Titou) redéploient tout seuls ;
- le workflow **Tests** vérifie le code à chaque envoi.

## Plus tard : passer chez LWS avec un nom de domaine

1. Acheter `sensuivi.com` (ou `sensuivi.sn`) chez LWS.
2. Sans changer d'hébergeur, faire pointer le domaine (zone DNS chez LWS) :
   - `sensuivi.com` et `www` → Vercel (Vercel affiche les enregistrements à créer
     dans **Settings > Domains**) ;
   - `api.sensuivi.com` → Render (**Settings > Custom Domains** du service).
3. Mettre à jour sur Render : `DJANGO_ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`,
   `CSRF_TRUSTED_ORIGINS` et `FRONTEND_URL` avec les nouvelles adresses ; sur
   Vercel : `API_BASE_URL` = `https://api.sensuivi.com/api` ; sur Render
   (`sen-suivi-ia`) : `BACKEND_URL`.
4. Pour tout héberger chez LWS, il faut un **VPS** (l'hébergement mutualisé ne
   fait pas tourner Docker). On y relance alors `docker compose`, avec n8n.

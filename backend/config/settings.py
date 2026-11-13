"""Configuration Django du back-end Sen Suivi."""

from datetime import timedelta
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
import environ
from corsheaders.defaults import default_headers

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()

SECRET_KEY = env('DJANGO_SECRET_KEY', default='change_moi')
DEBUG = env.bool('DJANGO_DEBUG', default=False)
ALLOWED_HOSTS = env.list('DJANGO_ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])
# Render donne l'adresse publique du service : elle est acceptée sans réglage
if env('RENDER_EXTERNAL_HOSTNAME', default=''):
    ALLOWED_HOSTS.append(env('RENDER_EXTERNAL_HOSTNAME'))

# En production, une clé secrète par défaut ou trop courte rendrait les jetons
# de connexion falsifiables : le serveur refuse de démarrer.
if not DEBUG and (SECRET_KEY == 'change_moi' or len(SECRET_KEY) < 40):
    raise RuntimeError('DJANGO_SECRET_KEY doit être une vraie clé secrète (40 caractères ou plus) en production.')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'apps.comptes',
    'apps.suivi',
    'apps.ressources',
    'apps.relations',
    'apps.forum',
    'apps.chatbot',
    'apps.notifications',
    'apps.orientation',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # Fichiers statiques (administration Django) servis par Django lui-même en production
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# En production, une seule adresse DATABASE_URL (celle que donne Neon,
# avec ?sslmode=require) ; en local, les variables POSTGRES_* du .env.
if env('DATABASE_URL', default=''):
    DATABASES = {'default': env.db('DATABASE_URL')}
    DATABASES['default']['CONN_MAX_AGE'] = 60
    DATABASES['default']['CONN_HEALTH_CHECKS'] = True
else:
    # En ligne, sans DATABASE_URL, Django chercherait l'hôte « db » de Docker
    # et échouerait avec un message obscur : on le dit clairement.
    if not DEBUG and not env('POSTGRES_HOST', default=''):
        raise ImproperlyConfigured(
            'DATABASE_URL est vide : coller l\'adresse Neon dans Environment (Render).'
        )
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': env('POSTGRES_DB', default='sensuivi'),
            'USER': env('POSTGRES_USER', default='sensuivi'),
            'PASSWORD': env('POSTGRES_PASSWORD', default=''),
            'HOST': env('POSTGRES_HOST', default='db'),
            'PORT': env('POSTGRES_PORT', default='5432'),
        }
    }

# CompteUtilisateur est le modèle d'authentification : aucun profil séparé
# du modèle User natif de Django n'est utilisé (voir apps/comptes/models.py).
AUTH_USER_MODEL = 'comptes.CompteUtilisateur'

# Robustesse des mots de passe (directive de sécurité, section 2A) :
# 8 caractères minimum, 3 catégories sur 4, aucun mot de passe compromis
# connu (liste locale de Django, sans appel à un service externe), aucune
# suite évidente.
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8},
    },
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
    {'NAME': 'apps.comptes.validateurs.ComplexiteValidator'},
    {'NAME': 'apps.comptes.validateurs.SuiteEvidenteValidator'},
]

# Cache partagé par tous les processus, stocké dans PostgreSQL : il garde les
# compteurs d'échecs de connexion sans ajouter de conteneur Redis. La table
# est créée au démarrage par « python manage.py createcachetable ».
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'cache_sen_suivi',
    }
}

# Protection contre la force brute (directive de sécurité, section 2C).
CONNEXION_TENTATIVES_MAX = env.int('CONNEXION_TENTATIVES_MAX', default=5)
CONNEXION_BLOCAGE_MINUTES = env.int('CONNEXION_BLOCAGE_MINUTES', default=15)

LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Dakar'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Fichiers envoyés (audio des podcasts). Dans Docker : volume « media_data »,
# pour qu'ils survivent à une reconstruction du conteneur.
MEDIA_URL = '/media/'
MEDIA_ROOT = Path(env('MEDIA_ROOT', default=str(BASE_DIR / 'media')))
# Un podcast peut peser jusqu'à 20 Mo : au-delà de 2,5 Mo, Django écrit le
# fichier reçu dans un fichier temporaire plutôt que de le garder en mémoire
FICHIER_AUDIO_MAX_OCTETS = 20 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = FICHIER_AUDIO_MAX_OCTETS + 1024 * 1024
IMAGE_LIEU_MAX_OCTETS = 5 * 1024 * 1024

# Stockage des fichiers envoyés. En local : le dossier MEDIA_ROOT. En
# production gratuite, le disque du serveur est effacé à chaque redémarrage :
# les fichiers partent alors dans un stockage compatible S3 (Supabase Storage,
# Cloudflare R2…) dès que STOCKAGE_BUCKET est renseigné.
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
}
if env('STOCKAGE_BUCKET', default=''):
    STORAGES['default'] = {
        'BACKEND': 'storages.backends.s3.S3Storage',
        'OPTIONS': {
            'bucket_name': env('STOCKAGE_BUCKET'),
            'endpoint_url': env('STOCKAGE_URL'),
            'access_key': env('STOCKAGE_CLE_ACCES'),
            'secret_key': env('STOCKAGE_CLE_SECRETE'),
            'region_name': env('STOCKAGE_REGION', default='auto'),
            # Liens signés et temporaires : un fichier n'est jamais public par défaut
            'querystring_auth': True,
            'querystring_expire': 3600,
            'file_overwrite': False,
        },
    }

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    # Le paramètre ?format= sert de filtre de la bibliothèque : on désactive
    # l'usage qu'en fait DRF pour le rendu.
    'URL_FORMAT_OVERRIDE': None,
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=env.int('JWT_ACCESS_MINUTES', default=60)),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=env.int('JWT_REFRESH_DAYS', default=7)),
}

# Nécessité technique : le front-end Angular (port 4200)
# et le back-end Django (port 8000) sont deux origines distinctes.
CORS_ALLOWED_ORIGINS = env.list(
    'CORS_ALLOWED_ORIGINS',
    default=['http://localhost:4200'],
)

# Jeton d'urgence (apps.orientation.urgence) envoyé par le front en plus des en-têtes standard
CORS_ALLOW_HEADERS = (*default_headers, 'x-jeton-urgence')
# Formulaires de l'administration Django servis derrière HTTPS
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[])

# Production : HTTPS obligatoire derrière le proxy de l'hébergeur (Render, Nginx)
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=True)
    # La vérification de santé de l'hébergeur passe en HTTP interne
    SECURE_REDIRECT_EXEMPT = [r'^api/sante$']
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = env.int('SECURE_HSTS_SECONDS', default=3600)
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = 'same-origin'

# E-mails réels : serveur SMTP lu dans le .env (Gmail avec un mot de passe
# d'application, Brevo…). Sans EMAIL_HOST, les e-mails s'affichent dans les
# journaux du back-end au lieu de partir.
EMAIL_HOST = env('EMAIL_HOST', default='')
EMAIL_BACKEND = (
    'django.core.mail.backends.smtp.EmailBackend' if EMAIL_HOST else 'django.core.mail.backends.console.EmailBackend'
)
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
EMAIL_TIMEOUT = env.int('EMAIL_TIMEOUT', default=10)
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='Sen Suivi <no-reply@sensuivi.sn>')
# Notifications aussi envoyées par e-mail (en plus de la cloche), selon les préférences de chacun
EMAIL_NOTIFICATIONS = env.bool('EMAIL_NOTIFICATIONS', default=True)
# Les notifications partent en arrière-plan : la page n'attend jamais le serveur d'e-mails
EMAIL_ASYNCHRONE = env.bool('EMAIL_ASYNCHRONE', default=True)

# Adresse du front-end, utilisée dans les liens envoyés par e-mail.
FRONTEND_URL = env('FRONTEND_URL', default='http://localhost:4200')

# Microservice IA (FastAPI), séparé du back-end.
AI_SERVICE_URL = env('AI_SERVICE_URL', default='http://localhost:8001')
# Clé partagée avec le microservice IA quand il est en ligne : sans elle,
# n'importe qui pourrait utiliser Titou (et la clé du modèle de langage).
AI_SERVICE_CLE = env('AI_SERVICE_CLE', default='')
AI_SERVICE_ENTETES = {'X-Cle-Service': AI_SERVICE_CLE} if AI_SERVICE_CLE else {}

# Dossier des MP3 des podcasts, servis par le front-end sous /audio/podcasts/
# (commande generer_audio_podcasts). Dans Docker, le front-end n'est pas monté :
# passer --dossier, puis copier les fichiers (voir DOCUMENTATION.md).
PODCASTS_AUDIO_DIR = env('PODCASTS_AUDIO_DIR', default=str(BASE_DIR.parent / 'frontend' / 'public' / 'audio' / 'podcasts'))
# Attente maximale d'une réponse du chatbot : plus long que la cascade de modèles côté IA
AI_SERVICE_DELAI_SECONDES = env.float('AI_SERVICE_DELAI_SECONDES', default=25)

# Automatisation n8n : adresse des webhooks et clé partagée pour les
# endpoints internes (/api/interne/...). La clé est générée par l'équipe
# (jamais une clé d'un service externe) : voir .env.example.
# Vide (hébergement gratuit sans n8n) : Django fait lui-même l'essentiel,
# voir apps.notifications.services.declencher_workflow.
N8N_WEBHOOK_URL = env('N8N_WEBHOOK_URL', default='http://n8n:5678')
N8N_API_KEY = env('N8N_API_KEY', default='')

# Rappels automatiques (workflows n8n) : jamais plus d'un rappel par
# utilisateur pendant RAPPEL_FREQUENCE_MAX_JOURS, tous types confondus
RAPPEL_JOURNAL_JOURS = env.int('RAPPEL_JOURNAL_JOURS', default=3)
RAPPEL_TEST_JOURS = env.int('RAPPEL_TEST_JOURS', default=30)
RAPPEL_FREQUENCE_MAX_JOURS = env.int('RAPPEL_FREQUENCE_MAX_JOURS', default=7)

# Offre de lancement : mise en relation gratuite pendant 2 mois.
# OFFRE_MODE=globale : même date de fin pour tous (OFFRE_DATE_FIN, AAAA-MM-JJ ;
# vide = offre sans fin). OFFRE_MODE=individuelle : OFFRE_DUREE_JOURS à partir
# de l'inscription de chaque utilisateur.
OFFRE_MODE = env('OFFRE_MODE', default='globale')
OFFRE_DATE_FIN = env('OFFRE_DATE_FIN', default='')
OFFRE_DUREE_JOURS = env.int('OFFRE_DUREE_JOURS', default=60)
# Accès à la mise en relation après l'offre (paiement mobile money, à brancher)
ACCES_TARIF_FCFA = env.int('ACCES_TARIF_FCFA', default=2000)
ACCES_DUREE_JOURS = env.int('ACCES_DUREE_JOURS', default=30)
# Durée de validité du jeton remis par le chatbot quand il détecte une détresse
URGENCE_JETON_HEURES = env.int('URGENCE_JETON_HEURES', default=24)

# Modération du forum : analyse en arrière-plan (l'interface n'attend pas le
# modèle) ; au-delà de MODERATION_SEUIL_INFRACTIONS blocages en
# MODERATION_FENETRE_JOURS jours, suspension de MODERATION_SUSPENSION_JOURS jours.
# Les messages de détresse ne comptent jamais.
MODERATION_ASYNCHRONE = env.bool('MODERATION_ASYNCHRONE', default=True)
MODERATION_SEUIL_INFRACTIONS = env.int('MODERATION_SEUIL_INFRACTIONS', default=3)
MODERATION_FENETRE_JOURS = env.int('MODERATION_FENETRE_JOURS', default=30)
MODERATION_SUSPENSION_JOURS = env.int('MODERATION_SUSPENSION_JOURS', default=7)

# Chatbot vocal : durée et poids maximaux d'un enregistrement (refus propre au-delà)
VOCAL_DUREE_MAX_SECONDES = env.int('VOCAL_DUREE_MAX_SECONDES', default=60)
VOCAL_TAILLE_MAX_MO = env.float('VOCAL_TAILLE_MAX_MO', default=10)

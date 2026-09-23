"""Configuration Django du back-end Sen Suivi."""

from datetime import timedelta
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()

SECRET_KEY = env('DJANGO_SECRET_KEY', default='change_moi')
DEBUG = env.bool('DJANGO_DEBUG', default=False)
ALLOWED_HOSTS = env.list('DJANGO_ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])

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
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
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
# suite évidente. Voir docs/securite.md.
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

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    # Le paramètre ?format= sert de filtre de la bibliothèque : on désactive l'usage qu'en fait DRF pour le rendu.
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

# Adresse du front-end, utilisée dans les liens envoyés par e-mail.
FRONTEND_URL = env('FRONTEND_URL', default='http://localhost:4200')

# Microservice IA (FastAPI), séparé du back-end.
AI_SERVICE_URL = env('AI_SERVICE_URL', default='http://localhost:8001')

# Automatisation n8n : adresse des webhooks et clé partagée pour les
# endpoints internes (/api/interne/...). La clé est générée par l'équipe
# (jamais une clé d'un service externe) : voir .env.example.
N8N_WEBHOOK_URL = env('N8N_WEBHOOK_URL', default='http://n8n:5678')
N8N_API_KEY = env('N8N_API_KEY', default='')

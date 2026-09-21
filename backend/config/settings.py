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

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

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

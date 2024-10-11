import os
from pathlib import Path
from dotenv import load_dotenv
import datetime
import requests  # Asegurarse de que esta librería esté instalada
import jwt  # Asegurarse de tener la librería pyjwt instalada

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TEMPLATE_DIR = os.path.join(BASE_DIR, "webappexample", "templates")

DEBUG = os.getenv('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = ['44.220.218.144', 'loocal.co', 'www.loocal.co']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'coreapi',
    'whitenoise.runserver_nostatic',
    'mercadopago',
    'products',
    'orders',
    'payments',
    'csp',
    'loocal'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'loocal.urls'

AUTH0_DOMAIN = os.getenv('AUTH0_DOMAIN', 'dev-bgodgyzz8ugzloem.us.auth0.com')
API_IDENTIFIER = os.getenv('API_IDENTIFIER', 'https://dev-bgodgyzz8ugzloem.us.auth0.com/api/v2/')
ALGORITHMS = ["RS256"]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'loocal.auth_backend.Auth0JWTAuthentication',  # Actualiza esta ruta según tu proyecto
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}

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

WSGI_APPLICATION = 'loocal.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'), 
        'PORT': os.getenv('DB_PORT', '5432'), 
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'es'

TIME_ZONE = 'America/Bogota'

USE_I18N = True

USE_L10N = True

USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'products/static/images'),
]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CORS_ALLOW_ALL_ORIGINS = False

CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',
    'https://loocal.co',
    'http://loocal.co',
    'http://44.220.218.144',
]

SESSION_COOKIE_AGE = 3600

CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = (
    "'self'",
    "'unsafe-inline'",
    "'unsafe-eval'",
    "'strict-dynamic'"
)
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'",)
CSP_FONT_SRC = ("'self'", "https://fonts.gstatic.com",)

CSP_OBJECT_SRC = ("'self'",)

CSRF_TRUSTED_ORIGINS = [
    'http://*',
    'https://loocal.co',
    'http://loocal.co',
    'http://44.220.218.144',
]

SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret_key')

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.titan.email'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'camilo@loocal.co'
EMAIL_HOST_PASSWORD = 'L00c4l@dev24'
DEFAULT_FROM_EMAIL = 'your_email@example.com'

DEBUG = True

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}

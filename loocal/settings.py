import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url
import datetime

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TEMPLATE_DIR = os.path.join(BASE_DIR, "webappexample", "templates")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = ['44.220.218.144', 'loocal.co', 'www.loocal.co']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'rest_framework.authtoken',
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

# Configuración de REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}

# Añade esta configuración para obtener las claves públicas de Auth0 y validar los JWT
def get_jwks():
    jwks_url = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
    jwks = requests.get(jwks_url).json()
    return jwks

def get_rsa_key(token):
    jwks = get_jwks()
    unverified_header = jwt.get_unverified_header(token)
    rsa_key = {}
    for key in jwks['keys']:
        if key['kid'] == unverified_header['kid']:
            rsa_key = {
                'kty': key['kty'],
                'kid': key['kid'],
                'use': key['use'],
                'n': key['n'],
                'e': key['e']
            }
    return rsa_key

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


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

# DATABASES = {
#     'default': dj_database_url.config(default=os.environ.get('DATABASE_URL'))
# }


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

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'es'

TIME_ZONE = 'America/Bogota'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'products/static/images'),
]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files (Uploaded by users)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CORS_ALLOW_ALL_ORIGINS = False

CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',
    'https://loocal.co',
    'http://loocal.co',
    'http://44.220.218.144',
]

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.coreapi.AutoSchema',
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
    ),
    'DEFAULT_EXPIRATION_DELTA': datetime.timedelta(hours=1),
}

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
    'https://server-production-1ddc.up.railway.app',
    'http://107.20.105.251',
    'http://ec2-107-20-105-251.compute-1.amazonaws.com',
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
EMAIL_USE_TLS = True 
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
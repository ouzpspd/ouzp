
import os
from pathlib import Path
from dotenv import load_dotenv
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


dotenv_path = os.path.join(BASE_DIR, '.env')
load_dotenv(dotenv_path)
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
SECRET_KEY = os.getenv('SECRET_KEY')
REDIS_LOCATION = os.getenv('REDIS_LOCATION')

CORDIS_USER_MKO = os.getenv('CORDIS_USER_MKO')
CORDIS_PASSWORD_MKO = os.getenv('CORDIS_PASSWORD_MKO')
CORDIS_USER_OUZP_SPD = os.getenv('CORDIS_USER_OUZP_SPD')
CORDIS_PASSWORD_OUZP_SPD = os.getenv('CORDIS_PASSWORD_OUZP_SPD')
CORDIS_USER_OATTR = os.getenv('CORDIS_USER_OATTR')
CORDIS_PASSWORD_OATTR = os.getenv('CORDIS_PASSWORD_OATTR')


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = [DB_HOST]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': DB_NAME,
        'USER': DB_USER,
        'PASSWORD': DB_PASSWORD,
        'HOST': DB_HOST,
        'PORT': DB_PORT
    }
}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_LOCATION,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient"
        },
        "KEY_PREFIX": "example"
    }
}

STATICFILES_DIRS = [
    BASE_DIR / 'static'
]

#STATIC_ROOT = os.path.join(BASE_DIR, "static")
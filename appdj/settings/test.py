from .base import *


SECRET_KEY = 'test'

RESOURCE_DIR = '/tmp'
MEDIA_ROOT = "/tmp"

CACHES['default']['OPTIONS']['REDIS_CLIENT_CLASS'] = "fakeredis.FakeStrictRedis"


PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.MD5PasswordHasher',
)
DEBUG = False
TEMPLATE_DEBUG = False

REST_FRAMEWORK['TEST_REQUEST_DEFAULT_FORMAT'] = 'json'

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

BROKER_BACKEND = 'memory'
CELERY_ALWAYS_EAGER = True
CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
CELERY_BROKER_URL = 'memory://localhost/'
CELERY_RESULT_BACKEND = None
CELERY_CACHE_BACKEND = 'memory'

INSTALLED_APPS += (
    'rest_framework.authtoken',
)

#MIDDLEWARE = [
#    'django.middleware.security.SecurityMiddleware',
#    'django.contrib.sessions.middleware.SessionMiddleware',
#    'django.middleware.common.CommonMiddleware',
#    'django.middleware.csrf.CsrfViewMiddleware',
#    'django.contrib.auth.middleware.AuthenticationMiddleware',
#    'django.contrib.messages.middleware.MessageMiddleware',
#    'django.middleware.clickjacking.XFrameOptionsMiddleware',
#    'base.middleware.NamespaceMiddleware',
#]
ANONYMOUS_USER_NAME = None

HAYSTACK_CONNECTIONS = {
    "default": {
        'ENGINE': 'haystack.backends.simple_backend.SimpleEngine',
    }
}

ENABLE_BILLING = True

from .base import *


SECRET_KEY = 'test'

RESOURCE_DIR = '/tmp'

CACHES['default']['OPTIONS']['REDIS_CLIENT_CLASS'] = "fakeredis.FakeStrictRedis"


class DisableMigrations(object):

    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return "notmigrations"


PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.MD5PasswordHasher',
)
DEBUG = False
TEMPLATE_DEBUG = False
MIGRATION_MODULES = DisableMigrations()

REST_FRAMEWORK['TEST_REQUEST_DEFAULT_FORMAT'] = 'json'

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

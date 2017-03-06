from .base import *

DEBUG = True

ALLOWED_HOSTS = ['*']

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = (
    'rest_framework.renderers.JSONRenderer',
    'rest_framework.renderers.BrowsableAPIRenderer',
)

REST_FRAMEWORK['DEFAULT_PARSER_CLASSES'] = (
    'rest_framework.parsers.JSONParser',
    'rest_framework.parsers.FormParser',
    'rest_framework.parsers.MultiPartParser'
)

# INSTALLED_APPS.append('debug_toolbar')

# MIDDLEWARE.append('debug_toolbar.middleware.DebugToolbarMiddleware')

INTERNAL_IPS = ['127.0.0.1']

STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, "static")

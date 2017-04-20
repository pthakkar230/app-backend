from .base import *

ALLOWED_HOSTS = ['go-pilot.3blades.io', 'localhost']
if 'TBS_HOST' in os.environ:
    ALLOWED_HOSTS.append(os.environ['TBS_HOST'])

LOGIN_REDIRECT_URL = '/swagger/'

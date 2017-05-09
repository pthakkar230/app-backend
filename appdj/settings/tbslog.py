import os
from appdj.settings import BASE_DIR

BASE_LOG_DIR = os.path.join(BASE_DIR, "logs/")


def check_and_make_dir(sub_dir):
    full_path = os.path.join(BASE_LOG_DIR, sub_dir)
    if not os.path.isdir(full_path):
        os.makedirs(full_path)
    return full_path


handlers = {}
loggers = {}

for app in ['base', 'users', 'billing', 'projects',
            'servers', 'actions', 'infrastructure', 'triggers']:
    app_handler = {'level': "DEBUG",
                   'filename': os.path.join(check_and_make_dir(app), app + ".log"),
                   'formatter': "verbose",
                   'class': "logging.handlers.TimedRotatingFileHandler",
                   'when': "midnight",
                   'interval': 1}
    handlers.update({app + "_file": app_handler})
    app_logger = {'handlers': [app + "_file", ],
                  'level': "DEBUG"}
    loggers.update({app: app_logger})


TBS_LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': "[%(asctime)s] %(levelname)s [%(module)s:%(filename)s:%(lineno)s] %(message)s",
        }
    },
    'handlers': handlers,
    'loggers': loggers,
}

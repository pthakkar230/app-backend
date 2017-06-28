import sys
import os
import json
import logging
log = logging.getLogger('projects')

if __name__ == "__main__":
    import django
    _, settings_module = sys.argv
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_module)
    log.info("Just set DJANGO_SETTINGS_MODULE to {mod}".format(mod=settings_module))
    django.setup()
    from projects.file_watch_handler import run
    files_sent_by_watchman = json.load(sys.stdin)
    run(files_sent_by_watchman)

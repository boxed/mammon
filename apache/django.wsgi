import os
import sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'mammon.settings'

path = '/var/www-python/kodare'
if path not in sys.path:
    sys.path.append(path)

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()

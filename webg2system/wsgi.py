import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

## This application object is used by the development server
## as well as any WSGI server configured to use this file.
#from django.core.wsgi import get_wsgi_application
#application = get_wsgi_application()
import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()

PROJECT_DIR = os.path.dirname(__file__)
path1 = os.path.abspath(os.path.join(PROJECT_DIR, '..'))
path2 = os.path.abspath(os.path.join(PROJECT_DIR, '..', 'webg2system'))
sys.path.append(path1)
sys.path.append(path2)

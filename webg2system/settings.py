# Django settings for webg2system project.
import os
import django

# calculated paths for django and the site
# used as starting points for various other paths
# (as shown in http://morethanseven.net/2009/02/11/django-settings-tip-setting-relative-paths.html)
DJANGO_ROOT = os.path.dirname(os.path.realpath(django.__file__))
SITE_ROOT = os.path.dirname(os.path.realpath(__file__))

DEBUG = True # REDEFINE THIS VARIABLE IN settings_local.py
TEMPLATE_DEBUG = DEBUG # REDEFINE THIS VARIABLE IN settings_local.py

ADMINS = (('', ''),) # REDEFINE THIS VARIABLE IN settings_local.py

MANAGERS = ADMINS # REDEFINE THIS VARIABLE IN settings_local.py

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': os.path.join(SITE_ROOT, 'sqlite.db'), # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    },
    'operations_db': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(SITE_ROOT, 'operations_db.db'),
    },
}
DATABASE_ROUTERS = ['db_router.MyAppRouter']

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = None

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = os.path.join(SITE_ROOT, 'assets')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '' # REDEFINE THIS VARIABLE INSIDE settings_local.py

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"

STATIC_ROOT = '' # REDEFINE THIS VARIABLE INSIDE settings_local.py

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Examples: "http://foo.com/static/admin/", "/static/admin/".
ADMIN_MEDIA_PREFIX = '/static/admin/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = '#2i0_v#z4dh78sh##z7b)7%@&!mls1(@4ospa-)6v(vzsg-6u='

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'webg2system.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(SITE_ROOT, 'templates'),
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.contrib.auth.context_processors.auth',
    'django.contrib.messages.context_processors.messages',
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
    'south',
    'systemsettings',
    'operations',
    'inspiresettings',
    'smssettings',
)

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
#LOGGING = {
#    'version': 1,
#    'disable_existing_loggers': False,
#    'handlers': {
#        'mail_admins': {
#            'level': 'ERROR',
#            'class': 'django.utils.log.AdminEmailHandler'
#        }
#    },
#    'loggers': {
#        'django.request': {
#            'handlers': ['mail_admins'],
#            'level': 'ERROR',
#            'propagate': True,
#        },
#    }
#}
LOGGING = {
        'version' : 1,
        'disable_existing_loggers' : True,
        'formatters': {
            'simple' : {'format' : '%(levelname)s %(message)s'},
            'verbose' : {'format' : '%(levelname)s %(asctime)s %(module)s '\
                                    '%(process)s %(thread)s %(message)s'},
        },
        'handlers': {
            'null' : {
                'level' : 'DEBUG', 
                'class' : 'django.utils.log.NullHandler',
            },
            'console' : {
                'level' : 'DEBUG', 
                'class' : 'logging.StreamHandler',
                'formatter' : 'simple',
            },
            'mail_admins' : {
                'level' : 'ERROR', 
                'class' : 'django.utils.log.AdminEmailHandler',
            },
        },
        'loggers': {
            'django' : {
                'handlers' : ['null',],
                'propagate' : True,
                'level' : 'INFO',
            },
            'django.request' : {
                'handlers' : ['mail_admins'],
                'propagate' : False,
                'level' : 'ERROR',
            },
            #'operations' : {
            #    'handlers' : ['console'],
            #    'level' : 'DEBUG',
            #},
            #'operations.models' : {
            #    'handlers' : ['console'],
            #    'level' : 'DEBUG',
            #},
            #'operations.views' : {
            #    'handlers' : ['console'],
            #    'level' : 'DEBUG',
            #},
            'operations.core' : {
                'handlers' : ['console', 'mail_admins'],
                'level' : 'DEBUG',
            },
            'webg2system.api' : {
                'handlers' : ['console', 'mail_admins'],
                'level' : 'DEBUG',
            },
        },
}

# local settings overrides. Must be the last import!
try:
    from settings_local import *
except ImportError:
    pass

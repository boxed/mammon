#!/usr/bin/python
# Django settings for mammon project.
from pathlib import Path

from iommi import (
    Asset,
    Style,
)
from iommi.style_bootstrap import bootstrap

DEBUG = False
TEMPLATE_DEBUG = DEBUG
BASE_DIR = str(Path(__file__).resolve().parent.parent)

SERVER_EMAIL = 'robot@kodare.net'

ADMINS = (('Möller', 'boxed@killingar.net'),)

import os
DOCUMENT_ROOT = os.path.split(os.path.dirname(os.path.abspath(__file__)))[0] + '/'

MANAGERS = ADMINS

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Stockholm'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'sv'

ALLOWED_HOSTS = [
    '.kodare.net',
    '127.0.0.1',
    'localhost',
]

LOCALE_PATHS = (
    os.path.join(os.path.abspath(os.path.dirname(__file__)), 'locale'),
)

LANGUAGES = (
    ('sv', 'Svenska'),
    ('en', 'English'),
)

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

SITE_ID = 1

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True,
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}

LOGIN_URL = '/login/'

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/site-media/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'h1p6ej(*2dmua-_^l!71*^!2d00-a+nt4-+b&u4pzaw6)iqh=h'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

MIDDLEWARE = [
    'iommi.live_edit.Middleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # TODO:!!! changing category for transaction doesn't work with CSRF. For example.
    # 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'mammon.middleware.mammon_middleware',
    'iommi.sql_trace.Middleware',
    'iommi.profiling.Middleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'iommi.middleware',
]

TEMPLATE_CONTEXT_PROCESSORS = (
    # 'django.contrib.auth.context_processors.auth',
    # 'django.core.context_processors.debug',
    # 'django.core.context_processors.i18n',
    # 'django.core.context_processors.media',
    'mammon.context_processors.general',
)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            # insert your TEMPLATE_DIRS here
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                # 'django.core.context_processors.debug',
                # 'django.core.context_processors.i18n',
                # 'django.core.context_processors.media',
                'mammon.context_processors.general',
            ],
        },
    },
]

ROOT_URLCONF = 'mammon.urls'

TEMPLATE_DIRS = tuple()
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
# )

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    # 'django.contrib.admin',
    'django.contrib.flatpages',
    'django_fastdev',
    'mammon.registration',
    'mammon.money',
    'mammon.authentication',
    'iommi',
)

REGISTRATION_NEXT = '/settings/'


dokku_db_conf = {}

# new hotness
if os.environ.get('DOKKU_POSTGRES_MAMMON_NAME'):
    dokku_db_conf = {
        'PORT': os.environ['DOKKU_POSTGRES_MAMMON_PORT_5432_TCP_PORT'],
        'HOST': os.environ['DOKKU_POSTGRES_MAMMON_PORT_5432_TCP_ADDR'],
        'USER': 'postgres',
        'PASSWORD': os.environ['DOKKU_POSTGRES_MAMMON_ENV_POSTGRES_PASSWORD'],
    }

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'mammon',
        **dokku_db_conf
    }
}

DATE_FORMAT = 'Y-m-d'
DATETIME_FORMAT = 'Y-m-d'

IOMMI_DEFAULT_STYLE = Style(
    bootstrap,
    base_template='iommi_base.html',
    root__assets=dict(
        jquery_ui=Asset.js(
            attrs=dict(
                src='https://code.jquery.com/ui/1.13.0/jquery-ui.min.js',
                crossorigin='anonymous',
                integrity='sha256-hlKLmzaRlE8SCJC1Kw8zoUbU8BxA+8kR3gseuKfMjxA',
            ),
            after=-1,
        ),
        i18n=Asset.js(attrs=dict(src="/jsi18n/", crossorigin='anonymous')),
        lodash=Asset.js(attrs=dict(src="https://cdnjs.cloudflare.com/ajax/libs/lodash.js/2.4.1/lodash.min.js", crossorigin='anonymous')),
        inline_edit=Asset.js(attrs=dict(src="/inline_edit.js", crossorigin='anonymous')),
        input_overlay=Asset.js(attrs=dict(src="/input_overlay.js", crossorigin='anonymous')),
        # inlinecomplete=Asset.js(attrs=dict(src="/site-media2/jquery.inlinecomplete.js", crossorigin='anonymous')),
        intoViewport=Asset.js(attrs=dict(src="/site-media2/jquery.intoViewport.min.js", crossorigin='anonymous')),
        custom_mammon=Asset.js(attrs=dict(src="/site-media2/custom.js", crossorigin='anonymous')),
    ),
    Container=dict(
        attrs__class={
            'mt-5': False,
            'iommi-container': True,
        },
    ),
)

try:
    from settings_local import *
except ImportError:
    pass

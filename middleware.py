import cProfile
import re
from io import StringIO

from django.conf import settings

from threading import local
_thread_locals = local()


def get_current_user():
    return getattr(_thread_locals, 'user', None)


def get_current_request():
    return getattr(_thread_locals, 'request', None)


def mammon_middleware(get_response):
    def middleware(request):
        _thread_locals.request = request
        _thread_locals.user = request.user
        response = get_response(request)
        return response

    return middleware


words_re = re.compile(r'\s+')

group_prefix_re = [
    re.compile("^.*/django/[^/]+"),
    re.compile("^(.*)/[^/]+$"),  # extract module path
    re.compile(".*"),  # catch strange entries
]

import sys
import os
import re
import tempfile
import StringIO

from django.conf import settings

from threading import local
_thread_locals = local()


def get_current_user():
    return getattr(_thread_locals, 'user', None)


def get_current_request():
    return getattr(_thread_locals, 'request', None)


class MammonMiddleware(object):
    def __init__(self):
        pass
        
    def process_request(self, request):
        _thread_locals.request = request
        _thread_locals.user = request.user

words_re = re.compile(r'\s+')

group_prefix_re = [
    re.compile("^.*/django/[^/]+"),
    re.compile("^(.*)/[^/]+$"),  # extract module path
    re.compile(".*"),  # catch strange entries
]


class ProfileMiddleware(object):
    """
    Displays hotshot profiling for any view.
    http://yoursite.com/yourview/?prof

    Add the "prof" key to query string by appending ?prof (or &prof=)
    and you'll see the profiling results in your browser.
    It's set up to only be available in django's debug mode, is available for superuser otherwise,
    but you really shouldn't add this middleware to any production configuration.

    WARNING: It uses hotshot profiler which is not thread safe.
    """
    def process_request(self, request):
        import hotshot
        import hotshot.stats

        if (settings.DEBUG or request.user.is_superuser) and 'prof' in request.GET:
            self.tmpfile = tempfile.mktemp()
            self.prof = hotshot.Profile(self.tmpfile)

    def process_view(self, request, callback, callback_args, callback_kwargs):
        if (settings.DEBUG or request.user.is_superuser) and 'prof' in request.GET:
            return self.prof.runcall(callback, request, *callback_args, **callback_kwargs)

    def process_response(self, request, response):
        import hotshot
        import hotshot.stats

        if (settings.DEBUG or request.user.is_superuser) and 'prof' in request.GET:
            self.prof.close()

            out = StringIO.StringIO()
            old_stdout = sys.stdout
            sys.stdout = out

            stats = hotshot.stats.load(self.tmpfile)
            stats.sort_stats('cumulative')
            stats.print_stats()

            sys.stdout = old_stdout
            stats_str = out.getvalue()

            lines = stats_str.split("\n")[:40]
            lines = ['<span%s>%s</span>' % (' style="font-weight: bold"' if 'mammon' in x else '', x) for x in lines]

            response.content = '<style>body {font-family: monospace; white-space: pre;}</style>'
            response.content += "\n".join(lines)

            os.unlink(self.tmpfile)

        return response
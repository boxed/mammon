import cProfile
import re
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
    """
    def process_request(self, request):
        if (settings.DEBUG or request.user.is_superuser) and 'prof' in request.GET:
            self.prof = cProfile.Profile()
            self.prof.enable()

    def process_view(self, request, callback, callback_args, callback_kwargs):
        if (settings.DEBUG or request.user.is_superuser) and 'prof' in request.GET:
            return self.prof.runcall(callback, request, *callback_args, **callback_kwargs)

    def process_response(self, request, response):
        if (settings.DEBUG or (hasattr(request, 'user') and request.user.is_superuser)) and 'prof' in request.GET:
            self.prof.disable()

            import pstats
            s = StringIO.StringIO()
            ps = pstats.Stats(self.prof, stream=s).sort_stats('cumulative')
            ps.print_stats()

            stats_str = s.getvalue()

            lines = stats_str.split("\n")[:100]
            lines = ['<span%s>%s</span>' % (' style="font-weight: bold"' if 'mammon' in x else '', x) for x in lines]

            response.content = '<style>body {font-family: monospace; white-space: pre;}</style>'
            response.content += "\n".join(lines)

        return response
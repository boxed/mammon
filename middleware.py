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
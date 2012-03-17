class MammonMiddleware(object):
    def __init__(self):
        pass
        
    def process_request(self, request):
        from curia import _thread_locals
        _thread_locals.request = request
        _thread_locals.user = request.user
        from django.contrib.auth.models import Group
        _thread_locals.community = Group.objects.get_or_create(name='mammon')[0]
        
        def group_absolute_url(self):
            return '/'
        Group.get_absolute_url = group_absolute_url
        
        request.community = _thread_locals.community
        try:
            foo = _thread_locals.community
        except:
            from curia.authentication.models import MetaGroup
            MetaGroup.objects.create(group=request.community, friend_group=False)
        request.domain = 'mammon.kodare.net'
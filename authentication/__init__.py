import datetime
import exceptions

from django.utils.encoding import smart_unicode


class AccessDeniedException(exceptions.Exception):
    user = None
    obj = None
    command = None

    def __init__(self, user, obj, command, comment = ''):
        self.user = user
        self.obj = obj
        self.command = command
        self.comment = comment
        self.args = {'user':user, 'obj':obj, 'command':command, 'comment':comment}

    #def __unicode__(self):
    #    return 'Access denied for command %s on object %s for user %s' % (self.user, self.obj, self.command)
    
def get_command(user, obj, command = None, level=1):
    if command == None:
        # guess command based on function name
        import inspect
        stackframe = inspect.stack()[level]
        function_name = stackframe[3]
        command = function_name.split('_')[0]

        # translate from function naming convention to django permission naming convention
        if command == 'edit':
            command = 'change'
        
        #if command not in ('change', 'delete', 'add', 'view', 'list'):
            #raise AccessDeniedException(user, obj, command, 'unknown access level')
            
    return command

    
class PermissionResponse:
    def __init__(self, granted, motivation):
        self.granted = granted
        self.motivation = motivation
        
    def __nonzero__(self):
        return self.granted
        
    def __unicode__(self):
        return smart_unicode(self.granted)+': '+unicode(self.motivation)
        
    def __repr__(self):
        return unicode(self)
        
def has_django_perm(user, obj, command):
    # translate from function naming convention to django permission naming convention
    if command == 'edit':
        command = 'change'

    if user.is_superuser:
        return PermissionResponse(True, 'user is superuser')
    
    if user.has_perm(obj._meta.app_label+'.can_'+command+'_'+obj._meta.module_name):
        return PermissionResponse(True, u'user has global permission on class')
    return None


def add_patterns(urlpatterns, cls):
    from django.conf import settings
    if 'curia.notifications' in settings.INSTALLED_APPS:
        from django.conf.urls import patterns
        urlpatterns += patterns('mammon.authentication.views',
            (r'^(?P<object_id>\d+)/permissions/$', 'view_permissions', {'type': cls}),
            (r'^(?P<object_id>\d+)/permissions/advanced/$', 'view_advanced_permissions', {'type': cls}),
        )

    
def age(bday, d=datetime.date.today()):
    return (d.year - bday.year) - int((d.month, d.day) < (bday.month, bday.day))
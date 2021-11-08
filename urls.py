from django.conf.urls import include
from django.urls import (
    path,
    re_path,
)
from django.views.i18n import JavaScriptCatalog

from django.views.static import serve
from iommi.admin import (
    Admin,
    Auth,
)

from authentication.views import (
    edit_user_password,
)
from views import (
    echo_headers,
    error_test,
)
from . import settings

urlpatterns = [
    path('', include('money.urls')),
    path('settings/password/$', edit_user_password),

    path(r'registration/', include('mammon.registration.urls')),
    path(r'echo_headers/', echo_headers),
    path(r'bin2/gfskod', echo_headers),

    path(r'system/error_test/$', error_test),

    path('jsi18n/', JavaScriptCatalog.as_view(), name='javascript-catalog'),
    path('admin/', include(Admin().urls())),

    # admin:
    # path(r'admin/', include(admin.site.urls)),
    # re_path(r'^media/(?P<path>.*)$', serve, {'document_root': '/var/www-python/kodare/django/contrib/admin/media'}),
    re_path(r'^site-media2/(?P<path>.*)$', serve, {'document_root': settings.DOCUMENT_ROOT + 'mammon/site-media'}),

    path('', include(Auth.urls()))
]

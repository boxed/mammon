from django.conf.urls import include
from django.urls import (
    path,
    re_path,
)

from django.views.static import serve

from authentication.views import (
    edit_user_password,
    login,
    logout,
)
from views import (
    echo_headers,
    error_test,
)
from . import settings
from django.contrib import admin

urlpatterns = [
    path('', include('money.urls')),
    re_path(r'^settings/password/$', edit_user_password),

    re_path(r'^login/', login),
    re_path(r'^logout/', logout),
    re_path(r'^registration/', include('mammon.registration.urls')),
    re_path(r'^echo_headers/', echo_headers),
    re_path(r'^bin2/gfskod', echo_headers),

    re_path(r'^error_test/$', error_test),

    # re_path(r'^jsi18n/$', javascript_catalog, {'packages': 'django.conf'}),

    # admin:
    # path(r'admin/', include(admin.site.urls)),
    # re_path(r'^media/(?P<path>.*)$', serve, {'document_root': '/var/www-python/kodare/django/contrib/admin/media'}),
    re_path(r'^site-media2/(?P<path>.*)$', serve, {'document_root': settings.DOCUMENT_ROOT + 'mammon/site-media'}),
]

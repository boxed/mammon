from django.conf.urls import *

urlpatterns = patterns('mammon.registration.views',
    (r'^set_new_password/$', 'set_new_password'),
    (r'^request_new_password/$', 'request_new_password'),
    (r'^$', 'register'),
)

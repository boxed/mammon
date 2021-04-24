from django.urls import path

from registration.views import (
    request_new_password,
    set_new_password,
    register,
)

urlpatterns = [
    path(r'set_new_password/', set_new_password),
    path(r'request_new_password/', request_new_password),
    path(r'', register),
]

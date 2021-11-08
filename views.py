import django.forms
from django.http import HttpResponse
# noinspection PyUnresolvedReferences
from django.shortcuts import render
from django.utils.translation import ugettext as _


class LoginForm(django.forms.Form):
    username = django.forms.CharField(max_length=1024, label=_('Email'))
    password = django.forms.CharField(max_length=1024, widget=django.forms.PasswordInput, label=_('Password'))


def echo_headers(request):
    post = '<h1>POST</h1>\n' + '<br />\n'.join(['%s: %s' % (i, request.POST[i]) for i in request.POST])
    get = '<h1>GET</h1>\n' + '<br />\n'.join(['%s: %s' % (i, request.GET[i]) for i in request.GET])
    cookies = '<h1>COOKIES</h1>\n' + '<br />\n'.join(['%s: %s' % (i, request.COOKIES[i]) for i in request.COOKIES])
    meta = '<h1>META</h1>\n' + '<br />\n'.join(['%s: %s' % (i, request.META[i]) for i in request.META])
    return HttpResponse('<html><body>%s %s %s %s</body></html>' % (post, get, cookies, meta))


def error_test(request):
    # noinspection PyUnresolvedReferences
    asd()

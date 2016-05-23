import django
from django.shortcuts import render_to_response
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect
# noinspection PyUnresolvedReferences
from django.utils.translation import ugettext as _
import django.forms
from mammon.authentication.models import MetaUser


class LoginForm(django.forms.Form):
    username = django.forms.CharField(max_length=1024, label=_('Email'))
    password = django.forms.CharField(max_length=1024, widget=django.forms.PasswordInput, label=_('Password'))


def echo_headers(request):
    post = '<h1>POST</h1>\n' + '<br />\n'.join(['%s: %s' % (i, request.POST[i]) for i in request.POST])
    get = '<h1>GET</h1>\n' + '<br />\n'.join(['%s: %s' % (i, request.GET[i]) for i in request.GET])
    cookies = '<h1>COOKIES</h1>\n' + '<br />\n'.join(['%s: %s' % (i, request.COOKIES[i]) for i in request.COOKIES])
    meta = '<h1>META</h1>\n' + '<br />\n'.join(['%s: %s' % (i, request.META[i]) for i in request.META])
    return HttpResponse('<html><body>%s %s %s %s</body></html>' % (post, get, cookies, meta))


def login(request, template='authentication/login.html'):
    next_url = request.GET.get('next', request.POST.get('next', '/'))

    if request.POST:
        form = LoginForm(request.POST)
        if form.is_valid():
            try:
                username = User.objects.get(email=form.cleaned_data['username']).username
                user = authenticate(username=username, password=form.cleaned_data['password'])
            except User.DoesNotExist:
                user = None
            if user is None:
                form.errors['username'] = [_(u'Username or password incorrect')]
            else:
                if user is not None and user.is_active:
                    from django.contrib.auth import login
                    login(request, user)

                    try:
                        if user.meta.language != '':
                            request.session['django_language'] = user.meta.language
                        else:
                            from django.conf import settings
                            request.session['django_language'] = settings.LANGUAGE_CODE
                        meta = user.meta
                        meta.last_notification_email_time = None
                        meta.save()
                    except MetaUser.DoesNotExist:
                        pass
                return HttpResponseRedirect(next_url)
    else:
        form = LoginForm(initial={})

    return render_to_response(template, {'login_form': form, 'next': next_url})


def logout(request):
    from django.contrib.auth import logout
    logout(request)
    return HttpResponseRedirect('/')


def error_test(request):
    # noinspection PyUnresolvedReferences
    asd()
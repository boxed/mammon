from curia.authentication.models import MetaUser
from curia.shortcuts import render_to_response
from django.contrib.auth import authenticate
from curia.authentication.views import LoginForm
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect
# noinspection PyUnresolvedReferences
from django.utils.translation import ugettext as _


def echo_headers(request):
    post = '<h1>POST</h1>\n' + '<br />\n'.join(['%s: %s' % (i, request.POST[i]) for i in request.POST])
    get = '<h1>GET</h1>\n' + '<br />\n'.join(['%s: %s' % (i, request.GET[i]) for i in request.GET])
    cookies = '<h1>COOKIES</h1>\n' + '<br />\n'.join(['%s: %s' % (i, request.COOKIES[i]) for i in request.COOKIES])
    meta = '<h1>META</h1>\n' + '<br />\n'.join(['%s: %s' % (i, request.META[i]) for i in request.META])
    return HttpResponse('<html><body>%s %s %s %s</body></html>' % (post, get, cookies, meta))


def login(request, template='authentication/login.html'):
    next = request.REQUEST.get('next', '/')

    if request.POST:
        form = LoginForm(request.POST)
        if form.is_valid():
            try:
                username = User.objects.get(email=form.cleaned_data['username']).username
                user = authenticate(username=username, password=form.cleaned_data['password'])
            except:
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
                return HttpResponseRedirect(next)
    else:
        form = LoginForm(initial={})

    return render_to_response(request, template, {'login_form': form, 'next': next})


def error_test(request):
    asd()
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.core.validators import EmailValidator
from django.shortcuts import *
import django.forms
from django.utils.translation import ugettext
from mammon.registration.models import *


def register(request):
    class RegisterForm(django.forms.Form):
        email = django.forms.CharField(label=ugettext('E-mail address'))
        password = django.forms.CharField(max_length=30, required=True, widget=django.forms.PasswordInput, label=ugettext('Password'))
        confirm_password = django.forms.CharField(max_length=30, required=True, widget=django.forms.PasswordInput, label=ugettext('Confirm password'))
        # TODO: language

    if request.POST:
        form = RegisterForm(request.POST)

        # validate email
        email = form.data['email']
        if not EmailValidator(email):
            form.errors['email'].append(ugettext('%s is not a valid email address') % email)

        if form.data['password'] != form.data['confirm_password']:
            form.errors['email'].append(ugettext('Passwords did not match.'))

        if form.is_valid():
            email = form.cleaned_data['email']

            try:
                User.objects.get(email=email)
                return HttpResponseRedirect('/registration/request_new_password/')
            except User.DoesNotExist:
                user = User.objects.create(email=email, username=User.objects.make_random_password(30), is_active=False)
                user.set_password(form.cleaned_data['password'])
                user.save()

            from django.template import loader, Context
            authenticate(username=user.username, password=form.cleaned_data['password'])
            return HttpResponseRedirect('/')
    else:
        form = RegisterForm(initial={})

    return render_to_response('registration/register.html', {'form': form})


def request_new_password(request):
    class RequestForm(django.forms.Form):
        email = django.forms.CharField(max_length=150, required=True, label=ugettext('Email'))

    if request.POST:
        form = RequestForm(request.GET)
        try:
            user = User.objects.get(email=request.GET['email'])
        except User.DoesNotExist:
            user = None
            form.errors['email'] = (ugettext('There is no user with this email'),)

        if form.is_valid():
            from django.template import loader, Context

            password = User.objects.make_random_password(6)
            email = form.cleaned_data['email']
            c = {
                'password': password,
                'email': email,
            }
            subject = ugettext('New password request for Mammon')

            from django.contrib.sites.models import Site
            send_mail(
                subject,
                message=loader.get_template('registration/retrieve.txt').render(Context(c)),
                html_message=loader.get_template('registration/retrieve.html').render(Context(c)),
                from_email='retrieve@' + Site.objects.get_current().domain,
                recipient_list=[email])

            try:
                forgot = ForgotPassword.objects.get(user=user)
                forgot.delete()
            except ForgotPassword.DoesNotExist:
                pass
            ForgotPassword.objects.create(user=user, password=password, created_from='')

            return render_to_response('registration/request_email_sent.html')

    else:
        form = RequestForm(initial={})

    return render_to_response('registration/request_new_password.html', {'form': form, 'disable_login_box': True})


def set_new_password(request):
    class NewPasswordForm(django.forms.Form):
        password = django.forms.CharField(max_length=30, required=True, widget=django.forms.PasswordInput, label=ugettext('New password'))
        confirm_password = django.forms.CharField(max_length=30, required=True, widget=django.forms.PasswordInput, label=ugettext('Confirm password'))

    if request.POST:
        form = NewPasswordForm(request.GET)

        try:
            user = User.objects.get(email=request.GET['email'])
            forgot = ForgotPassword.objects.get(user=user, password=request.GET['code'])
        except (User.DoesNotExist, ForgotPassword.DoesNotExist):
            user = None
            forgot = None
            form.errors['password'] = (ugettext('Username or password incorrect'),)

        if form.data['password'] != form.data['confirm_password']:
            form.errors['confirm'] = (ugettext('Passwords did not match.'),)

        if form.is_valid():
            user.set_password(form.cleaned_data['password'])
            user.save()
            forgot.delete()
            return HttpResponseRedirect('/')
    else:
        form = NewPasswordForm(initial={})

    return render_to_response('registration/set_new_password.html', {'form': form})

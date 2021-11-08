from django.shortcuts import render

from mammon.authentication.models import *
from django.core.validators import EmailValidator
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext as _
import django.forms


def edit_user_settings(request, user_id):
    user = User.objects.get(pk=user_id)

    if user != request.user and not request.user.is_superuser:
        return HttpResponseRedirect('/')

    meta = user.meta

    class EditForm(django.forms.Form):
        firstname = django.forms.CharField(label=_('First name'), help_text=_('Visible to other users'))
        lastname = django.forms.CharField(required=False, label=_('Last name'), help_text=_('Visible to other users'))
        email = django.forms.CharField(label=_('E-mail'), help_text=_('Not visible to other users'))
        birthday = django.forms.DateField(required=False, label=_('Birthday'), help_text=_('Format is yyyy-MM-dd, e.g. 1980-05-27'))
        # language = django.forms.ChoiceField(label=_('Language'), choices=(('en-us', 'English'), ('sv-se', 'Svenska'),))
        gender = django.forms.ChoiceField(label=_('Gender'), choices=(('M', _('Male')), ('F', _('Female')),), help_text=_('Visible to other users'))
        old_password = django.forms.CharField(label=_('Password'), widget=django.forms.PasswordInput, help_text=_('Confirm your identity'))
        # new_password = django.forms.CharField(label=_('Password'), widget = django.forms.PasswordInput, required=False)
        # confirm = django.forms.CharField(label=_('Confirm password'), widget = django.forms.PasswordInput, required=False)
        # location = django.forms.ChoiceField(label=_('Location'), choices=(('Stockholm', 'Stockholm'), ('Inte Stockholm', 'Inte Stockholm'),))
        notification_style = django.forms.ChoiceField(label=_('Notification style'), choices=user.meta.NotificationStyle_Choices)

        # TODO: first day of week

    if request.POST:
        form = EditForm(request.POST)
        if form.data['firstname'].isspace():
            form.data['firstname'] = None
        if not user.check_password(form.data['old_password']):
            form.errors['old_password'] = (_('Incorrect password'),)

        email = form.data["email"]
        if email != '':
            if not EmailValidator(email):
                form.errors['email'] = (_('%s is not a valid email address') % email,)

        try:
            existing_user = User.objects.get(email=form.data['email'])
        except User.DoesNotExist:
            existing_user = None
        if existing_user and existing_user != user:
            form.errors['email'] = _('The selected e-mail address was invalid.')

        if form.is_valid():
            user.first_name = form.cleaned_data['firstname']
            user.last_name = form.cleaned_data['lastname']
            user.save()
            user.email = form.cleaned_data['email']
            user.save()
            meta.notification_style = form.cleaned_data['notification_style']

            django.forms.models.save_instance(form, meta)

            request.session['django_language'] = user.meta.language

            return HttpResponseRedirect(str(user.get_absolute_url()))
    else:
        form = EditForm(initial={
            'birthday': meta.birthday,
            'gender': meta.gender,
            'username': user.username,
            'firstname': user.first_name,
            'lastname': user.last_name,
            'email': user.email,
            'language': user.meta.language,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'notification_style': meta.notification_style,
        })

    return render(request, 'authentication/edit_user_settings.html', {'form': form, 'the_user': user})


def edit_user_password(request, user_id=None):
    if user_id is not None:
        user = User.objects.get(pk=user_id)
    else:
        user = request.user

    if user != request.user and not request.user.is_superuser:
        return HttpResponseRedirect('/')

    class EditForm(django.forms.Form):
        new_password = django.forms.CharField(label=_('Password'), widget=django.forms.PasswordInput, required=False, help_text=_('Your new password'))
        confirm = django.forms.CharField(label=_('Confirm password'), widget=django.forms.PasswordInput, required=False, help_text=_('Confirm your new password'))
        old_password = django.forms.CharField(label=_('Old password'), widget=django.forms.PasswordInput, help_text=_('Confirm your identity'))

    if request.POST:
        form = EditForm(request.POST)
        if not user.check_password(form.data['old_password']):
            form.errors['old_password'] = (_('Incorrect password'),)

        if form.data['new_password'] != form.data['confirm'] and form.data['confirm'] != '':
            form.errors['confirm'] = (_('Passwords did not match.'),)

        if form.is_valid():
            if form.cleaned_data['confirm'] != '':
                user.set_password(form.cleaned_data['new_password'])
            user.save()

            return HttpResponseRedirect(str(user.get_absolute_url()))
    else:
        form = EditForm(initial={})

    return render(request, 'authentication/edit_user_password.html', {'form': form, 'the_user': user})

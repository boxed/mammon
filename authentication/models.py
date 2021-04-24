from django.db import models
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _


class Detail(models.Model):
    owner_user = models.ForeignKey(User, blank=True, null=True, related_name='user_details', verbose_name=_('User'), on_delete=models.CASCADE)
    owner_group = models.ForeignKey(Group, blank=True, null=True, related_name='group_details', verbose_name=_('Group'), on_delete=models.CASCADE)
    name = models.CharField(max_length=1024, verbose_name=_('Name'))
    value = models.TextField(blank=True, verbose_name=_('Value'))

    def __str__(self):
        if self.owner_user:
            return f'{str(self.owner_user)} {self.name}={self.value}'
        else:
            return f'{str(self.owner_group)} {self.name}={self.value}'

    class Admin:
        search_fields = ['user__username']

    class Meta:
        verbose_name = _('detail')
        verbose_name_plural = _('Details')
        ordering = ('id',)


class MetaUser(models.Model):
    Gender_Choices = (
        ('M', _('Male')),
        ('F', _('Female')),
    )

    NotificationStyle_Choices = (
        ('D', _('Default')),
        ('E', _('On every event')),
    )

    user = models.OneToOneField(User, primary_key=True, related_name='meta', verbose_name=_('User'), on_delete=models.CASCADE)
    birthday = models.DateField(blank=True, null=True, verbose_name=_('Birthday'))
    picture = models.ImageField(upload_to='user-pictures', blank=True, verbose_name=_('Picture'))
    gender = models.CharField(verbose_name=_('Gender'), choices=Gender_Choices, max_length=10)
    location = models.CharField(verbose_name=_('Location'), max_length=200)
    inviter = models.ForeignKey(User, blank=True, null=True, related_name='invites', verbose_name=_('Inviter'), on_delete=models.CASCADE)
    friends = models.ForeignKey(Group, related_name='friends_of', blank=True, null=True, verbose_name=_('Friends'), on_delete=models.CASCADE)
    language = models.CharField(verbose_name=_('Language'), max_length=10)
    deleted_by = models.ForeignKey(User, blank=True, null=True, default=None, related_name='deleted_users', verbose_name=_('Deleted by'), on_delete=models.CASCADE)
    deletion_time = models.DateTimeField(blank=True, null=True, verbose_name=_('Deletion time'))
    last_notification_email_time = models.DateTimeField(blank=True, null=True, verbose_name=_('Notification e-mail time'))
    notification_style = models.CharField(verbose_name=_('Notification Style'), choices=NotificationStyle_Choices, max_length=10, default='D')

    def __str__(self):
        return str(self.user)

    class Admin:
        search_fields = ['user__username']

    class Meta:
        verbose_name = _('meta user')
        verbose_name_plural = _('meta users')

from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _


class ForgotPassword(models.Model):
    user = models.ForeignKey(User)
    password = models.CharField(max_length=32, db_index=True, verbose_name=_('Password'))
    creation_time = models.DateTimeField(auto_now_add=True, verbose_name=_('Creation time'))
    created_from = models.CharField(max_length=1024, verbose_name=_('Created from'))
    
    def __unicode__(self):
        return self.user
        
    class Admin:
        pass
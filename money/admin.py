from django.contrib import admin
from mammon.money.models import *

admin.site.register(Account)
admin.site.register(Category)
admin.site.register(Transaction)
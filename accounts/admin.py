# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from accounts.models import User, UserStrategy, Strategy

# Register your models here.
admin.site.register(User)
admin.site.register(UserStrategy)
admin.site.register(Strategy)



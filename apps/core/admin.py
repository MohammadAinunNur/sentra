from django.contrib import admin

from .models import Keyword, Topic, Unit

admin.site.register(Unit)
admin.site.register(Topic)
admin.site.register(Keyword)
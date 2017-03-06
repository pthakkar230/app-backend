from django.contrib import admin

from .models import Action


@admin.register(Action)
class ActionAdmin(admin.ModelAdmin):
    list_display = ('action', 'user', 'path')
    list_filter = ('user', 'action', 'state')

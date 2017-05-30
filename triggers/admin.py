from django.contrib import admin

from .models import Trigger


@admin.register(Trigger)
class TriggerAdmin(admin.ModelAdmin):
    list_fields = ('id', 'cause', 'effect', 'user')
    list_filter = ('user',)

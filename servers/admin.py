from django.contrib import admin

from .models import EnvironmentResource


@admin.register(EnvironmentResource)
class EnvironmentResourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'cpu', 'memory', 'active')
    list_filter = ('active',)

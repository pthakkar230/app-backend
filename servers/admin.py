from django.contrib import admin

from .models import EnvironmentType


@admin.register(EnvironmentType)
class EnvironmentTypeAdmin(admin.ModelAdmin):
    pass

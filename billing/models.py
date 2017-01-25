from django.contrib.postgres.fields import JSONField
from django.db import models

from base.models import HashIDMixin


class BillingAddress(HashIDMixin, models.Model):
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    state_province = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=11)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    class Meta:
        db_table = 'billing_address'


class BillingPlan(HashIDMixin, models.Model):
    name = models.CharField(max_length=50, blank=True, null=True)
    description = models.CharField(max_length=400, blank=True, null=True)
    settings = JSONField(blank=True, null=True)
    cost = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)

    class Meta:
        db_table = 'billing_plan'

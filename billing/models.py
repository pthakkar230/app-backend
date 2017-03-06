from decimal import Decimal
from django.contrib.postgres.fields import JSONField
from django.db import models


class BillingAddress(models.Model):
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    state_province = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=11)
    created_at = models.DateTimeField(auto_now_add=True)


class BillingPlan(models.Model):
    name = models.CharField(max_length=50, blank=True, null=True)
    description = models.CharField(max_length=400, blank=True)
    settings = JSONField(default={})
    cost = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal(0.0))

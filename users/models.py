from pathlib import Path

from django.conf import settings
from django.contrib.postgres.fields import ArrayField, JSONField
from django.db import models
from django.utils.functional import cached_property

from base.models import HashIDMixin
from utils import encode_id


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, primary_key=True, related_name='profile')
    avatar_url = models.CharField(max_length=100, blank=True, null=True)
    bio = models.CharField(max_length=400, blank=True, null=True)
    url = models.CharField(max_length=200, blank=True, null=True)
    email_confirmed = models.BooleanField(default=False)
    confirmed_at = models.DateTimeField(blank=True, null=True)
    location = models.CharField(max_length=120, blank=True, null=True)
    company = models.CharField(max_length=255, blank=True, null=True)
    billing_address = models.OneToOneField('billing.BillingAddress', blank=True, null=True)
    billing_plan = models.OneToOneField('billing.BillingPlan', blank=True, null=True)
    current_login_ip = models.CharField(max_length=20, blank=True, null=True)
    last_login_at = models.DateTimeField(blank=True, null=True)
    last_login_ip = models.CharField(max_length=20, blank=True, null=True)
    login_count = models.IntegerField(blank=True, null=True)
    timezone = models.CharField(db_column='Timezone', max_length=20, blank=True, null=True)

    def resource_root(self):
        return Path(settings.RESOURCE_DIR, self.user.username)

    def ssh_public_key(self):
        key_path = self.resource_root().joinpath('.ssh', 'id_rsa.pub')
        if key_path.exists():
            return key_path.read_text()
        return ''

    @cached_property
    def hashid(self):
        return encode_id(self.user_id)


class Email(models.Model):
    address = models.CharField(max_length=255, primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='emails', null=True)
    public = models.BooleanField(default=False)
    unsubscribed = models.BooleanField(default=True)

    class Meta:
        db_table = 'email'


class Integration(HashIDMixin, models.Model):
    GITHUB = 'github'
    S3 = 's3'
    GOOGLE = 'google'

    PROVIDERS = (
        (GITHUB, "GitHub"),
        (S3, "Amazon S3"),
        (GOOGLE, "Google Drive")
    )

    FIELDS = {
        GITHUB: [
            {'name': 'branch', 'verbose_name': 'GitHub branch', 'validators': ['path_exists'],
             'helper': 'Default branch is master'},
        ]
    }

    ACCESS_TOKEN_CACHE_KEY_FORMAT = '{provider}_{integration_id}_access_token'
    REFRESH_TOKEN_CACHE_KEY_FORMAT = '{provider}_{integration_id}_refresh_token'

    integration_id = models.CharField(max_length=64)
    integration_email = models.CharField(max_length=255)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='integrations', null=True)
    scopes = ArrayField(models.CharField(max_length=255), blank=True, null=True)
    provider = models.CharField(max_length=255)
    settings = JSONField(blank=True, null=True)

    class Meta:
        db_table = 'integration'

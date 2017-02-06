# -*- coding: utf-8 -*-
# Generated by Django 1.10.6.dev20170130203940 on 2017-01-31 15:37
from __future__ import unicode_literals

import django.contrib.contenttypes.models
from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ContentType',
            fields=[
                ('app_label', models.CharField(max_length=100)),
                ('model', models.CharField(max_length=100, verbose_name='python model class name')),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
            ],
            options={
                'verbose_name': 'content type',
                'verbose_name_plural': 'content types',
                'db_table': 'django_content_type',
            },
            managers=[
                ('objects', django.contrib.contenttypes.models.ContentTypeManager()),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='contenttype',
            unique_together=set([('app_label', 'model')]),
        ),
    ]
# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-01-20 17:25
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_auto_20170116_1556'),
    ]

    state_operations = [
        migrations.RemoveField(
            model_name='email',
            name='id',
        ),
        migrations.AlterField(
            model_name='email',
            name='address',
            field=models.CharField(max_length=255, primary_key=True, serialize=False),
        ),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(state_operations=state_operations)
    ]

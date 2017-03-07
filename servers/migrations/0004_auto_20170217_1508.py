# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-17 15:08
from __future__ import unicode_literals

from django.db import migrations


def move_models_config(apps, schema_editor):
    Model = apps.get_model("servers", "Model")
    for model in Model.objects.select_related('server'):
        model.server.config['script'] = model.script
        model.server.config['method'] = model.method
        model.save()


def move_jobs_config(apps, schema_editor):
    Job = apps.get_model("servers", "Job")
    for job in Job.objects.select_related('server'):
        job.server.auto_restart = job.auto_restart
        job.server.config['script'] = job.script
        job.server.config['method'] = job.method
        job.server.config['schedule'] = job.schedule
        job.save()


class Migration(migrations.Migration):

    dependencies = [
        ('servers', '0003_auto_20170217_1508'),
    ]

    operations = [
        migrations.RunPython(move_models_config, migrations.RunPython.noop),
        migrations.RunPython(move_models_config, migrations.RunPython.noop)
    ]
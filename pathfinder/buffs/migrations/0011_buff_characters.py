# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-03-09 16:20
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('buffs', '0010_auto_20160309_1612'),
    ]

    operations = [
        migrations.AddField(
            model_name='buff',
            name='characters',
            field=models.ManyToManyField(to='buffs.Character'),
        ),
    ]

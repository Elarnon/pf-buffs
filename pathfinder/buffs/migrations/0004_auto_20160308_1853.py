# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-03-08 18:53
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('buffs', '0003_auto_20160308_1853'),
    ]

    operations = [
        migrations.CreateModel(
            name='ConstrainedStat',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name_fr', models.CharField(blank=True, max_length=255, verbose_name='Nom (FR)')),
            ],
        ),
        migrations.AlterField(
            model_name='stat',
            name='name_fr',
            field=models.CharField(max_length=255, verbose_name='Nom (FR)'),
        ),
        migrations.AddField(
            model_name='constrainedstat',
            name='stat',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='buffs.Stat'),
        ),
        migrations.AlterUniqueTogether(
            name='constrainedstat',
            unique_together=set([('stat', 'name_fr')]),
        ),
    ]

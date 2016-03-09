# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-03-08 23:56
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('buffs', '0001_squashed_0008_auto_20160308_2331'),
    ]

    operations = [
        migrations.CreateModel(
            name='Buff',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('duration', models.IntegerField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Constraint',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name_fr', models.CharField(blank=True, max_length=255, verbose_name='Nom (FR)')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='constrainedstat',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='constrainedstat',
            name='stat',
        ),
        migrations.RemoveField(
            model_name='effect',
            name='group',
        ),
        migrations.RemoveField(
            model_name='effect',
            name='source',
        ),
        migrations.RemoveField(
            model_name='group',
            name='effects',
        ),
        migrations.RemoveField(
            model_name='source',
            name='stats',
        ),
        migrations.AlterField(
            model_name='bonus',
            name='stat',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='buffs.Stat', verbose_name='Attribut modifié'),
        ),
        migrations.DeleteModel(
            name='ConstrainedStat',
        ),
        migrations.DeleteModel(
            name='Effect',
        ),
        migrations.AddField(
            model_name='buff',
            name='group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='buffs.Group'),
        ),
        migrations.AddField(
            model_name='buff',
            name='source',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='buffs.Source'),
        ),
        migrations.AddField(
            model_name='bonus',
            name='constraint',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='buffs.Constraint', verbose_name='Contrainte'),
        ),
        migrations.AddField(
            model_name='group',
            name='sources',
            field=models.ManyToManyField(through='buffs.Buff', to='buffs.Source'),
        ),
    ]

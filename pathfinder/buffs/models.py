from django.db import models

class BuffType(models.Model):
    name_fr = models.CharField()
    stacks = models.BooleanField(default=False)

class Stat(models.Model):
    name_fr = models.CharField()

class Source(models.Model):
    name = models.CharField()
    stats = models.ManyToManyField(Stat, through='Buff')

class Buff(models.Model):
    source = models.ForeignKey(Source)
    stat = models.ForeignKey(Stat)
    type_ = models.ForeignKey(BuffType)
    value = models.IntegerField()


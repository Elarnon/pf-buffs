from django.db import models

from django.db.models import Case, When, Max, Sum, F

from django.utils.safestring import mark_safe

from .utils import make_stats

class BonusType(models.Model):
    name_fr = models.CharField(max_length=255, verbose_name="Nom (FR)", blank=True, null=False)
    name_en = models.CharField(max_length=255, verbose_name="Nom (EN)", unique=True, blank=False, null=False)
    stacks = models.BooleanField(default=False)

    def __str__(self):
        if self.stacks:
            return '{} ({}, stacks)'.format(self.name_fr, self.name_en)
        return '{} ({})'.format(self.name_fr, self.name_en)

class Stat(models.Model):
    name_fr = models.CharField(max_length=255, verbose_name="Nom (FR)", blank=False, null=False)

    def __str__(self):
        return self.name_fr

class Constraint(models.Model):
    name_fr = models.CharField(max_length=255, verbose_name="Nom (FR)", blank=True, null=False)

    def __str__(self):
        return self.name_fr

class Source(models.Model):
    name_fr = models.CharField(max_length=255, verbose_name="Nom (FR)")
    author = models.ForeignKey('Character', blank=True, null=True, verbose_name="Auteur")
    level_dependent = models.BooleanField(default=False, verbose_name="Dépend du niveau")
    stats = models.ManyToManyField(Stat, through='Bonus')


    def make_stats(self, sources):
        return make_stats([sources[self.pk]])

    def __str__(self):
        return self.name_fr + (' [{}]'.format(self.author.name) if self.author else '')

class Bonus(models.Model):
    source = models.ForeignKey(Source)
    stat = models.ForeignKey(Stat, verbose_name="Attribut modifié")
    constraint = models.ForeignKey(Constraint, verbose_name="Contrainte", null=True, blank=True)
    typ = models.ForeignKey(BonusType, verbose_name="Type de bonus", null=True, blank=True)
    value = models.IntegerField(verbose_name="Valeur")

    class Meta:
        unique_together = [
            ('source', 'typ', 'stat', 'constraint'),
        ]

    def __str__(self):
        return ' '.join([
            '{:+}'.format(self.value),
            '{}'.format(self.stat),
            '[{}]'.format(self.typ.name_fr) if self.typ else '',
            '{}'.format(self.constraint) if self.constraint else ''
        ])

class Character(models.Model):
    name = models.CharField(max_length=255)
    undead = models.BooleanField(default=False)
    players = models.ManyToManyField('auth.User', blank=True)

    def __str__(self):
        return self.name + (" (mort-vivant)" if self.undead else "")

    def buffs(self):
        return [buff.source for buff in self.buff_set.all() if buff.active]

    def make_stats(self, sources):
        fn = None
        if self.undead:
            fn = lambda typ: typ['name'] != 'Moral'
        my_sources = [
            v
            for k, v in sources.items()
            if k in {buff.source_id for buff in self.buff_set.all() if buff.active}
        ]
        return make_stats(my_sources, fn)

    def end_turn(self):
        Buff.objects.filter(active=True, source__author=self, duration__lte=0).update(active=False)
        Buff.objects.filter(active=True, source__author=self, duration__gt=0).update(duration=F('duration')-1)

class Buff(models.Model):
    characters = models.ManyToManyField(Character)
    source = models.ForeignKey(Source)
    duration = models.IntegerField(null=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return "{} sur {} ({} tours)".format(self.source, ', '.join(map(str, self.characters.all())), self.duration)

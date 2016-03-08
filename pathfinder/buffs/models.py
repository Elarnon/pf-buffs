from django.db import models

from django.db.models import Case, When, Max, Sum, F

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

class ConstrainedStat(models.Model):
    name_fr = models.CharField(max_length=255, verbose_name="Nom (FR)", blank=True, null=False)
    stat = models.ForeignKey(Stat)

    class Meta:
        unique_together = (
            ('stat', 'name_fr'),
        )

    def __str__(self):
        return '{} {}'.format(self.stat, self.name_fr)

class Source(models.Model):
    name_fr = models.CharField(max_length=255, verbose_name="Nom (FR)")
    stats = models.ManyToManyField(ConstrainedStat, through='Bonus')
    author = models.ForeignKey('Character', blank=True, null=True, verbose_name="Auteur")
    level_dependent = models.BooleanField(default=False, verbose_name="Dépend du niveau")

    def __str__(self):
        return self.name_fr

class Bonus(models.Model):
    source = models.ForeignKey(Source)
    stat = models.ForeignKey(ConstrainedStat, verbose_name="Attribut modifié")
    typ = models.ForeignKey(BonusType, verbose_name="Type de bonus")
    value = models.IntegerField(verbose_name="Valeur")

class Character(models.Model):
    name = models.CharField(max_length=255)
    sources = models.ManyToManyField(Source, through='Buff')
    undead = models.BooleanField(default=False)

    def __str__(self):
        return self.name + (" (undead)" if self.undead else "")

    def stats(self):
        grid = self.buff_set.values(
            "source__bonus__stat", "source__bonus__typ").annotate(
            value=Case(
                When(source__bonus__typ__stacks=True, then=Sum("source__bonus__value")),
                default=Max("source__bonus__value")),
            stat=F("source__bonus__stat__stat__name_fr"),
            stat_id=F("source__bonus__stat__stat"),
            constraint=F("source__bonus__stat__name_fr"),
            constraint_id=F("source__bonus__stat"),
            typ=F("source__bonus__typ__name_fr")).values(
            "value", "stat", "stat_id", "constraint", "constraint_id", "typ")

        stats = {}
        for elt in grid:
            # FIXME: Lolwut
            if self.undead and elt['typ'] == 'Moral':
                continue
            stat_id = elt['stat_id']
            if stat_id not in stats:
                stats[stat_id] = { 'name': elt['stat'], 'value': 0, 'typs': {}, 'constraints': {} }
            stat = stats[stat_id]

            if elt['constraint'] is '':
                stat['value'] += elt['value']
                assert(elt['typ'] not in stat['typs'])
                stat['typs'][elt['typ']] = elt
            else:
                constraints = stat['constraints']
                constraint = elt['constraint_id']
                if constraint not in constraints:
                    constraints[constraint] = { 'name': elt['constraint'], 'typs': {} }
                assert(elt['typ'] not in constraints[constraint]['typs'])
                constraints[constraint]['typs'][elt['typ']] = elt

        for stat in stats.values():
            remove_constraint = set()
            for cid, constraint in stat['constraints'].items():
                toremove = set()
                for tid, typ in constraint['typs'].items():
                    if tid in stat['typs'] and stat['typs'][tid]['value'] >= typ['value']:
                        toremove.add(tid)
                    else:
                        typ['value'] -= stat['typs'][tid]['value']
                for tid in toremove:
                    del constraint['typs'][tid]
                if len(constraint['typs']) == 0:
                    remove_constraint.add(cid)
            for cid in remove_constraint:
                del stat['constraints'][cid]

        return [
            (stat['name'], '{:+}'.format(stat['value']),
            '; '.join(
                ' '.join('{:+} [{}]'.format(elt['value'], elt['typ']) for elt in constraint['typs'].values())
                + ' ' + constraint['name']
                for constraint in stat['constraints'].values()
            ))
            for stat in stats.values()
        ]

class Buff(models.Model):
    character = models.ForeignKey(Character)
    source = models.ForeignKey(Source)
    duration = models.IntegerField(null=True)

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

class Constraint(models.Model):
    name_fr = models.CharField(max_length=255, verbose_name="Nom (FR)", blank=True, null=False)

    def __str__(self):
        return self.name_fr

class Source(models.Model):
    name_fr = models.CharField(max_length=255, verbose_name="Nom (FR)")
    author = models.ForeignKey('Character', blank=True, null=True, verbose_name="Auteur")
    level_dependent = models.BooleanField(default=False, verbose_name="Dépend du niveau")
    stats = models.ManyToManyField(Stat, through='Bonus')

    def __str__(self):
        return self.name_fr + (' [{}]'.format(self.author) if self.author else '')

class Bonus(models.Model):
    source = models.ForeignKey(Source)
    stat = models.ForeignKey(Stat, verbose_name="Attribut modifié")
    constraint = models.ForeignKey(Constraint, verbose_name="Contrainte", null=True, blank=True)
    typ = models.ForeignKey(BonusType, verbose_name="Type de bonus")
    value = models.IntegerField(verbose_name="Valeur")

    class Meta:
        unique_together = [
            ('source', 'typ', 'stat', 'constraint'),
        ]

class Character(models.Model):
    name = models.CharField(max_length=255)
    undead = models.BooleanField(default=False)
    players = models.ManyToManyField('auth.User', blank=True)

    def __str__(self):
        return self.name + (" (undead)" if self.undead else "")

    def buffs(self):
        return Source.objects.filter(buff__active=True, buff__group__in=self.group_set.all())

    def stats(self):
        grid = self.group_set.filter(buff__active=True).values(
            "source__bonus__stat", "source__bonus__constraint", "source__bonus__typ").annotate(
            bonus=Case(
                When(source__bonus__typ__stacks=True, then=Sum(
                    Case(
                        When(source__bonus__value__gte=0, then=F("source__bonus__value")),
                        default=0))),
                default=Max(
                    Case(
                        When(source__bonus__value__gte=0, then=F("source__bonus__value")),
                        default=0))),
            malus=Sum(
                Case(
                    When(source__bonus__value__lt=0, then=F("source__bonus__value")),
                    default=0)),
            stat=F("source__bonus__stat__name_fr"),
            stat_id=F("source__bonus__stat"),
            constraint=F("source__bonus__constraint__name_fr"),
            constraint_id=F("source__bonus__constraint"),
            typ=F("source__bonus__typ__name_fr")).values(
            "bonus", "malus", "stat", "stat_id", "constraint", "constraint_id", "typ")

        stats = {}
        for elt in grid:
            # FIXME: Lolwut
            if self.undead and elt['typ'] == 'Moral':
                continue
            stat_id = elt['stat_id']
            if stat_id not in stats:
                stats[stat_id] = { 'name': elt['stat'], 'bonus': 0, 'malus': 0, 'typs': {}, 'constraints': {} }
            stat = stats[stat_id]

            if elt['constraint'] is None:
                stat['bonus'] += elt['bonus']
                stat['malus'] += elt['malus']
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
                    if tid not in stat['typs']:
                        continue
                    typ['malus'] += stat['typs'][tid]['malus']
                    if stat['typs'][tid]['bonus'] >= typ['bonus']:
                        typ['bonus'] = 0
                        if typ['malus'] == 0:
                            toremove.add(tid)
                    else:
                        typ['bonus'] -= stat['typs'][tid]['bonus']
                for tid in toremove:
                    del constraint['typs'][tid]
                if len(constraint['typs']) == 0:
                    remove_constraint.add(cid)
            for cid in remove_constraint:
                del stat['constraints'][cid]

        return [
            {
                'name': stat['name'],
                'value':'{:+}'.format(stat['bonus'] + stat['malus']),
                'additional': '; '.join(
                    ' '.join('{:+} [{}]'.format(elt['value'], elt['typ']) for elt in constraint['typs'].values())
                    + ' ' + constraint['name']
                    for constraint in stat['constraints'].values()
                ),
                'detail': ' '.join(
                    '{:+} {}'.format(elt['value'], elt['typ'])
                    for elt in stat['typs'].values()
                ),
            }
            for stat in stats.values()
        ]

class Group(models.Model):
    name = models.CharField(max_length=255)
    characters = models.ManyToManyField(Character)
    source = models.ManyToManyField(Source, through='Buff')

    def __str__(self):
        return self.name

class Buff(models.Model):
    group = models.ForeignKey(Group)
    source = models.ForeignKey(Source)
    duration = models.IntegerField(null=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return "{} sur {} ({} tours)".format(self.source, self.group, self.duration)

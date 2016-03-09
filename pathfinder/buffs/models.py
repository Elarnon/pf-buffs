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

    def description(self):
        return '; '.join(str(bonus) for bonus in self.bonus_set.all())

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
        return self.name + (" (undead)" if self.undead else "")

    def buffs(self):
        return Source.objects.filter(buff__active=True, buff__group__in=self.group_set.all())

    def stats(self, pr=False):
        grid = Buff.objects.filter(source__bonus__isnull=False, active=True, group__in=self.group_set.all()).annotate(
            stacks=F("source__bonus__typ__stacks"),
            source_=F("source__name_fr"),
            typ=F("source__bonus__typ__name_fr"),
            constraint=F("source__bonus__constraint__name_fr"),
            value=F("source__bonus__value"),
            stat=F("source__bonus__stat__name_fr")).values(
            "source_", "stat", "constraint", "value", "typ", "stacks")

        stats = {}
        for elt in grid:
            if self.undead and elt['typ'] == 'Moral':
                continue

            stat_id = elt['stat']
            if stat_id not in stats:
                stats[stat_id] = { 'name': elt['stat'], 'typs': {} }
            stat = stats[stat_id]

            typ_id = elt['typ']
            if typ_id not in stat['typs']:
                if elt['stacks'] is None:
                    elt['stacks'] = True
                stat['typs'][typ_id] = { 'name': elt['typ'], 'stacks': elt['stacks'], 'constraints': { }, 'sources': { } }
            typ = stat['typs'][typ_id]
            constraints = typ['constraints']

            constraint_id = elt['constraint']
            if constraint_id is None:
                sources = typ['sources']
            else:
                if constraint_id not in constraints:
                    constraints[constraint_id] = { 'name': elt['constraint'], 'sources': { } }
                sources = constraints[constraint_id]['sources']

            source_id = elt['source_']
            if source_id not in sources:
                sources[source_id] = { 'name': elt['source_'], 'value': elt['value'] }
            else: # FIXME: This is probably a validation error
                sources[source_id]['value'] = max(elt['value'], sources[source_id]['value'])

        sources = {elt['source_'] for elt in grid}

        stat_values = {}
        for stat in stats.values():
            typed_values = {}
            all_constraints = set()
            for typ in stat['typs'].values():
                unconstrained_value = 0
                for source in sources:
                    value = typ['sources'].get(source, None)
                    value = 0 if value is None else value['value']
                    if typ['stacks']:
                        unconstrained_value += value
                    else:
                        unconstrained_value = max(unconstrained_value, value)
                constrained_values = {}
                for constraint in typ['constraints'].values():
                    constrained_value = 0
                    for source in sources:
                        value = constraint['sources'].get(source, None)
                        if value is None:
                            value = typ['sources'].get(source, None)
                        if value is None:
                            value = 0
                        else:
                            value = value['value']
                        if typ['stacks']:
                            constrained_value += value
                        else:
                            constrained_value = max(constrained_value, value)
                    if constrained_value == unconstrained_value:
                        continue
                    else:
                        all_constraints.add(constraint['name'])
                        constrained_values[constraint['name']] = constrained_value - unconstrained_value
                if unconstrained_value == 0 and len(constraints) == 0:
                    continue
                typed_values[typ['name']] = { 'value': unconstrained_value, 'constraints': constrained_values }
            if len(typed_values) == 0:
                continue
            stat_values[stat['name']] = {
                'value': sum(typed_value['value'] for typed_value in typed_values.values()),
                'constraints': sorted([
                    (k, v)
                    for k, v in [
                        (constraint,
                            sorted([(name, typed_value['constraints'].get(constraint, 0))
                                for name, typed_value in typed_values.items()
                                if constraint in typed_value['constraints']],
                                key=lambda x: x[0]))
                            for constraint in all_constraints
                    ]
                    if len(v) > 0
                ], key=lambda x: x[0]),
                'detail': sorted([(k or '', v['value']) for k, v in typed_values.items() if v['value'] != 0], key=lambda x: x[0])
            }

        if pr:
            print(stat_values)

        return [
            {
                'name': k,
                'value': '{:+}'.format(v['value']) if v['value'] != 0 else None,
                'detail': ' '.join('{:+} {}'.format(detail[1], detail[0] or '') for detail in v['detail']).strip()or None,
                'additional':
                    ' '.join(
                        ' '.join(
                            '{:+} [{}]'.format(x[1], x[0]) if x[0] is not None else '{:+}'.format(x[1]) for x in constraint[1])
                        + ' ' + constraint[0]
                    for constraint in v['constraints'])
            }
                for k, v in stat_values.items()
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

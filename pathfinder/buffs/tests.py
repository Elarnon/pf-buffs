from django.test import TestCase

from .models import Character, Source, Stat, Group, Buff, Bonus, BonusType, Constraint

class SingleStatTests(TestCase):
    def setUp(self):
        self.stat = Stat.objects.create(name_fr='Attaque')
        self.constraint = Constraint.objects.create(name_fr='Constraint')

        self.stacking_type = BonusType.objects.create(name_fr='Stacking', name_en='Stacking', stacks=True)
        self.nonstacking_type = BonusType.objects.create(name_fr='Nonstacking', name_en='Nonstacking', stacks=False)

        self.source1 = Source.objects.create(name_fr='Unconstrained')

        self.source2 = Source.objects.create(name_fr='Constrained')

        self.character =Character.objects.create(name='Character', undead=False)
        self.group = Group.objects.create(name='Group')
        self.group.characters.add(self.character)

    def test_empty_buff(self):
        Buff.objects.create(group=self.group, source=self.source1, duration=1, active=True)

        self.assertEqual(
            self.character.stats(),
            []
        )
    
    def test_unconstrained(self):
        Buff.objects.create(group=self.group, source=self.source1, duration=1, active=True)
       
       # Unconstrained bonuses
        Bonus.objects.create(source=self.source1, stat=self.stat, value=1, typ=self.stacking_type)

        self.assertEqual(
            self.character.stats(),
            [{'detail': '+1 Stacking', 'value': '+1', 'name': 'Attaque', 'additional': ''}]
        )
        
        Bonus.objects.create(source=self.source1, stat=self.stat, value=1, typ=self.nonstacking_type)
        
        self.assertEqual(
            self.character.stats(),
            [{'detail': '+1 Nonstacking +1 Stacking', 'value': '+2', 'name': 'Attaque', 'additional': ''}]
        )

    def test_unconstrained_same_source_dont_stack(self):
        Buff.objects.create(group=self.group, source=self.source1, duration=1, active=True)

        # Stacking bonuses
        b1 = Bonus.objects.create(source=self.source1, stat=self.stat, value=1, typ=self.stacking_type)
        b2 = Bonus.objects.create(source=self.source1, stat=self.stat, value=1, typ=self.stacking_type)

        self.assertEqual(
            self.character.stats(),
            [{'detail': '+1 Stacking', 'value': '+1', 'name': 'Attaque', 'additional': ''}]
        )

        # Nonstacking bonuses
        b1.typ = self.nonstacking_type
        b2.typ = self.nonstacking_type
        b1.save()
        b2.save()
        
        self.assertEqual(
            self.character.stats(),
            [{'detail': '+1 Nonstacking', 'value': '+1', 'name': 'Attaque', 'additional': ''}]
        )
    
    def test_unconstrained_stacking_different_sources_stack(self):
        Buff.objects.create(group=self.group, source=self.source1, duration=1, active=True)
        Buff.objects.create(group=self.group, source=self.source2, duration=1, active=True)

        b1 = Bonus.objects.create(source=self.source1, stat=self.stat, value=1, typ=self.stacking_type)
        b2 = Bonus.objects.create(source=self.source2, stat=self.stat, value=1, typ=self.stacking_type)

        self.assertEqual(
            self.character.stats(),
            [{'detail': '+2 Stacking', 'value': '+2', 'name': 'Attaque', 'additional': ''}]
        )
    
    def test_unconstrained_nonstacking_different_sources_dont_stack(self):
        typ = self.nonstacking_type

        Buff.objects.create(group=self.group, source=self.source1, duration=1, active=True)
        Buff.objects.create(group=self.group, source=self.source2, duration=1, active=True)

        b1 = Bonus.objects.create(source=self.source1, stat=self.stat, value=1, typ=typ)
        b2 = Bonus.objects.create(source=self.source2, stat=self.stat, value=1, typ=typ)

        self.assertEqual(
            self.character.stats(),
            [{'detail': '+1 Nonstacking', 'value': '+1', 'name': 'Attaque', 'additional': ''}]
        )

    def test_unconstrained_constrained_same_source_override(self):
        Buff.objects.create(group=self.group, source=self.source1, duration=1, active=True)

        Bonus.objects.create(source=self.source1, stat=self.stat, value=2, typ=self.stacking_type)
        b = Bonus.objects.create(source=self.source1, stat=self.stat, value=3, typ=self.stacking_type, constraint=self.constraint)

        self.assertEqual(
            self.character.stats(),
            [{'detail': '+2 Stacking', 'value': '+2', 'name': 'Attaque', 'additional': '+1 [Stacking] Constraint'}]
        )

        b.value = 1
        b.save()
        
        self.assertEqual(
            self.character.stats(),
            [{'detail': '+2 Stacking', 'value': '+2', 'name': 'Attaque', 'additional': '-1 [Stacking] Constraint'}]
        )

    def test_constrained(self):
        # Constrained bonuses
        Bonus.objects.create(source=self.source2, stat=self.stat, value=10, typ=self.stacking_type, constraint=self.constraint)
        Bonus.objects.create(source=self.source2, stat=self.stat, value=10, typ=self.nonstacking_type, constraint=self.constraint)

        Buff.objects.create(group=self.group, source=self.source2, duration=1, active=True)

        self.assertEqual(
            self.character.stats(),
            [{'detail': None, 'value': None, 'name': 'Attaque', 'additional': '+10 [Nonstacking] +10 [Stacking] Constraint'}]
        )

        # No stacking from the same source
        Buff.objects.create(group=self.group, source=self.source2, duration=1, active=True)

        self.assertEqual(
            self.character.stats(),
            [{'detail': None, 'value': None, 'name': 'Attaque', 'additional': '+10 [Nonstacking] +10 [Stacking] Constraint'}]
        )

    def test_unconstrained_constrained_same_source(self):
        Bonus.objects.create(source=self.source1, stat=self.stat, value=1, typ=self.stacking_type)
        Bonus.objects.create(source=self.source1, stat=self.stat, value=10, typ=self.stacking_type, constraint=self.constraint)
        Bonus.objects.create(source=self.source1, stat=self.stat, value=1, typ=self.nonstacking_type)
        Bonus.objects.create(source=self.source1, stat=self.stat, value=10, typ=self.nonstacking_type, constraint=self.constraint)

        Buff.objects.create(group=self.group, source=self.source1, duration=1, active=True)

        self.assertEqual(self.character.stats(),
            [{'additional': '+9 [Nonstacking] +9 [Stacking] Constraint', 'detail': '+1 Nonstacking +1 Stacking', 'name': 'Attaque', 'value': '+2'}]
        )

    def test_ignore_small_constraints(self):
        Bonus.objects.create(source=self.source1, stat=self.stat, value=1, typ=self.stacking_type)
        Bonus.objects.create(source=self.source1, stat=self.stat, value=1, typ=self.stacking_type, constraint=self.constraint)
        
        Buff.objects.create(group=self.group, source=self.source1, duration=1, active=True)

        self.assertEqual(self.character.stats(),
            [{'additional': '', 'detail': '+1 Stacking', 'name': 'Attaque', 'value': '+1'}]
        )

    def test_ignore_inactive(self):
        Bonus.objects.create(source=self.source1, stat=self.stat, value=1, typ=self.stacking_type)
        
        buff = Buff.objects.create(group=self.group, source=self.source1, duration=1, active=True)

        self.assertEqual(self.character.stats(),
            [{'additional': '', 'detail': '+1 Stacking', 'name': 'Attaque', 'value': '+1'}]
        )

        buff.active = False
        buff.save()

        self.assertEqual(self.character.stats(),
            []
        )
        
        Buff.objects.create(group=self.group, source=self.source1, duration=1, active=True)

        self.assertEqual(self.character.stats(),
            [{'additional': '', 'detail': '+1 Stacking', 'name': 'Attaque', 'value': '+1'}]
        )

    def test_untyped(self):
        Bonus.objects.create(source=self.source1, stat=self.stat, value=1)
        Buff.objects.create(group=self.group, source=self.source1, duration=1, active=True)

        self.assertEqual(self.character.stats(),
            [{'additional': '', 'detail': '+1', 'name': 'Attaque', 'value': '+1'}]
        )
        
        Bonus.objects.create(source=self.source1, stat=self.stat, value=1, constraint=self.constraint)
        self.assertEqual(self.character.stats(),
            [{'additional': '', 'detail': '+1', 'name': 'Attaque', 'value': '+1'}]
        )

    def test_malus(self):
        Bonus.objects.create(source=self.source1, stat=self.stat, value=-1)
        Buff.objects.create(group=self.group, source=self.source1, duration=1, active=True)
        
        self.assertEqual(self.character.stats(),
            [{'additional': '', 'detail': '-1', 'name': 'Attaque', 'value': '-1'}]
        )
        
        Buff.objects.create(group=self.group, source=self.source2, duration=1, active=True)
        Bonus.objects.create(source=self.source2, stat=self.stat, value=1)

        self.assertEqual(self.character.stats(),
            []
        )

    def test_nonstacking_constraint(self):
        # Source 1 gives +1 Nonstacking and +1 additional Nonstacking Constraint
        Bonus.objects.create(source=self.source1, stat=self.stat, value=1, typ=self.nonstacking_type)
        constrained = Bonus.objects.create(source=self.source1, stat=self.stat, value=2, typ=self.nonstacking_type, constraint=self.constraint)
        # Source 2 gives +3 Nonstacking
        Bonus.objects.create(source=self.source2, stat=self.stat, value=3, typ=self.nonstacking_type)

        Buff.objects.create(group=self.group, source=self.source1, duration=1, active=True)
        Buff.objects.create(group=self.group, source=self.source2, duration=1, active=True)

        self.assertEqual(self.character.stats(),
            [{'additional': '', 'detail': '+3 Nonstacking', 'name': 'Attaque', 'value': '+3'}]
        )

        # Now Source 1 gives +4 total for Nonstacking Constraint
        constrained.value = 4
        constrained.save()
        
        self.assertEqual(self.character.stats(),
            [{'additional': '+1 [Nonstacking] Constraint', 'detail': '+3 Nonstacking', 'name': 'Attaque', 'value': '+3'}]
        )
    
    def test_stacking_constraint(self):
        # Source 1 gives +1 stacking and +1 additional stacking Constraint
        Bonus.objects.create(source=self.source1, stat=self.stat, value=1, typ=self.stacking_type)
        constrained = Bonus.objects.create(source=self.source1, stat=self.stat, value=2, typ=self.stacking_type, constraint=self.constraint)
        # Source 2 gives +3 stacking
        Bonus.objects.create(source=self.source2, stat=self.stat, value=3, typ=self.stacking_type)

        Buff.objects.create(group=self.group, source=self.source1, duration=1, active=True)
        Buff.objects.create(group=self.group, source=self.source2, duration=1, active=True)

        self.assertEqual(self.character.stats(),
            [{'additional': '+1 [Stacking] Constraint', 'detail': '+4 Stacking', 'name': 'Attaque', 'value': '+4'}]
        )

        # Now Source 1 gives +3 additional for stacking Constraint
        constrained.value = 4
        constrained.save()
        
        self.assertEqual(self.character.stats(),
            [{'additional': '+3 [Stacking] Constraint', 'detail': '+4 Stacking', 'name': 'Attaque', 'value': '+4'}]
        )

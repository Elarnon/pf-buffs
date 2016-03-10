from django.test import TestCase

from .models import Character, Source, Stat, Buff, Bonus, BonusType, Constraint, build_stats

def get_stats(character):
    return character.make_stats(build_stats(Source.objects.select_related('author')))

class SingleStatTests(TestCase):
    def setUp(self):
        self.stat = Stat.objects.create(name_fr='Attaque')
        self.constraint = Constraint.objects.create(name_fr='Constraint')

        self.stacking_type = BonusType.objects.create(name_fr='Stacking', name_en='Stacking', stacks=True)
        self.nonstacking_type = BonusType.objects.create(name_fr='Nonstacking', name_en='Nonstacking', stacks=False)

        self.source1 = Source.objects.create(name_fr='Unconstrained')

        self.source2 = Source.objects.create(name_fr='Constrained')

        self.character =Character.objects.create(name='Character', undead=False)

    def test_empty_buff(self):
        Buff.objects.create(source=self.source1, duration=1, active=True).characters.add(self.character)

        self.assertEqual(
            get_stats(self.character),
            {}
        )
    
    def test_unconstrained(self):
        Buff.objects.create(source=self.source1, duration=1, active=True).characters.add(self.character)
       
       # Unconstrained bonuses
        Bonus.objects.create(source=self.source1, stat=self.stat, value=1, typ=self.stacking_type)

        self.assertEqual(
            get_stats(self.character),
            {'Attaque': {'detail': [('Stacking', 1)], 'value': 1, 'constraints': []}})
        
        Bonus.objects.create(source=self.source1, stat=self.stat, value=1, typ=self.nonstacking_type)
        
        self.assertEqual(
            get_stats(self.character),
            {'Attaque': {'detail': [('Nonstacking', 1), ('Stacking', 1)], 'value': 2, 'constraints': []}})

    def test_unconstrained_same_source_dont_stack(self):
        Buff.objects.create(source=self.source1, duration=1, active=True).characters.add(self.character)

        # Stacking bonuses
        b1 = Bonus.objects.create(source=self.source1, stat=self.stat, value=1, typ=self.stacking_type)
        b2 = Bonus.objects.create(source=self.source1, stat=self.stat, value=1, typ=self.stacking_type)

        self.assertEqual(
            get_stats(self.character),
            {'Attaque': {'detail': [('Stacking', 1)], 'value': 1, 'constraints': []}})

        # Nonstacking bonuses
        b1.typ = self.nonstacking_type
        b2.typ = self.nonstacking_type
        b1.save()
        b2.save()
        
        self.assertEqual(
            get_stats(self.character),
            {'Attaque': {'detail': [('Nonstacking', 1)], 'value': 1, 'constraints': []}})
    
    def test_unconstrained_stacking_different_sources_stack(self):
        Buff.objects.create(source=self.source1, duration=1, active=True).characters.add(self.character)
        Buff.objects.create(source=self.source2, duration=1, active=True).characters.add(self.character)

        b1 = Bonus.objects.create(source=self.source1, stat=self.stat, value=1, typ=self.stacking_type)
        b2 = Bonus.objects.create(source=self.source2, stat=self.stat, value=1, typ=self.stacking_type)

        self.assertEqual(
            get_stats(self.character),
            {'Attaque': {'detail': [('Stacking', 2)], 'value': 2, 'constraints': []}})
    
    def test_unconstrained_nonstacking_different_sources_dont_stack(self):
        typ = self.nonstacking_type

        Buff.objects.create(source=self.source1, duration=1, active=True).characters.add(self.character)
        Buff.objects.create(source=self.source2, duration=1, active=True).characters.add(self.character)

        b1 = Bonus.objects.create(source=self.source1, stat=self.stat, value=1, typ=typ)
        b2 = Bonus.objects.create(source=self.source2, stat=self.stat, value=1, typ=typ)

        self.assertEqual(
            get_stats(self.character),
            {'Attaque': {'detail': [('Nonstacking', 1)], 'value': 1, 'constraints': []}})

    def test_unconstrained_constrained_same_source_override(self):
        Buff.objects.create(source=self.source1, duration=1, active=True).characters.add(self.character)

        Bonus.objects.create(source=self.source1, stat=self.stat, value=2, typ=self.stacking_type)
        b = Bonus.objects.create(source=self.source1, stat=self.stat, value=3, typ=self.stacking_type, constraint=self.constraint)

        self.assertEqual(
            get_stats(self.character),
            {'Attaque': {'detail': [('Stacking', 2)], 'value': 2, 'constraints': [('Constraint', [('Stacking', 1)])]}})

        b.value = 1
        b.save()
        
        self.assertEqual(
            get_stats(self.character),
            {'Attaque': {'detail': [('Stacking', 2)], 'value': 2, 'constraints': [('Constraint', [('Stacking', -1)])]}})

    def test_constrained(self):
        # Constrained bonuses
        Bonus.objects.create(source=self.source2, stat=self.stat, value=10, typ=self.stacking_type, constraint=self.constraint)
        Bonus.objects.create(source=self.source2, stat=self.stat, value=10, typ=self.nonstacking_type, constraint=self.constraint)

        Buff.objects.create(source=self.source2, duration=1, active=True).characters.add(self.character)

        self.assertEqual(
            get_stats(self.character),
            {'Attaque': {'detail': [], 'value': 0, 'constraints': [('Constraint', [('Nonstacking', 10), ('Stacking', 10)])]}})

    def test_unconstrained_constrained_same_source(self):
        Bonus.objects.create(source=self.source1, stat=self.stat, value=1, typ=self.stacking_type)
        Bonus.objects.create(source=self.source1, stat=self.stat, value=10, typ=self.stacking_type, constraint=self.constraint)
        Bonus.objects.create(source=self.source1, stat=self.stat, value=1, typ=self.nonstacking_type)
        Bonus.objects.create(source=self.source1, stat=self.stat, value=10, typ=self.nonstacking_type, constraint=self.constraint)

        Buff.objects.create(source=self.source1, duration=1, active=True).characters.add(self.character)

        self.assertEqual(get_stats(self.character),
            {'Attaque': {'detail': [('Nonstacking', 1), ('Stacking', 1)], 'value': 2, 'constraints': [('Constraint', [('Nonstacking', 9), ('Stacking', 9)])]}})

    def test_ignore_small_constraints(self):
        Bonus.objects.create(source=self.source1, stat=self.stat, value=1, typ=self.stacking_type)
        Bonus.objects.create(source=self.source1, stat=self.stat, value=1, typ=self.stacking_type, constraint=self.constraint)
        
        Buff.objects.create(source=self.source1, duration=1, active=True).characters.add(self.character)

        self.assertEqual(get_stats(self.character),
            {'Attaque': {'detail': [('Stacking', 1)], 'value': 1, 'constraints': []}})

    def test_ignore_inactive(self):
        Bonus.objects.create(source=self.source1, stat=self.stat, value=1, typ=self.stacking_type)
        
        buff = Buff.objects.create(source=self.source1, duration=1, active=True)
        buff.characters.add(self.character)

        self.assertEqual(get_stats(self.character),
            {'Attaque': {'detail': [('Stacking', 1)], 'value': 1, 'constraints': []}})

        buff.active = False
        buff.save()

        self.assertEqual(get_stats(self.character),
            {}
        )
        
        Buff.objects.create(source=self.source1, duration=1, active=True).characters.add(self.character)

        self.assertEqual(get_stats(self.character),
            {'Attaque': {'detail': [('Stacking', 1)], 'value': 1, 'constraints': []}})

    def test_untyped(self):
        Bonus.objects.create(source=self.source1, stat=self.stat, value=1)
        Buff.objects.create(source=self.source1, duration=1, active=True).characters.add(self.character)

        self.assertEqual(get_stats(self.character),
                         [{ 'name': 'Attaque', 'value': 1, 'constraints': [], 'detail': [{ 'name': None, 'value': 1 }] }])
        
        Bonus.objects.create(source=self.source1, stat=self.stat, value=1, constraint=self.constraint)
        self.assertEqual(get_stats(self.character),
                         [{ 'name': 'Attaque', 'value': 1, 'constraints': [], 'detail': [{ 'name': None, 'value': 1 }] }])

    def test_malus(self):
        Bonus.objects.create(source=self.source1, stat=self.stat, value=-1)
        Buff.objects.create(source=self.source1, duration=1, active=True).characters.add(self.character)
        
        self.assertEqual(get_stats(self.character),
                         {'Attaque': {'value': -1, 'constraints': [], 'detail': [('', -1)]}})
        
        Buff.objects.create(source=self.source2, duration=1, active=True).characters.add(self.character)
        Bonus.objects.create(source=self.source2, stat=self.stat, value=1)

        self.assertEqual(get_stats(self.character), {})

    def test_nonstacking_constraint(self):
        # Source 1 gives +1 Nonstacking and +1 additional Nonstacking Constraint
        Bonus.objects.create(source=self.source1, stat=self.stat, value=1, typ=self.nonstacking_type)
        constrained = Bonus.objects.create(source=self.source1, stat=self.stat, value=2, typ=self.nonstacking_type, constraint=self.constraint)
        # Source 2 gives +3 Nonstacking
        Bonus.objects.create(source=self.source2, stat=self.stat, value=3, typ=self.nonstacking_type)

        Buff.objects.create(source=self.source1, duration=1, active=True).characters.add(self.character)
        Buff.objects.create(source=self.source2, duration=1, active=True).characters.add(self.character)

        self.assertEqual(get_stats(self.character),
            {'Attaque': {'detail': [('Nonstacking', 3)], 'value': 3, 'constraints': []}})

        # Now Source 1 gives +4 total for Nonstacking Constraint
        constrained.value = 4
        constrained.save()
        
        self.assertEqual(get_stats(self.character),
            {'Attaque': {'detail': [('Nonstacking', 3)], 'value': 3, 'constraints': [('Constraint', [('Nonstacking', 1)])]}})
    
    def test_stacking_constraint(self):
        # Source 1 gives +1 stacking and +1 additional stacking Constraint
        Bonus.objects.create(source=self.source1, stat=self.stat, value=1, typ=self.stacking_type)
        constrained = Bonus.objects.create(source=self.source1, stat=self.stat, value=2, typ=self.stacking_type, constraint=self.constraint)
        # Source 2 gives +3 stacking
        Bonus.objects.create(source=self.source2, stat=self.stat, value=3, typ=self.stacking_type)

        Buff.objects.create(source=self.source1, duration=1, active=True).characters.add(self.character)
        Buff.objects.create(source=self.source2, duration=1, active=True).characters.add(self.character)

        self.assertEqual(get_stats(self.character),
            {'Attaque': {'detail': [('Stacking', 4)], 'value': 4, 'constraints': [('Constraint', [('Stacking', 1)])]}})

        # Now Source 1 gives +3 additional for stacking Constraint
        constrained.value = 4
        constrained.save()
        
        self.assertEqual(get_stats(self.character),
            {'Attaque': {'detail': [('Stacking', 4)], 'value': 4, 'constraints': [('Constraint', [('Stacking', 3)])]}})

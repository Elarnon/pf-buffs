from django import forms

from django.utils.functional import curry
from django.db.models import Q

from .models import Character, Source, Buff

class BuffForm(forms.ModelForm):
    class Meta:
        model = Buff
        fields = ('source', 'characters', 'duration', 'active')
        widgets = {
            'characters': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        sources = kwargs.pop('sources')
        super().__init__(*args, **kwargs)
        self.fields['source'].queryset = sources

class BaseBuffFormSet(forms.BaseModelFormSet):
    def __init__(self, *args, **kwargs):
        character = kwargs.pop('character', None)
        if character is None:
            kwargs['prefix'] = 'buffs-shared-'
        else:
            kwargs['prefix'] = 'buffs-by-{}'.format(character.id)
        super().__init__(*args, **kwargs)
        if character is None:
            sources = Source.objects.filter(Q(author__isnull=True))
        else:
            sources = Source.objects.filter(Q(author=character))
        sources = sources.select_related('author')
        self.queryset = Buff.objects.filter(source__in=sources).select_related('source', 'source__author').order_by('source__name_fr')
        self.form = curry(BuffForm, sources=sources)

from django import forms

from django.utils.functional import curry
from django.db.models import Q

from .models import Character, Source, Buff

class BuffForm(forms.ModelForm):
    class Meta:
        model = Buff
        fields = ('source', 'group', 'duration', 'active')

    def __init__(self, *args, **kwargs):
        sources = kwargs.pop('sources')
        super().__init__(*args, **kwargs)
        self.fields['source'].queryset = sources

class BaseBuffFormSet(forms.BaseModelFormSet):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        sources = Source.objects.filter(Q(author__in=user.character_set.all()) | Q(author__isnull=True))
        self.queryset = Buff.objects.filter(source__in=sources)
        self.form = curry(BuffForm, sources=sources)

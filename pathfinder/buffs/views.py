from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.views.generic import DetailView, ListView
from django.utils.functional import curry

from .models import Character, Buff, Source
from django.db.models import Q

from .forms import BuffForm, BaseBuffFormSet

from django import forms

def test(request):
    if request.method == 'POST':
        formset = BuffFormSet(request.POST, request.FILES)
        if formset.is_valid():
            pass
    else:
        formset = BuffFormSet()

    return render(request, 'buffs/buff_form.html', { 'formset': formset })

class CharacterView(DetailView):
    model = Character

class CharacterListView(ListView):
    model = Character

def index(request):
    characters = Character.objects.all()

    BuffFormSet = forms.modelformset_factory(Buff, fields=('source', 'characters', 'duration', 'active'), formset=BaseBuffFormSet, can_delete=True)

    if request.user.is_authenticated():
        if request.method == 'POST':
            formset = BuffFormSet(request.POST, request.FILES, user=request.user)
            if formset.is_valid():
                formset.save()
                return redirect(reverse('index'))
        else:
            formset = BuffFormSet(user=request.user)
    else:
        formset = None
        
    names = set()
    for character in characters:
        character.cached_stats = {
            stat['name']: stat for stat in character.stats(pr=True)
        }
        names |= character.cached_stats.keys()

    stats = [
        (name, [character.cached_stats.get(name, None) for character in characters])
        for name in sorted(names)
    ]

    buffs = [character.buffs() for character in characters]

    names = set()
    sources = Source.objects.all()
    for source in sources:
        source.cached_stats = {
            stat['name']: stat for stat in source.stats()
        }
        names |= source.cached_stats.keys()

    source_stats = [
        (name, [source.cached_stats.get(name, None) for source in sources])
        for name in sorted(names)
    ]

    return render(request, 'buffs/index.html', {
        'stats': stats,
        'buffs': buffs,
        'characters': characters,
        'buffs_formset': formset,
        'sources': sources,
        'source_stats': source_stats
    })

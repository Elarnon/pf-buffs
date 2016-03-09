from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.views.generic import DetailView, ListView
from django.utils.functional import curry

from django.core.exceptions import ObjectDoesNotExist

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
                if 'end-turn' in request.POST:
                    end_turn = int(request.POST['end-turn'])
                    try:
                        Character.objects.get(pk=end_turn).end_turn()
                    except ObjectDoesNotExist:
                        pass
                return redirect(reverse('index'))
        else:
            formset = BuffFormSet(user=request.user)
    else:
        formset = None

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
        'characters': characters,
        'buffs_formset': formset,
        'sources': sources,
        'source_stats': source_stats
    })

from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.views.generic import DetailView, ListView
from django.utils.functional import curry

from django.core.exceptions import ObjectDoesNotExist

from .models import Character, Buff, Source
from django.db.models import Q

from .forms import BuffForm, BaseBuffFormSet

from .utils import build_stats

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

    sources = Source.objects.select_related('author')
    source_stats = build_stats(sources)

    characters = Character.objects.all().prefetch_related('buff_set', 'players')

    for character in characters:
        character.formatted_stats = character.make_stats(source_stats)
        if character.name == 'Georges':
            print(character.formatted_stats)

    for source in sources:
        source.formatted_stats = source.make_stats(source_stats)

    return render(request, 'buffs/index.html', {
        'characters': characters,
        'buffs_formset': formset,
        'sources': sources,
    })

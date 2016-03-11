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

BuffFormSet = forms.modelformset_factory(Buff, fields=('source', 'characters', 'duration', 'active'), formset=BaseBuffFormSet, can_delete=True)

def index(request):
    if request.method == 'POST' and 'end-turn' in request.POST:
        end_turn = int(request.POST['end-turn'])
        try:
            Character.objects.get(pk=end_turn).end_turn()
            return redirect(reverse('index'))
        except ObjectDoesNotExist:
            pass

    if request.user.is_authenticated():
        managed = request.user.character_set.all()
    else:
        managed = []
    for character in managed:
        assert(request.user.is_authenticated)

        if request.method == 'POST' and request.POST['buff-source'] == str(character.id):
            formset = BuffFormSet(request.POST, request.FILES, character=character)
            if formset.is_valid():
                formset.save()
                return redirect(reverse('index'))
            character.formset = formset
        else:
            character.formset = BuffFormSet(character=character)

    sources = Source.objects.select_related('author')
    source_stats = build_stats(sources)

    characters = Character.objects.all().prefetch_related('buff_set', 'buff_set__source', 'buff_set__source__author', 'players')

    sources = {
        source.id: {
            'name': source.name_fr,
            'link': source.link,
            'author_id': source.author_id,
            'author': source.author.name,
            'level_dependent': source.level_dependent,
            'stats': source.make_stats(source_stats)
        }
        for source in sources
    }

    characters = [
        {
            'stats': character.make_stats(source_stats),
            'id': character.id,
            'name': character.name,
            'buffs': [
                {
                    'duration': buff.duration,
                    'source': sources[buff.source_id]
                }
                for buff in character.buffs()
            ]
        }
        for character in characters
    ]

    return render(request, 'buffs/index.html', {
        'managed_characters': [character.id for character in managed],
        'formsets': [
            {
                'id': character.id,
                'name': character.name,
                'formset': character.formset
            } for character in managed
        ],
        'characters': sorted(characters, key=lambda x: x['name']),
        'sources': sorted(sources.values(), key=lambda x: (x['author'], x['name'])),
    })

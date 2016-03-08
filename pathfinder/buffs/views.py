from django.shortcuts import render
from django.views.generic import DetailView, ListView

from .models import Character

class CharacterView(DetailView):
    model = Character

class CharacterListView(ListView):
    model = Character

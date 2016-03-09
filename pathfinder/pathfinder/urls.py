"""pathfinder URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin

from buffs.views import CharacterView, CharacterListView, test, index

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^character/(?P<pk>[0-9]+)/$', CharacterView.as_view(), name='character-detail'),
    url(r'^character/$', CharacterListView.as_view(), name='character-list'),
    url(r'^buff/$', test),
    url(r'^$', index, name='index'),
]

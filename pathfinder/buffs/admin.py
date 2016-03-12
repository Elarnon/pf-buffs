from django.contrib import admin

from .models import BonusType, Stat, Constraint, Source, Bonus, Character, Buff

class BonusInline(admin.TabularInline):
    model = Bonus

class BuffInline(admin.StackedInline):
    model = Buff
    extra = 1

class SourceAdmin(admin.ModelAdmin):
    inlines = (BonusInline, BuffInline)
    list_display = ('name_fr', 'author', 'level_dependent')
    list_filter = ('author',)

class CharacterAdmin(admin.ModelAdmin):
    list_display = ('name', 'undead')
    list_filter = ('players',)

class ConstraintAdmin(admin.ModelAdmin):
    pass

class StatAdmin(admin.ModelAdmin):
    pass

class BonusTypeAdmin(admin.ModelAdmin):
    list_display = ('name_en', 'name_fr', 'stacks')
    list_display_links = ('name_en',)
    list_editable = ('name_fr',)

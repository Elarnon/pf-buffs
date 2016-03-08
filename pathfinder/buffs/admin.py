from django.contrib import admin

# Register your models here.
from .models import BonusType, Stat, ConstrainedStat, Source, Bonus, Character, Buff

class BonusInline(admin.TabularInline):
    model = Bonus

class BuffInline(admin.TabularInline):
    model = Buff

class SourceAdmin(admin.ModelAdmin):
    inlines = (BonusInline, BuffInline)

class CharacterAdmin(admin.ModelAdmin):
    inlines = (BuffInline,)

class ConstrainedStatAdmin(admin.ModelAdmin):
    list_display = ('stat', 'name_fr')
    list_editable = ('stat', 'name_fr')

class ConstrainedStatInline(admin.TabularInline):
    model = ConstrainedStat

class StatAdmin(admin.ModelAdmin):
    inlines = (ConstrainedStatInline,)

admin.site.register(BonusType)
admin.site.register(ConstrainedStat, ConstrainedStatAdmin)
admin.site.register(Stat, StatAdmin)
admin.site.register(Source, SourceAdmin)
admin.site.register(Character, CharacterAdmin)

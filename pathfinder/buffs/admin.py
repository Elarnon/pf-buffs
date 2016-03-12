from django.contrib import admin

# Register your models here.
from .models import BonusType, Stat, Constraint, Source, Bonus, Character, Buff

class BonusInline(admin.TabularInline):
    model = Bonus

class SourceAdmin(admin.ModelAdmin):
    inlines = (BonusInline,)

class CharacterAdmin(admin.ModelAdmin):
    pass

class ConstraintAdmin(admin.ModelAdmin):
    pass

class StatAdmin(admin.ModelAdmin):
    pass

admin.site.register(BonusType)
admin.site.register(Constraint, ConstraintAdmin)
admin.site.register(Stat, StatAdmin)
admin.site.register(Source, SourceAdmin)
admin.site.register(Character, CharacterAdmin)
admin.site.register(Buff)

from django.contrib import admin
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory
from .models import Series, Character, CharacterInstance, Location, LocationInstance
from .models import Outline, Arc, ArcElementNode, StoryElementNode

# Register your models here.


class SeriesAdmin(admin.ModelAdmin):
    pass


class CharacterAdmin(admin.ModelAdmin):
    pass


class CharacterInstanceAdmin(admin.ModelAdmin):
    pass


class LocationAdmin(admin.ModelAdmin):
    pass


class LocationInstanceAdmin(admin.ModelAdmin):
    pass


class OutlineAdmin(admin.ModelAdmin):
    pass


class ArcAdmin(admin.ModelAdmin):
    pass


class ArcElementNodeAdmin(TreeAdmin):
    form = movenodeform_factory(ArcElementNode)


class StoryElementNodeAdmin(TreeAdmin):
    form = movenodeform_factory(StoryElementNode)


admin.site.register(Series, SeriesAdmin)
admin.site.register(Character, CharacterAdmin)
admin.site.register(CharacterInstance, CharacterInstanceAdmin)
admin.site.register(Location, LocationAdmin)
admin.site.register(LocationInstance, LocationInstanceAdmin)
admin.site.register(Outline, OutlineAdmin)
admin.site.register(Arc, ArcAdmin)
admin.site.register(ArcElementNode, ArcElementNodeAdmin)
admin.site.register(StoryElementNode, StoryElementNodeAdmin)

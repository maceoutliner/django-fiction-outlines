from django.contrib import admin
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory
from .models import Series, Character, CharacterInstance, Location, LocationInstance
from .models import Outline, Arc, ArcElementNode, StoryElementNode

# Register your models here.


class SeriesAdmin(admin.ModelAdmin):  # pragma: no cover
    pass


class CharacterAdmin(admin.ModelAdmin):  # pragma: no cover
    pass


class CharacterInstanceAdmin(admin.ModelAdmin):  # pragma: no cover
    pass


class LocationAdmin(admin.ModelAdmin):  # pragma: no cover
    pass


class LocationInstanceAdmin(admin.ModelAdmin):  # pragma: no cover
    pass


class OutlineAdmin(admin.ModelAdmin):  # pragma: no cover
    pass


class ArcAdmin(admin.ModelAdmin):  # pragma: no cover
    pass


class ArcElementNodeAdmin(TreeAdmin):  # pragma: no cover
    form = movenodeform_factory(ArcElementNode)  # pragma: no cover


class StoryElementNodeAdmin(TreeAdmin):  # pragma: no cover
    form = movenodeform_factory(StoryElementNode)  # pragma: no cover


admin.site.register(Series, SeriesAdmin)  # pragma: no cover
admin.site.register(Character, CharacterAdmin)  # pragma: no cover
admin.site.register(CharacterInstance, CharacterInstanceAdmin)  # pragma: no cover
admin.site.register(Location, LocationAdmin)  # pragma: no cover
admin.site.register(LocationInstance, LocationInstanceAdmin)  # pragma: no cover
admin.site.register(Outline, OutlineAdmin)  # pragma: no cover
admin.site.register(Arc, ArcAdmin)  # pragma: no cover
admin.site.register(ArcElementNode, ArcElementNodeAdmin)  # pragma: no cover
admin.site.register(StoryElementNode, StoryElementNodeAdmin)  # pragma: no cover

import logging
from django import forms
from django.utils.translation import gettext_lazy as _
from treebeard import forms as tforms
from .models import CharacterInstance, LocationInstance, Outline
from .models import Character, Location, Series, ArcElementNode, StoryElementNode

logger = logging.getLogger('forms')
logger.setLevel(logging.DEBUG)


class OutlineMoveNodeForm(tforms.MoveNodeForm):
    '''
    Subclass of base ``treebeard`` move node form allowing us to restrict
    target node options to within a single tree.
    '''

    __position_choices_sorted = (
        ('sorted-child', _('Child of')),
        ('sorted-sibling', _('Sibling of')),
    )

    __position_choices_unsorted = (
        ('first-child', _('First child of')),
        ('left', _('Before')),
        ('right', _('After')),
    )

    _position = forms.ChoiceField(required=True, label=_("Position"))

    _ref_node_id = forms.TypedChoiceField(required=True,
                                          label=_("Relative to"))

    def __init__(self, data=None, files=None, auto_id='id_%s', prefix=None,
                 initial=None, error_class=forms.models.ErrorList, label_suffix=':',
                 empty_permitted=False, instance=None, **kwargs):
        '''
        Here's the deal. py:module:`treebeard` has a great API with one exception.
        That exception is this form. If you want to limit the tree, you need to override
        the py:method:`treebeard.forms.MoveNodeForm.__init__` method, but because it does some
        black magic, you can't really ever call ``super()`` for it. Which unfortunately means
        that we have to embed the whole method in our class with a few small changes.
        '''
        root_node = kwargs.pop('root_node')
        if not root_node:
            raise KeyError(_('A root node must be specified'))  # pragma: no cover
        if isinstance(root_node, ArcElementNode):
            type = 'ArcElementNode'
        elif isinstance(root_node, StoryElementNode):
            type = 'StoryElementNode'
        else:
            type = 'Unknown'  # pragma: no cover
        logger.debug("OutlineMoveNodeForm was fed a root node of type: %s - pk %s" % (type, root_node.pk))
        # Beginning ``treebeard`` boilerplate.
        opts = self._meta
        if opts.model is None:  # pragma: no cover
            raise ValueError('forms.ModelForm has no class specified.')  # pragma: no cover

        # Update the position choice field.
        self.is_sorted = getattr(opts.model, 'node_order_by', False)
        if self.is_sorted:  # pragma: no cover - We don't user this. Only there for backwards compat.
            choices_sort_mode = self.__class__.__position_choices_sorted  # pragma: no cover
        else:
            choices_sort_mode = self.__class__.__position_choices_unsorted
        self.declared_fields['_position'].choices = choices_sort_mode

        # Here's where things get different as we need to ensure we only call our altered methods
        # Update _ref_node_id choices
        choices = self.__class__.mk_dropdown_tree(opts.model, root_node=root_node, for_node=instance)
        logger.debug("Length of choices is %d" % len(choices))
        self.declared_fields['_ref_node_id'].choices = choices

        # More ``treebeard`` boilerplate.
        # Put initial data  data for fields into a map, update map with initial data,
        # and pass this to the constructor.
        if instance is None:  # pragma: no cover
            initial_ = {}
        else:
            initial_ = self._get_position_ref_node(instance)

        if initial is not None:  # pragma: no cover
            initial_.update(initial)

        forms.ModelForm.__init__(self, data, files, auto_id, prefix, initial_, error_class, label_suffix,
                                 empty_permitted, instance, **kwargs)

    @classmethod
    def mk_dropdown_tree(cls, model, root_node, for_node=None):
        '''
        Override of ``treebeard`` method to enforce the same root.
        '''
        options = []
        # The difference is that we only generate the subtree for the current root.
        logger.debug("Using root node pk of %s" % root_node.pk)
        cls.add_subtree(for_node, root_node, options)
        return options[1:]


class CharacterInstanceForm(forms.ModelForm):
    '''
    Form for creating character instances
    '''

    def __init__(self, *args, **kwargs):
        character = kwargs.pop('character', None)
        super().__init__(*args, **kwargs)
        if character:
            self.fields['outline'].queryset = Outline.objects.filter(
                user=character.user)
        else:
            raise KeyError(_('character must be specified'))  # pragma: no cover

    class Meta:
        model = CharacterInstance
        fields = (
            'outline',
            'main_character',
            'pov_character',
            'protagonist',
            'antagonist',
            'obstacle',
            'villain',
        )


class LocationInstanceForm(forms.ModelForm):
    '''
    Form for creating location instances.
    '''

    def __init__(self, *args, **kwargs):
        location = kwargs.pop('location', None)
        super().__init__(*args, **kwargs)
        if location:
            self.fields['outline'].queryset = Outline.objects.filter(user=location.user)
        else:
            raise KeyError(_('location must be specified'))  # pragma: no cover

    class Meta:
        model = LocationInstance
        fields = {
            'outline',
        }


class CharacterForm(forms.ModelForm):
    '''
    Form for Character model.
    '''

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['series'].queryset = Series.objects.filter(user=user)
        else:
            raise KeyError(_('Form must be instantiated with a user object.'))  # pragma: no cover

    class Meta:
        model = Character
        fields = (
            'name',
            'description',
            'series',
            'tags',
        )


class LocationForm(forms.ModelForm):
    '''
    Form class for Locations
    '''

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['series'].queryset = Series.objects.filter(user=user)
        else:
            raise KeyError(_('Form must be instantiated with a user object.'))  # pragma: no cover

    class Meta:
        model = Location
        fields = (
            'name',
            'description',
            'series',
            'tags',
        )


class OutlineForm(forms.ModelForm):
    '''
    Form class for Outline model
    '''

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        if user:
            self.fields['series'].queryset = Series.objects.filter(user=user)
        else:
            raise KeyError(_('Form must be instantiated with a user object.'))  # pragma: no cover

    class Meta:
        model = Outline
        fields = (
            'title',
            'description',
            'series',
            'tags',
        )


class ArcNodeForm(forms.ModelForm):
    '''
    Form class for arc node form.
    Handles properties, but not position or parent arc.
    '''

    def __init__(self, *args, **kwargs):
        arc = kwargs.pop('arc')
        super().__init__(*args, **kwargs)
        if arc:
            outline = arc.outline
            self.fields['assoc_characters'].queryset = CharacterInstance.objects.filter(outline=outline)
            self.fields['assoc_locations'].queryset = LocationInstance.objects.filter(outline=outline)
            self.fields['story_element_node'].queryset = StoryElementNode.objects.filter(outline=outline, depth__gt=1)
        else:
            raise KeyError(_('form must be instantiated with an arc object.'))  # pragma: no cover

    class Meta:
        model = ArcElementNode
        fields = (
            'arc_element_type',
            'description',
            'assoc_characters',
            'assoc_locations',
            'story_element_node',
        )


class StoryNodeForm(forms.ModelForm):
    '''
    Form class for story node form.
    Handles properties but not position or parent arc.
    '''

    def __init__(self, *args, **kwargs):
        outline = kwargs.pop('outline')
        super().__init__(*args, **kwargs)
        if outline:
            self.fields['assoc_characters'].queryset = CharacterInstance.objects.filter(outline=outline)
            self.fields['assoc_locations'].queryset = LocationInstance.objects.filter(outline=outline)
        else:
            raise KeyError(_('Form must be isntantiated with an outline object.'))  # pragma: no cover

    class Meta:
        model = StoryElementNode
        fields = {
            'name',
            'story_element_type',
            'description',
            'assoc_characters',
            'assoc_locations',
        }

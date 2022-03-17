import uuid
import logging
from collections import OrderedDict
from django.db.models.functions import Now
from django.core.exceptions import ObjectDoesNotExist
from django.db import models, IntegrityError, transaction
from django.db.models import Q
from django.conf import settings
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.utils.functional import cached_property
from model_utils.models import TimeStampedModel as LegacyTimeStampedModel
from model_utils.fields import AutoCreatedField, AutoLastModifiedField as LegacyAutoLastModifiedField
from treebeard.mp_tree import MP_Node
from taggit.managers import TaggableManager
from taggit.models import GenericUUIDTaggedItemBase, TaggedItemBase
from .signals import tree_manipulation

logger = logging.getLogger('MS_Models')
logger.setLevel('DEBUG')

# Create your models here


class AutoLastModifiedField(LegacyAutoLastModifiedField):
    '''
    Override of the default model_utils behavior to ensure
    that when an instance is created that the modifed and created will
    be the same.
    '''
    def pre_save(self, model_instance, add):
        if (hasattr(model_instance, 'created') and
            model_instance._meta.get_field('created').__class__ ==
            AutoCreatedField and
            not getattr(model_instance, 'pk')):  # noqa: E129
            value = getattr(model_instance, 'created')
        else:
            value = Now()
        setattr(model_instance, self.attname, value)
        return value


class TimeStampedModel(LegacyTimeStampedModel):
    '''
    Override the model_utils behavior to use our new field.
    '''
    modified = AutoLastModifiedField()

    class Meta:
        abstract = True


user_relation = settings.AUTH_USER_MODEL

MACE_TYPES = (
    ('milieu', "Milieu"),
    ('answer', "Answers"),
    ('character', "Character"),
    ('event', "Event")
)

ARC_NODE_TYPES_CHOICES = (
    ('root', 'Arc Parent Node(user-hidden)'),
    ('mile_hook', "Milestone: Hook"),
    ('mile_pt1', "Milestone: Plot Turn 1"),
    ('mile_pnch1', "Milestone: Pinch 1"),
    ('mile_mid', "Milestone: Midpoint"),
    ('mile_pnch2', "Milestone: Pinch 2"),
    ('mile_pt2', "Milestone: Plot Turn 2"),
    ('mile_reso', "Milestone: Resolution"),
    ('tf', "Try/Fail"),
    ('beat', "Beat"),
)

ARC_NODE_ELEMENT_DEFINITIONS = OrderedDict({
    'root': {
        'milestone': False,
        'template_description': None,
        'milestone_seq': None,
        'seq_restrict': None,
        'allowed_parents': None
    },
    'mile_hook': {
        'milestone': True,
        'template_description': _('The starting point of this arc. The opposite of the resolution.'),
        'milestone_seq': 1,
        'seq_restrict': None,
        'allowed_parents': None
    },
    'mile_pt1': {
        'milestone': True,
        'template_description': _('The change that initiates the story of the arc'),
        'milestone_seq': 2,
        'seq_restrict': None,
        'allowed_parents': None
    },
    'mile_pnch1': {
        'milestone': True,
        'template_description': _('The first major challenge to the path of the arc.'),
        'milestone_seq': 3,
        'seq_restrict': None,
        'allowed_parents': None
    },
    'mile_mid': {
        'milestone': True,
        'template_description': _('The middle of the arc, the arc moves towards the resolution with purpose.'),
        'milestone_seq': 4,
        'seq_restrict': None,
        'allowed_parents': None
    },
    'mile_pnch2': {
        'milestone': True,
        'template_description': _('The last major challenge to the arc. All appears lost.'),
        'milestone_seq': 5,
        'seq_restrict': None,
        'allowed_parents': None
    },
    'mile_pt2': {
        'milestone': True,
        'template_description': _('The change that allows the arc to resolve. The way past the final pinch.'),
        'milestone_seq': 6,
        'seq_restrict': None,
        'allowed_parents': None
    },
    'mile_reso': {
        'milestone': True,
        'template_description': _('The resolution of the arc. Opposite of the hook. Victory or failure is achieved.'),
        'milestone_seq': 7,
        'seq_restrict': None,
        'allowed_parents': None
    },
    'tf': {
        'milestone': False,
        'template_description': _('A try/fail cycle along the path of the arc.'),
        'milestone_seq': None,
        'seq_restrict': {'after': 'mile_hook', 'before': 'mile_reso'},
        'allowed_parents': ('tf',)
    },
    'beat': {
        'milestone': False,
        'template_description': _('Something happens... what?'),
        'milestone_seq': None,
        'seq_restrict': {'after': 'mile_hook', 'before': 'mile_reso'},
        'allowed_parents': ('tf',)
    },
})

STORY_NODE_ELEMENT_DEFINITIONS_TYPES_CHOICES = (
    ('root', 'Root'),
    ('ss', 'Scene/Sequel'),
    ('chapter', 'Chapter'),
    ('part', 'Part'),
    ('act', 'Act'),
    ('book', 'Book'),
)

STORY_NODE_ELEMENT_DEFINITIONS = {
    'root': {'allowed_children': ('ss', 'chapter', 'part', 'act', 'book'), 'allowed_parents': ()},
    'ss': {'allowed_chidren': None, 'allowed_parents': ('chapter', 'part', 'act', 'book', 'root')},
    'chapter': {'allowed_children': ('ss',), 'allowed_parents': ('part', 'act', 'book', 'root')},
    'part': {'allowed_children': ('chapter', 'ss'), 'allowed_parents': ('act', 'book', 'root')},
    'act': {'allowed_children': ('part', 'chapter', 'ss'), 'allowed_parents': ('book', 'root')},
    'book': {'allowed_children': ('act', 'part', 'chapter', 'ss'), 'allowed_parents': ('root',)},
}


class ArcIntegrityError(IntegrityError):
    '''
    Generic exception for Arc structural warnings.
    '''
    pass


class MilestoneSequenceError(ArcIntegrityError):
    '''
    Exception for when milestone arc elements violate their defined sequence rules.
    '''
    pass


class MilestoneDepthError(ArcIntegrityError):
    '''
    Exception for when an attempt to make a milestone a descendent of any node
    besides the root node for the tree.
    '''
    pass


class GenericArcSequenceError(ArcIntegrityError):
    '''
    Exception for when a non-milestone element is placed in an invalid sequence.
    '''
    pass


class ArcGenerationError(ArcIntegrityError):
    '''
    Exception for when a non-milestone node is placed at an invalid level of descendency.
    '''
    pass


class UUIDCharacterTag(GenericUUIDTaggedItemBase, TaggedItemBase):
    '''
    Character tags with UUID primary keys
    '''

    class Meta:
        verbose_name = _('Tag')
        verbose_name_plural = _("Tags")


class UUIDLocationTag(GenericUUIDTaggedItemBase, TaggedItemBase):
    '''
    Location tags with UUID primary keys
    '''

    class Meta:
        verbose_name = _('Tag')
        verbose_name_plural = _("Tags")


class UUIDOutlineTag(GenericUUIDTaggedItemBase, TaggedItemBase):
    '''
    Outline tags with UUID primary keys
    '''

    class Meta:
        verbose_name = _('Tag')
        verbose_name_plural = _("Tags")


class Character(TimeStampedModel):
    '''
    Reusable character defintion model.
    '''
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, db_index=True, help_text='Name of the character.')
    description = models.TextField(blank=True, null=True, help_text='Notes about the character to help you remember.')
    series = models.ManyToManyField('Series', blank=True,
                                    help_text='If the character is part of a series, consider referencing it here.')
    tags = TaggableManager(through=UUIDCharacterTag, blank=True,
                           help_text='Tags associated with this character. Yay, taxonomy!')
    user = models.ForeignKey(user_relation, on_delete=models.CASCADE,
                             help_text='The user that created this character.')

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse_lazy('fiction_outlines:character_detail', kwargs={'character': self.pk})


class CharacterInstance(TimeStampedModel):
    '''
    An instance of the character object that can be associated with outlines.
    '''
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    main_character = models.BooleanField(default=False, db_index=True,
                                         help_text='Is this character the main character for the outline?')
    pov_character = models.BooleanField(default=False, db_index=True, help_text='Is this character a POV character?')
    protagonist = models.BooleanField(default=False, db_index=True,
                                      help_text='Does this character serve as the protagonist for this outline?')
    antagonist = models.BooleanField(default=False, db_index=True,
                                     help_text='Does this character serve as an antagonist for this outline?')
    obstacle = models.BooleanField(default=False,
                                   db_index=True,
                                   help_text="Is this character an obstacle in the outline? (not antagonist)")
    villain = models.BooleanField(default=False, db_index=True, help_text='Is the character a straight-out villain?')
    character = models.ForeignKey(Character, on_delete=models.CASCADE,
                                  help_text='Reference to originating character object.')
    outline = models.ForeignKey('Outline', on_delete=models.CASCADE,
                                help_text='Outline this instance is associated with.')

    def __str__(self):
        return "%s (%s)" % (self.character.name, self.outline.title)

    def get_absolute_url(self):
        return reverse_lazy('fiction_outlines:character_instance_detail',
                            kwargs={'character': self.character.pk, 'instance': self.pk})

    class Meta:
        unique_together = ('outline', 'character')


class Location(TimeStampedModel):
    '''
    Reusable location definition model
    '''
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, db_index=True, help_text='Name of the location.')
    description = models.TextField(null=True, blank=True, help_text='Notes about the location to help you remember.')
    series = models.ManyToManyField('Series', blank=True, help_text='Series this location is associated with.')
    tags = TaggableManager(through=UUIDLocationTag, blank=True, help_text='Tags for this location.')
    user = models.ForeignKey(user_relation, on_delete=models.CASCADE, help_text='The user that created this location.')

    def __str__(self):
        return self.name  # pragma: no cover

    def get_absolute_url(self):
        return reverse_lazy('fiction_outlines:location_detail', kwargs={'location': self.pk})


class LocationInstance(TimeStampedModel):
    '''
    An instance of the given location that can be associated with a given outline.
    '''
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    location = models.ForeignKey(Location, on_delete=models.CASCADE, help_text='Originating location object.')
    outline = models.ForeignKey('Outline', on_delete=models.CASCADE,
                                help_text="Outline this object is associated with.")

    def __str__(self):
        return "%s (%s)" % (self.location.name, self.outline.title)

    def get_absolute_url(self):
        return reverse_lazy('fiction_outlines:location_instance_detail',
                            kwargs={'location': self.location.pk, 'instance': self.pk})

    class Meta:
        unique_together = ('location', 'outline')


class Series (TimeStampedModel):
    '''
    Container object to hold multiple outline objects if necessary.
    '''
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, db_index=True,
                             help_text="Name of the series. You can always change this later.")
    description = models.TextField(null=True, blank=True, help_text="Jot down a description about your series.")
    tags = TaggableManager(through=UUIDOutlineTag, blank=True, help_text='Tags for the series.')
    user = models.ForeignKey(user_relation, on_delete=models.CASCADE, help_text='The user that created this Series.')

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse_lazy('fiction_outlines:series_detail', kwargs={'series': self.pk})

    class Meta:
        verbose_name = 'Series'
        verbose_name_plural = 'Series'


class Outline (TimeStampedModel):
    '''
    The typical top of the hierarchy when not enclosed in a series.
    '''
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, db_index=True,
                             help_text='Outline title. You can always change this later.')
    description = models.TextField(
        null=True,
        blank=True,
        help_text='Optionally, describe the story. Or use for notes.'
    )
    series = models.ForeignKey(Series, null=True, blank=True, on_delete=models.SET_NULL,
                               help_text='Belongs to series.')
    tags = TaggableManager(through=UUIDOutlineTag, blank=True, help_text='Tags for the outline.')
    user = models.ForeignKey(user_relation, on_delete=models.CASCADE,
                             help_text='The user that created this outline.')

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse_lazy('fiction_outlines:outline_detail', kwargs={'outline': self.pk})

    @cached_property
    def length_estimate(self):
        '''
        Calculates and estimated word count based on number of characters, locations,
        and arcs. For reference see:
        http://www.writingexcuses.com/2017/07/02/12-27-choosing-a-length/
        '''
        characters = self.characterinstance_set.filter(
            Q(main_character=True) |
            Q(pov_character=True) |
            Q(protagonist=True) |
            Q(antagonist=True) |
            Q(villain=True)).count()
        locations = self.locationinstance_set.count()
        arcs = self.arc_set.count()
        return ((characters + locations) * 750) * (1.5 * arcs)

    @cached_property
    def story_tree_root(self):
        '''
        Fetches the root node for the outline's StoryElementNode tree.
        '''
        try:
            return StoryElementNode.objects.get(outline=self, depth=1)
        except ObjectDoesNotExist:  # pragma: no cover
            return None

    def refresh_from_db(self, *args, **kwargs):
        super().refresh_from_db(*args, **kwargs)
        cached_properties = [
            'length_estimate',
            'story_tree_root',
        ]
        for property in cached_properties:
            try:
                del self.__dict__[property]
            except KeyError:  # pragma: no cover
                pass

    @transaction.atomic
    def create_arc(self, mace_type, name):
        '''
        Creates the story arc and initial tree for that arc
        for the current outline. Returns the resulting Arc
        instance.
        '''
        arc = Arc(mace_type=mace_type, outline=self, name=name)
        arc.save()
        milestone_count = arc.generate_template_arc_tree()
        if milestone_count == 7:  # pragma: no cover
            arc.refresh_from_db()
            return arc
        else:
            raise ArcIntegrityError('Something went wrong during arc template generation')  # pragma: no cover

    def validate_nesting(self):
        '''
        Reviews the story tree and validates associated arc
        elements are nested appropriately. Returns a dict of errors.
        '''
        error_dict = {}
        story_root = self.story_tree_root
        story_nodes = story_root.get_descendants().prefetch_related('arcelementnode_set').filter(depth=2)

        def parse_children(node_object, seq=0):
            '''
            Recursive method to check all generations of a node for arc
            elements.
            '''
            returnable_ae_dict = {}
            if node_object.get_children_count():
                for node in node_object.get_children().prefetch_related('arcelementnode_set'):
                    if node.get_children_count():
                        local_ae_dict, newseq = parse_children(node, seq)
                        for arc in local_ae_dict.keys():
                            if arc not in returnable_ae_dict.keys():
                                returnable_ae_dict[arc] = []
                            returnable_ae_dict[arc] = returnable_ae_dict[arc] + (local_ae_dict[arc])
                        seq = newseq
                    else:
                        local_arc_elements = node.arcelementnode_set.all()
                        for ae in local_arc_elements:
                            if ae.is_milestone:
                                logger.debug('Found a milestone to sequence.')
                                if ae.arc not in returnable_ae_dict.keys():
                                    returnable_ae_dict[ae.arc] = []
                                returnable_ae_dict[ae.arc].append({
                                    ae.arc_element_type: seq,
                                })
                                logger.debug('Appended an element of type %s  from arc %s at sequence %d' % (
                                    ae.arc_element_type,
                                    ae.arc.name,
                                    seq))
                        seq += 1
            return returnable_ae_dict, seq

        arcs_out_of_sequence = []
        arc_milestone_elements = {}
        x = 0
        arcs_with_nest_conflicts = []
        for node in story_nodes:
            arc_elements_found, x = parse_children(node, x)
            for arc in arc_elements_found.keys():
                if arc not in arc_milestone_elements.keys():
                    arc_milestone_elements[arc] = []
                arc_milestone_elements[arc] = arc_milestone_elements[arc] + arc_elements_found[arc]
        arc_entry_exit = {}
        for arc, elements in arc_milestone_elements.items():
            z = {}
            last_local_seq = 0
            logger.debug("There are %d elements to parse" % len(elements))
            for ae_elements in elements:
                logger.debug('Parsing %s' % ae_elements)
                for k, v in ae_elements.items():
                    z[k] = v
            logger.debug('%s' % OrderedDict(sorted(z.items(), key=lambda t: t[1])))
            for key, value in OrderedDict(sorted(z.items(), key=lambda t: t[1])).items():
                if last_local_seq > ARC_NODE_ELEMENT_DEFINITIONS[key]['milestone_seq']:
                    arcs_out_of_sequence.append(arc)
                    break
                last_local_seq = ARC_NODE_ELEMENT_DEFINITIONS[key]['milestone_seq']
                if 'mile_hook' in z.keys() and 'mile_reso' in z.keys():
                    arc_entry_exit[arc] = {
                        'entry': z['mile_hook'],
                        'exit': z['mile_reso'],
                    }
        if arc_entry_exit:
            temp_ent = {}
            temp_ex = {}
            for en_arc, enter in arc_entry_exit.items():
                temp_ent[en_arc] = enter['entry']
            for ex_arc, leave in arc_entry_exit.items():
                temp_ex[ex_arc] = leave['exit']
            arc_entries = OrderedDict(sorted(temp_ent.items(), key=lambda t: t[1]))
            arc_exits = OrderedDict(sorted(temp_ex.items(), key=lambda t: t[1], reverse=True))
            logger.debug("Evaluating entries vs exits: %s vs %s" % (arc_entries, arc_exits))
            index_num = 0
            for entrance in arc_entries.keys():
                test_exit = list(arc_exits.keys())[index_num]
                logger.debug('Checking %s vs %s arcs' % (entrance, test_exit))
                if entrance != test_exit:
                    logger.debug("Different arcs.. making sure they don't share an entry/exist point")
                    if (arc_entry_exit[entrance]['entry'] != arc_entry_exit[test_exit]['entry'] and
                        arc_entry_exit[entrance]['exit'] != arc_entry_exit[test_exit]['exit']):
                        if ((arc_entry_exit[entrance]['entry'] < arc_entry_exit[test_exit]['entry'] and
                                arc_entry_exit[entrance]['exit'] > arc_entry_exit[test_exit]['exit']) or
                            (arc_entry_exit[entrance]['entry'] > arc_entry_exit[test_exit]['entry'] and
                             arc_entry_exit[entrance]['exit'] < arc_entry_exit[test_exit]['exit'])):
                            logger.debug("No same entry point, but the nest is still valid.")
                        else:
                            logger.debug("nesting error found: %s should resole before %s" % (entrance, test_exit))
                            if entrance not in arcs_with_nest_conflicts:
                                arcs_with_nest_conflicts.append(entrance)
                            if test_exit not in arcs_with_nest_conflicts:
                                arcs_with_nest_conflicts.append(test_exit)
                    else:
                        logger.debug('Arcs share an entry/exit point so nesting error is ignored.')
                index_num += 1
        unique_nest_errors = list(set(arcs_with_nest_conflicts))
        logger.debug("%d arcs with nesting errors found" % len(unique_nest_errors))
        logger.debug('Arcs with nesting errors: %s' % unique_nest_errors)
        story_tree = story_root.get_descendants().prefetch_related('arcelementnode_set')
        if arcs_out_of_sequence:
            error_dict['nest_arc_seq'] = {
                'error_message': "Arc element milestones are out of sequence",
                'offending_arcs': []
            }
            logger.debug('There are %d arcs out of internal sequence' % len(arcs_out_of_sequence))
            arc_sequence_error_dict = {}
            story_root.refresh_from_db()
            for arc in arcs_out_of_sequence:
                arc_sequence_error_dict['offending_nodes'] = story_tree.filter(arcelementnode__arc=arc)
            error_dict['nest_arc_seq']['offending_arcs'].append(arc_sequence_error_dict)
        if unique_nest_errors:
            error_dict['nest_reso_error'] = {
                'error_message': "Arcs should resolve in the opposite order that they were introduced",
                'offending_nodes': story_tree.filter(
                    arcelementnode__arc__in=unique_nest_errors,
                    arcelementnode__arc_element_type='mile_reso'
                )
            }
        return error_dict


class Arc (TimeStampedModel):
    '''
    A MACE arc for a outline.
    '''
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mace_type = models.CharField(max_length=10, choices=MACE_TYPES, db_index=True,
                                 help_text='The MACE type of the Arc.')
    outline = models.ForeignKey("Outline", on_delete=models.CASCADE,
                                help_text='Arc belongs to this outline.')
    name = models.CharField(max_length=255, db_index=True,
                            help_text="Name of this Arc (makes it easier for you to keep track of it.)")

    def __str__(self):
        return "%s (%s)" % (self.name, self.outline.title)

    def get_absolute_url(self):
        return reverse_lazy('fiction_outlines:arc_detail', kwargs={'outline': self.outline.pk, 'arc': self.pk})

    @cached_property
    def current_errors(self):
        '''
        Returns list of errors from arc_validation.
        '''
        return self.fetch_arc_errors()

    @cached_property
    def arc_root_node(self):
        '''
        Returns the root node from this object's ArcElementNode tree.
        '''
        try:
            return ArcElementNode.objects.get(depth=1, arc=self)
        except ObjectDoesNotExist:
            return None

    def refresh_from_db(self, *args, **kwargs):
        super().refresh_from_db(*args, **kwargs)
        cached_properties = [
            'current_errors',
            'arc_root_node',
        ]
        for property in cached_properties:
            try:
                del self.__dict__[property]
            except KeyError:  # pragma: no cover
                pass

    @transaction.atomic
    def generate_template_arc_tree(self):
        '''
        Generate a seven point template in this arc. Arc must be empty.
        '''
        arc_root = self.arc_root_node
        if not arc_root:
            arc_root = ArcElementNode.add_root(
                arc_element_type='root',
                description='root of arc %s' % self.name,
                arc=self
            )
        if arc_root.get_children():
            raise ArcIntegrityError(_("This arc already has elements. You cannot build a template on top of it"))
        for key, value in ARC_NODE_ELEMENT_DEFINITIONS.items():
            if value['milestone']:
                arc_root.add_child(arc_element_type=key, description=value['template_description'])
                arc_root.refresh_from_db()
        return ArcElementNode.objects.get(pk=arc_root.pk).get_children().count()

    def fetch_arc_errors(self):
        '''
        Evaluates the current tree of the arc and provides a list of errors that
        the user should correct.
        '''
        error_list = []
        hnode = self.validate_first_element()
        if hnode:
            error_list.append({'hook_error': hnode})
        rnode = self.validate_last_element()
        if rnode:
            error_list.append({'reso_error': rnode})
        try:
            self.validate_generations()
        except ArcGenerationError as ag:
            error_list.append({'generation_error': str(ag)})
        milecheck = self.validate_milestones()
        if milecheck:
            error_list.append({'mseq_error': milecheck})
        return error_list

    def validate_first_element(self):
        '''
        Ensures that the first node for the direct decendents of root is the hook.
        '''
        first_child = self.arc_root_node.get_first_child()
        if first_child.arc_element_type == 'mile_hook':
            return None
        return first_child

    def validate_last_element(self):
        '''
        Ensures that the last element of the arc is the resolution.
        '''
        last_child = self.arc_root_node.get_last_child()
        if last_child.arc_element_type == 'mile_reso':
            return None
        return last_child

    def validate_generations(self):
        '''
        Make sure that the descendent depth is valid.
        '''
        nodes = self.arc_root_node.get_descendants()
        for node in nodes:
            logger.debug("Checking parent for node of type %s" % node.arc_element_type)
            parent = ArcElementNode.objects.get(pk=node.pk).get_parent(update=True)
            if 'mile' in node.arc_element_type and parent.get_depth() > 1:
                logger.debug("Milestone node... with leaf parent")
                raise ArcGenerationError(_("Milestones cannot be descendants of anything besides the root!"))
            if (parent.get_depth() > 1 and
                parent.arc_element_type not in ARC_NODE_ELEMENT_DEFINITIONS[node.arc_element_type]['allowed_parents']):
                raise ArcGenerationError(_("Node %s cannot be a descendant of node %s" % (node, parent)))
        return None

    def validate_milestones(self):
        '''
        Reviews the arc element tree to ensure that milestones appear in the right
        order.
        '''
        milestones = self.arc_root_node.get_children().filter(arc_element_type__contains='mile')
        current_cursor = 0
        for mile in milestones:
            seq = mile.milestone_seq
            if seq < current_cursor:
                return mile
            current_cursor = seq
        return None


class ArcElementNode(TimeStampedModel, MP_Node):
    '''
    Tree nodes for the arc elements.
    '''

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    steplen = 5
    arc_element_type = models.CharField(max_length=15, db_index=True, choices=ARC_NODE_TYPES_CHOICES,
                                        help_text='What part of the arc does this represent?')
    arc = models.ForeignKey(Arc, on_delete=models.CASCADE, help_text='Parent arc.')
    headline = models.CharField(max_length=255, blank=True, null=True, help_text=_('Autogenerated from description'))
    description = models.TextField(help_text='Describe what happens at this moment in the story...')
    story_element_node = models.ForeignKey('StoryElementNode', on_delete=models.SET_NULL, blank=True, null=True,
                                           help_text='Which story node is this element associated with?')
    assoc_characters = models.ManyToManyField(CharacterInstance, blank=True,
                                              help_text='M2M relation with character instances.',
                                              verbose_name='Associated Characters')
    assoc_locations = models.ManyToManyField(LocationInstance, blank=True,
                                             help_text='M2M relation with location instances.',
                                             verbose_name='Associated Locations')

    def __str__(self):
        return "[%s: %s]" % (self.arc.name, self.get_arc_element_type_display())

    def get_absolute_url(self):
        return reverse_lazy('fiction_outlines:arcnode_detail',
                            kwargs={'outline': self.parent_outline.pk, 'arc': self.arc.pk, 'arcnode': self.pk})

    @property
    def milestone_seq(self):
        '''
        Returns the milestone sequence based off of the arc element definitions.
        '''
        return ARC_NODE_ELEMENT_DEFINITIONS[self.arc_element_type]['milestone_seq']

    @cached_property
    def is_milestone(self):
        '''
        Does this node represent an arc milestone?
        '''
        return ARC_NODE_ELEMENT_DEFINITIONS[self.arc_element_type]['milestone']

    @cached_property
    def parent_outline(self):
        '''
        Private method to fetch parent outline.
        '''
        return self.arc.outline

    def add_child(self, arc_element_type, description=None, story_element_node=None, **kwargs):
        '''
        Overrides the default `treebeard` function, adding additional integrity checks.
        '''
        if 'mile' in arc_element_type:
            if 'mile' in self.arc_element_type:
                raise ArcGenerationError('You cannot have a milestone as a child to another milestone.')
            if self.get_depth() == 1:
                nodes_to_check = self.get_descendants().filter(arc_element_type__icontains='mile')
            else:
                nodes_to_check = self.get_root().get_descendants().filter(arc_element_type__icontains='mile')
            for node in nodes_to_check:
                if node.arc_element_type == arc_element_type:
                    raise ArcIntegrityError('You cannot have two of the same milestone in the same arc.')
        return super().add_child(
            arc=self.arc,
            arc_element_type=arc_element_type,
            description=description,
            story_element_node=story_element_node
        )

    def add_sibling(self, pos=None, arc_element_type=None, description=None, story_element_node=None, **kwargs):
        '''
        Overrides the default `treebeard` function, adding additional integrity checks.
        '''
        if 'mile' in arc_element_type:
            if self.get_depth() == 1:
                raise ArcGenerationError('Milestones are invalid to be the root')
            nodes_to_check = self.get_root().get_descendants().filter(arc_element_type__icontains='mile')
            for node in nodes_to_check:
                if node.arc_element_type == arc_element_type:
                    raise ArcIntegrityError('You cannot have two of the same milestone in the same arc.')
        return super().add_sibling(
            pos=pos,
            arc=self.arc,
            arc_element_type=arc_element_type,
            description=description,
            story_element_node=story_element_node
        )


ArcElementNode._meta.get_field('path').max_length = 1024


class StoryElementNode(TimeStampedModel, MP_Node):
    '''
    Tree nodes for the overall outline of the story.
    '''
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    steplen = 5
    name = models.CharField(max_length=255, null=True, blank=True,
                            help_text='Optional name/title for this element of the story.')
    description = models.TextField(null=True, blank=True,
                                   help_text='Optional description for this element of the story.')
    outline = models.ForeignKey(Outline, on_delete=models.CASCADE, help_text="Parent outline.")
    story_element_type = models.CharField(
        max_length=25,
        db_index=True,
        choices=STORY_NODE_ELEMENT_DEFINITIONS_TYPES_CHOICES,
        default='ss',
        help_text='What part of the story does this represent? A scene? A chapter?'
    )
    assoc_characters = models.ManyToManyField(CharacterInstance, blank=True,
                                              help_text='Character instances associated with this node.',
                                              verbose_name='Associated Characters')
    assoc_locations = models.ManyToManyField(LocationInstance, blank=True,
                                             help_text='Location instances associated with this node.',
                                             verbose_name='Associated Locations')

    def __str__(self):
        return "[%s : %s] %s" % (self.outline.title, self.get_story_element_type_display(), self.name)

    def get_absolute_url(self):
        return reverse_lazy('fiction_outlines:storynode_detail', kwargs={'outline': self.outline.pk,
                                                                         'storynode': self.pk})

    @property
    def all_characters(self):
        '''
        Returns a queryset of all characters associated with this node and its descendants,
        excluding any duplicates.
        '''
        qs = self.assoc_characters.all()
        for node in self.get_descendants():
            qs2 = node.assoc_characters.all()
            qs = qs.union(qs2)
        return qs

    @property
    def impact_rating(self):
        '''
        Returns the impact rating for this node. Impact rating is a measure
        of how powerful this moment in the story is by evaluting how many simultaneous
        arc elements are associated with it. There is also a generational bleed element,
        where the impact score creates shockwaves throughout their direct ancestor and
        descendant nodes. This echo fades fast, but the bigger the impact, the farther
        it goes.

        Currently, the impact bleed does not extend to sibling nodes.

        WARNING: Here be dragons.
        '''
        if self.depth == 1:
            logger.debug('Root node. Skipping.')
            return 0  # pragma: no cover
        impact_bleed = {
            'mile': 0.5,  # A milestone extends it's influence by 50% per generation
            'tf_beat': 0.25,
        }
        inherited_impact = 0
        base_impact, add_impact, mile_impact = self._local_impact_rating()
        local_impact = base_impact + add_impact + mile_impact
        logger.debug("Local impact is %f" % local_impact)
        parents = self.get_ancestors().filter(depth__gt=1)
        children = self.get_descendants()
        logger.debug('Found %d parents and %d children' % (parents.count(), children.count()))
        for node in parents | children:
            if node.depth == 1:
                logger.debug("Skipping root node...")
            else:
                logger.debug('Checking a related node...')
                b, a, m = node._local_impact_rating()
                logger.debug('Related node has %f of additional impact and %f of milestone impact.' % (a, m))
                if (a + m) > 0:
                    if node.depth > self.depth:
                        depth_diff = node.depth - self.depth
                    else:
                        depth_diff = self.depth - node.depth
                    logger.debug('There is a generational difference of %f. Adjusting impact bleed.' % depth_diff)
                    for x in range(depth_diff):
                        a = a * impact_bleed['tf_beat']
                        m = m * impact_bleed['mile']
                    logger.debug('Additional impact bleed of %f. Milestone impact bleed of %f' % (a, m))
                    inherited_impact += a + m
                    logger.debug('Final impact bleed of %f. Adding to inherited impact.' % inherited_impact)
                else:
                    logger.debug('Node had 0 bleedworthy impact. Skipping...')
        logger.debug('Inherited impact of %f. Adding to local impact of %f' % (inherited_impact, local_impact))
        return local_impact + inherited_impact

    def _local_impact_rating(self):
        '''
        Traverses the generations to evaluate the impact/power
        of the arc elements associated with each node.
        '''
        impact_values = {
            'base': 0.5,
            'mile': 2,
            'beat': 0.5,
            'tf': 0.5,
            'mile_child': 0.5,
            'same_mile': 2.5,
        }
        base_impact = impact_values['base']
        mile_impact = 0
        add_impact = 0
        direct_arc_nodes = self.arcelementnode_set.all()
        logger.debug('Found %d associated arc nodes...' % direct_arc_nodes.count())
        arc_element_types = {}
        logger.debug('Preloading arc element types...')
        for type_name, values in ARC_NODE_ELEMENT_DEFINITIONS.items():
            arc_element_types[type_name] = 0
        for node in direct_arc_nodes:
            arc_element_types[node.arc_element_type] += 1
            logger.debug('Found an node of type %s' % node.arc_element_type)
            if ARC_NODE_ELEMENT_DEFINITIONS[node.arc_element_type]['milestone']:
                logger.debug('node is a milestone of type %s. Adding bonus' % node.arc_element_type)
                mile_impact += impact_values['mile']
            else:
                logger.debug('Checking node parent.')
                parent_type = node.get_parent().arc_element_type
                logger.debug('Direct parent is of type %s' % parent_type)
                if ARC_NODE_ELEMENT_DEFINITIONS[node.get_parent().arc_element_type]['milestone']:
                    logger.debug('Impact calc: adding a bonus for being direct child of milestone.')
                    add_impact += impact_values['mile_child']
                if node.arc_element_type == 'beat':
                    logger.debug('Adding impact for beat.')
                    add_impact += impact_values['beat']
                if node.arc_element_type == 'tf':
                    add_impact += impact_values['tf']
        for key, value in arc_element_types.items():
            if ARC_NODE_ELEMENT_DEFINITIONS[key]['milestone'] and value > 1:
                logger.debug('Adding bonus for same milestone.')
                add_impact += (value - 1) * .5
        return base_impact, add_impact, mile_impact

    @property
    def all_locations(self):
        '''
        Returns a queryset of all locations associated with this node and its descendants,
        excluding any duplicates.
        '''
        qs = self.assoc_locations.all()
        for node in self.get_descendants():
            qs2 = node.assoc_locations.all()
            qs = qs.union(qs2)
        return qs

    def move(self, target, pos=None):
        '''
        An override of the treebeard api in order to send a signal in advance.
        '''
        if self.outline != target.outline:
            raise IntegrityError('Elements must be from the same outline!')
        tree_manipulation.send(
            sender=self.__class__,
            instance=self,
            action='move',
            target_node_type=None,
            target_node=target,
            pos=pos
        )
        return super().move(target, pos)

    def add_child(self, story_element_type=None, outline=None, name=None, description=None, **kwargs):
        '''
        An override of the treebeard add_child() method so we can send a signal.
        '''
        if not outline:
            outline = self.outline
        if outline != self.outline:
            raise IntegrityError('Elements must be from the same outline!')
        tree_manipulation.send(
            sender=self.__class__,
            instance=self,
            action='add_child',
            target_node_type=story_element_type,
            target_node=None,
            pos=None
        )
        return super().add_child(
            story_element_type=story_element_type,
            outline=outline,
            name=name,
            description=description,
            **kwargs
        )

    def add_sibling(self, story_element_type=None, outline=None, name=None, description=None, pos=None, **kwargs):
        '''
        Override of treebeard api to allow us to send a signal.
        '''
        if not outline:
            outline = self.outline
        if outline != self.outline:
            raise IntegrityError('Elements must be from the same outline!')
        tree_manipulation.send(
            sender=self.__class__,
            instance=self,
            action='add_sibling',
            target_node_type=story_element_type,
            target_node=None,
            pos=pos
        )
        return super().add_sibling(
            story_element_type=story_element_type,
            outline=outline,
            name=name,
            description=description,
            pos=pos,
            **kwargs
        )


StoryElementNode._meta.get_field('path').max_length = 1024

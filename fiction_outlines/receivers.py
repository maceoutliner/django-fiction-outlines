'''
Recieving methods for signals go here.
'''

import logging
from django.db.models.signals import pre_save, post_save, m2m_changed
from django.db import IntegrityError
from django.utils.translation import gettext_lazy as _
from django.template.defaultfilters import truncatewords, truncatechars
from django.dispatch import receiver
from .models import Outline, StoryElementNode, ArcElementNode, CharacterInstance, LocationInstance
from .models import STORY_NODE_ELEMENT_DEFINITIONS, ArcIntegrityError
from .signals import tree_manipulation


logger = logging.getLogger(name='Signals')

# Model-based signal logic appears below here.


@receiver(pre_save, sender=ArcElementNode)
def generate_headline_from_description(sender, instance, *args, **kwargs):
    '''
    Auto generate the headline of the node from the first lines of the description.
    '''
    lines = instance.description.split('\n')
    headline = truncatewords(lines[0], 20)
    if headline[:-1] == '…':
        headline = truncatechars(headline.replace(' …', ''), 250)  # Just in case the words exceed char limit.
    else:
        headline = truncatechars(headline, 250)
    instance.headline = headline


@receiver(post_save, sender=Outline)
def story_root_for_new_outline(sender, instance, created, *args, **kwargs):
    '''
    If a new instance of a Outline is created, also create
    the root node of the story tree.
    '''
    if created and isinstance(instance, Outline):
        streeroot = StoryElementNode.add_root(outline=instance, story_element_type='root')
        streeroot.save()
        instance.refresh_from_db()


@receiver(m2m_changed, sender=ArcElementNode.assoc_characters.through)
@receiver(m2m_changed, sender=ArcElementNode.assoc_locations.through)
def arc_node_edit_add_missing_characters_and_locations_to_related_story_node(
        sender,
        instance,
        action,
        reverse,
        pk_set,
        *args,
        **kwargs
):
    '''
    If an arc_element is modified and it's characters/locations are not already in the story node, add them.
    We don't assume that removing the arc element would change the characters or locations as of yet.
    This takes up a little more space in the database, but the additional flexibility for users is
    worth it.

    '''
    if action == 'post_add':
        logger.debug("Updating nodes after character or location change.")
        if reverse:
            logger.debug("Searching backwards from character or location to arc node")
            # We are going to need to be querying the arc element node.
            for arcnode in instance.arcelementnode_set.all().select_related('story_element_node'):
                logger.debug("Scanning arc node...")
                if arcnode.story_element_node:
                    logger.debug("Found story node to update...")
                    story_node = arcnode.story_element_node
                    if isinstance(instance, CharacterInstance):
                        logger.debug("Updating characters...")
                        story_node.assoc_characters.add(instance)
                    if isinstance(instance, LocationInstance):
                        logger.debug("updating locations...")
                        story_node.assoc_locations.add(instance)
        else:
            # We already have the arc_element_node
            logger.debug('Scanning arcnode instance...')
            if instance.story_element_node:
                logger.debug("found story node to update...")
                story_node = instance.story_element_node
                if sender == ArcElementNode.assoc_characters.through:
                    logger.debug('Adding character')
                    story_node.assoc_characters.add(*pk_set)
                if sender == ArcElementNode.assoc_locations.through:
                    logger.debug('Adding locations')
                    story_node.assoc_locations.add(*pk_set)


@receiver(post_save, sender=ArcElementNode)
def story_node_add_arc_element_update_characters_locations(sender, instance, created, *args, **kwargs):
    '''
    If an arc element is added to a story element node, add any missing elements or locations.
    '''
    arc_node = ArcElementNode.objects.get(pk=instance.pk)
    logger.debug('Scanning arc_node %s' % arc_node)
    if arc_node.arc_element_type == 'root':
        logger.debug("root node. skipping...")
    else:
        logger.debug('Checking arc node for story element relationship...')
        if arc_node.story_element_node:
            logger.debug('Found a story element node for arc element...')
            # This change was initiated by the arc element node as opposed to the story node.
            story_node = arc_node.story_element_node
            if arc_node.assoc_characters.count() > 0:
                logger.debug('Found %d characters to add...' % arc_node.assoc_characters.count())
                for character in arc_node.assoc_characters.all():
                    story_node.assoc_characters.add(character)
            if arc_node.assoc_locations.count() > 0:
                logger.debug('Found %d locations to add...' % arc_node.assoc_locations.count())
                for location in arc_node.assoc_locations.all():
                    story_node.assoc_locations.add(location)


@receiver(pre_save, sender=ArcElementNode)
def validate_arc_links_same_outline(sender, instance, *args, **kwargs):
    '''
    Evaluates attempts to link an arc to a story node from another outline.
    '''
    if instance.story_element_node:
        if instance.story_element_node.outline != instance.parent_outline:
            raise IntegrityError(_('An arc cannot be associated with an story element from another outline.'))


@receiver(m2m_changed, sender=ArcElementNode.assoc_characters.through)
def validate_character_instance_valid_for_arc(sender, instance, action, reverse, pk_set, *args, **kwargs):
    '''
    Evaluate attempts to assign a character instance to ensure it is from same
    outline.
    '''
    if action == 'pre_add':
        if reverse:
            # Fetch arc definition through link.
            for apk in pk_set:
                arc_node = ArcElementNode.objects.get(pk=apk)
                if arc_node.parent_outline != instance.outline:
                    raise IntegrityError(_('Character Instance and Arc Element must be from same outline.'))
        else:
            for cpk in pk_set:
                char_instance = CharacterInstance.objects.get(pk=cpk)
                if char_instance.outline != instance.parent_outline:
                    raise IntegrityError(_('Character Instance and Arc Element must be from the same outline.'))


@receiver(m2m_changed, sender=ArcElementNode.assoc_locations.through)
def validate_location_instance_valid_for_arc(sender, instance, action, reverse, pk_set, *args, **kwargs):
    '''
    Evaluates attempts to add location instances to arc, ensuring they are from same outline.
    '''
    if action == 'pre_add':
        if reverse:
            # Fetch arc definition through link.
            for apk in pk_set:
                arc_node = ArcElementNode.objects.get(pk=apk)
                if arc_node.parent_outline != instance.outline:
                    raise IntegrityError(_('Location instance must be from same outline as arc element.'))
        else:
            for lpk in pk_set:
                loc_instance = LocationInstance.objects.get(pk=lpk)
                if loc_instance.outline != instance.parent_outline:
                    raise IntegrityError(_('Location Instance must be from the same outline as arc element.'))


@receiver(m2m_changed, sender=StoryElementNode.assoc_characters.through)
def validate_character_for_story_element(sender, instance, action, reverse, pk_set, *args, **kwargs):
    '''
    Validates that character is from the same outline as the story node.
    '''
    if action == 'pre_add':
        if reverse:
            for spk in pk_set:
                story_node = StoryElementNode.objects.get(pk=spk)
                if instance.outline != story_node.outline:
                    raise IntegrityError(_('Character Instance must be from the same outline as story node.'))
        else:
            for cpk in pk_set:
                char_instance = CharacterInstance.objects.get(pk=cpk)
                if char_instance.outline != instance.outline:
                    raise IntegrityError(_('Character Instance must be from the same outline as story node.'))


@receiver(m2m_changed, sender=StoryElementNode.assoc_locations.through)
def validate_location_for_story_element(sender, instance, action, reverse, pk_set, *args, **kwargs):
    '''
    Validates that location is from same outline as story node.
    '''
    if action == 'pre_add':
        if reverse:
            for spk in pk_set:
                story_node = StoryElementNode.objects.get(pk=spk)
                if instance.outline != story_node.outline:
                    raise IntegrityError(_('Location must be from same outline as story node.'))
        else:
            for lpk in pk_set:
                loc_instance = LocationInstance.objects.get(pk=lpk)
                if instance.outline != loc_instance.outline:
                    raise IntegrityError(_('Location must be from the same outline as story node.'))


@receiver(tree_manipulation, sender=StoryElementNode)
def validate_generations_for_story_elements(
        sender,
        instance,
        action,
        target_node_type=None,
        target_node=None,
        pos=None,
        *args,
        **kwargs
):
    '''
    Unlike arc nodes, for which we just warn about structure, the story tree
    allowed parent/child rules must be strictly enforced.
    '''
    if action == 'add_child':
        if instance.story_element_type not in STORY_NODE_ELEMENT_DEFINITIONS[target_node_type]['allowed_parents']:
            raise IntegrityError(_('%s is not an allowed child of %s' % (target_node_type,
                                                                         instance.story_element_type)))
    if action == 'update':
        parent = instance.get_parent()
        children = instance.get_children()
        if parent.story_element_type not in STORY_NODE_ELEMENT_DEFINITIONS[target_node_type]['allowed_parents']:
            raise IntegrityError(_('%s is not an allowed child of %s' % (target_node_type, parent.story_element_type)))
        if children:
            for child in children:
                if target_node_type not in STORY_NODE_ELEMENT_DEFINITIONS[child.story_element_type]['allowed_parents']:
                    raise IntegrityError(_('%s is not permitted to be a parent of %s' % (
                        target_node_type, child.story_element_type)))
    if action == 'add_sibling':
        parent = instance.get_parent()
        if parent.story_element_type not in STORY_NODE_ELEMENT_DEFINITIONS[target_node_type]['allowed_parents']:
            raise IntegrityError(_('%s is not an allowed child of %s' % (target_node_type, parent.story_element_type)))
    if action == 'move':
        if not pos or 'sibling' in pos or 'right' in pos or 'left' in pos:
            parent = target_node.get_parent()
            if (parent.story_element_type not in
                STORY_NODE_ELEMENT_DEFINITIONS[instance.story_element_type]['allowed_parents']):
                raise IntegrityError(_('%s is not an allowed child of %s' % (
                    instance.story_element_type,
                    parent.story_element_type
                )))
        if 'child' in pos:
            if (target_node.story_element_type not in
                STORY_NODE_ELEMENT_DEFINITIONS[instance.story_element_type]['allowed_parents']):
                raise IntegrityError(_('%s is not an allowed child of %s' % (
                    instance.story_element_type,
                    target_node.story_element_type
                )))


@receiver(tree_manipulation, sender=ArcElementNode)
def validate_against_prohibited_actions(
        sender,
        instance,
        action,
        target_node_type=None,
        target_node=None,
        pos=None,
        *args,
        **kwargs):
    if action == 'update' and 'mile' in target_node_type:
        milestones = ArcElementNode.objects.filter(
            arc=instance.arc,
            arc_element_type=instance.arc_element_type
        ).exclude(pk=instance.pk).count()
        if milestones:
            raise ArcIntegrityError(_("You cannot have two of the same milestone within the same arc."))

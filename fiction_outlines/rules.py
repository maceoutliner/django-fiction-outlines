'''
Permission definitions for fiction_outlines
'''

import rules


# First we define our predicates.

@rules.predicate
def is_outline_owner(user, outline):
    return outline.user == user


@rules.predicate
def is_series_owner(user, series):
    return series.user == user


@rules.predicate
def is_character_owner(user, character):
    return character.user == user


@rules.predicate
def is_location_owner(user, location):
    return location.user == user


@rules.predicate
def is_arc_owner(user, arc):
    return arc.outline.user == user


@rules.predicate
def is_arc_element_node_owner(user, arc_node):
    return arc_node.arc.outline.user == user


@rules.predicate
def is_story_node_owner(user, story_node):
    return story_node.outline.user == user


@rules.predicate
def is_character_instance_owner(user, character_instance):
    return character_instance.character.user == user


@rules.predicate
def is_location_instance_owner(user, location_instance):
    return location_instance.location.user == user


rules.add_perm('fiction_outlines.view_outline', is_outline_owner)
rules.add_perm('fiction_outlines.edit_outline', is_outline_owner)
rules.add_perm('fiction_outlines.delete_outline', is_outline_owner)
rules.add_perm('fiction_outlines.view_character', is_character_owner)
rules.add_perm('fiction_outlines.edit_character', is_character_owner)
rules.add_perm('fiction_outlines.delete_character', is_character_owner)
rules.add_perm('fiction_outlines.view_location', is_location_owner)
rules.add_perm('fiction_outlines.edit_location', is_location_owner)
rules.add_perm('fiction_outlines.delete_location', is_location_owner)
rules.add_perm('fiction_outlines.view_series', is_series_owner)
rules.add_perm('fiction_outlines.edit_series', is_series_owner)
rules.add_perm('fiction_outlines.delete_series', is_series_owner)
rules.add_perm('fiction_outlines.add_character_to_series', is_character_owner & is_series_owner)
rules.add_perm('fiction_outlines.add_location_to_series', is_location_owner & is_series_owner)
rules.add_perm('fiction_outlines.add_character_instance', is_character_owner)
rules.add_perm('fiction_outlines.view_character_instance', is_character_instance_owner)
rules.add_perm('fiction_outlines.edit_character_instance', is_character_instance_owner)
rules.add_perm('fiction_outlines.delete_character_instance', is_character_instance_owner)
rules.add_perm('fiction_outlines.add_location_instance', is_location_owner & is_outline_owner)
rules.add_perm('fiction_outlines.view_location_instance', is_location_instance_owner)
rules.add_perm('fiction_outlines.edit_location_instance', is_location_instance_owner)
rules.add_perm('fiction_outlines.delete_location_instance', is_location_instance_owner)
rules.add_perm('fiction_outlines.add_arc', is_outline_owner)
rules.add_perm('fiction_outlines.view_arc', is_arc_owner)
rules.add_perm('fiction_outlines.edit_arc', is_arc_owner)
rules.add_perm('fiction_outlines.delete_arc', is_arc_owner)
rules.add_perm('fiction_outlines.add_arc_node', is_arc_owner)
rules.add_perm('fiction_outlines.view_arc_node', is_arc_element_node_owner)
rules.add_perm('fiction_outlines.edit_arc_node', is_arc_element_node_owner)
rules.add_perm('fiction_outlines.delete_arc_node', is_arc_element_node_owner)
rules.add_perm('fiction_outlines.add_story_node', is_outline_owner)
rules.add_perm('fiction_outlines.view_story_node', is_story_node_owner)
rules.add_perm('fiction_outlines.edit_story_node', is_story_node_owner)
rules.add_perm('fiction_outlines.delete_story_node', is_story_node_owner)

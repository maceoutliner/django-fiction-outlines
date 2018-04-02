'''
Custom signals sent by this app.

Current list:

tree_manipulation: Sent when either the ArcElementNode or StoryElementNode trees have their structure manipulated.
'''

from django.dispatch import Signal

tree_manipulation = Signal(providing_args=['action', 'target_node_type', 'target_node', 'pos'])

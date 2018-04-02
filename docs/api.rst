.. _apiref:

======
API
======

.. module:: fiction_outlines.models

------
Models
------

There are two types of models used in Fiction Outlines, Standard and Tree. 

Standard
========

Standard models are rather typical Django models and so the API is much as you would expect. 

.. _Series:

.. autoclass:: Series
   :show-inheritance:

This model represents a story series that can hold one or more outlines within it. it is not necessary to define a Series, but it is a useful organizational tool. Standard Django ORM applies.

.. _Character:

.. autoclass:: Character
   :show-inheritance:

This model represents a character that may be reused in multiple series, outlines, and story elements.

.. _`CharacterInstance`:

.. autoclass:: CharacterInstance
   :show-inheritance:

This model represents a single instance of a character that is associated with an Outline. Contains additional metadata on the character's role in the story.

.. _Location:

.. autoclass:: Location
   :show-inheritance:

This model represents a location that may be reused in multiple series, outlines, and story elements.

.. _LocationInstance:

.. autoclass:: LocationInstance
   :show-inheritance:

This model represents an instance of a location that is associated with an outline.

.. _Outline:

.. autoclass:: Outline
   :show-inheritance:

The outline is the manuscript level element that represents and encapsulates all the information about a specific work. It provides a number of convenient convenience features.

.. automethod:: Outline.length_estimate

   This is a cached property that calculates the projected total length of the manuscript.

   Example:

   .. code-block:: python

      o1.length_estimate
      # Returns estimated total words.

.. automethod:: Outline.story_tree_root

   Cached property that returns the root of the outline tree.

   Example:

   .. code-block:: python

      root_node = o1.story_tree_root

.. automethod:: Outline.refresh_from_db

   Just like Django's ``refresh_from_db()`` except that this clears the property cache of the object as well.

.. automethod:: Outline.create_arc

   Creates an Arc_ object within the outline, and builds the initial tree of ArcElementNode_ objects. Returns the Arc object.

   Example:

   .. code-block:: python

      arc1 = o1.create_arc(mace_type='event', name='Dragon Invasion')

.. automethod:: Outline.validate_nesting

   Evaluates the tree of StoryElementNode_ objects and returns a dict of errors if any are found. For each error entry, a list of offending nodes will also be included.

   Example:

   .. code-block:: python

      error_dict = o1.validate_nesting()
      if error_dict:
         # There are errors
         for key, value in error_dict.items():
             print("%s: %s" % (key, value)


.. _`Arc`:

.. autoclass:: Arc
   :show-inheritance:

The arc represents a story throughline that will be integrated with the outline.

.. automethod:: Arc.current_errors

   A cached property of current structural errors within the Arc.

.. automethod:: Arc.arc_root_node

   A cached property pointing to the root node of the ArcElementNode_ object tree.

.. automethod:: Arc.refresh_from_db

   Like the standard Django method, but this also clears cached properties.

.. automethod:: Arc.generate_template_arc_tree

   Creates the template arc tree using :ref:`7PSS`.

.. automethod:: Arc.fetch_arc_errors

   Evaluates the arc tree for errors the user is recommended to correct.

.. automethod:: Arc.validate_first_element

   Checks that the first child of the root is the Hook.

.. automethod:: Arc.validate_last_element

   Checks that the last child of the root is the Resolution.

.. automethod:: Arc.validate_generations

   Reviews the structure of the Arc to ensure that node types follow the `allowed_parents` and `allowed_children` properties.

.. automethod:: Arc.validate_milestones

   Verifies that milestones appear in the tree in the Arc tree in the correct sequence.

Tree Models
===========

Tree models are Materialized Path trees descended from the `django-treebeard` provided `MP_Node`.

.. note::
   A discussion of the details of working with MP trees is out of scope for this document. You are recommended to peruse `django-treebeard's excellent documentation`_. Make sure to also review ``fiction_outlines`` :ref:`caveats` documentation.

.. _`django-treebeard's excellent documentation`: http://django-treebeard.readthedocs.io/en/latest/

.. _`ArcElementNode`:

.. autoclass:: ArcElementNode
   :show-inheritance:

   This model represents the nodes of the tree that is used as the structure of the Arc_.

.. automethod:: ArcelementNode.milestone_seq
                
   Cached property retrieving the derived milestone sequence number as it relates to 7PSS_.

.. automethod:: ArcElementNode.is_milestone

   Cached property returning if this node represents an arc milestone.

.. automethod:: ArcElementNode.parent_outline

   Cached property for convenient access to the outline to which this arc tree belongs.

.. automethod:: ArcElementNode.move

   Subclass of the ``treebeard`` method. Fires a :ref:`tree_manipulation` signal for your use.

.. automethod:: ArcElementNode.add_child

   Subclasses the ``treebeard`` method to add required logic for instantiating an Arc Element object.

   Example:

   .. code-block:: python

      # Add a try/fail cycle
      new_element = ae1.add_child('tf', description="Attempting to get into the secret enclave to get information")

.. automethod:: ArcElementNode.add_sibling

   Subclasses the ``treebeard`` method to add specific model instantiation requirements.

   Example:

   .. code-block:: python

      # Add another beat that followed after another one
      beat2 = beat1.add_sibling('beat', description="John discovers an odd item in his bag.")

.. _`StoryElementNode`:

.. autoclass:: StoryElementNode
   :show-inheritance:

   This class represent the actual structure of the overall outline. Individual arc elements can be associated with a story node, which is how the outline validation tool can verify that :ref:`nesting` is valid.

.. automethod:: StoryElementNode.all_characters

   A property that returns queryset of all the unique character instances associated with this node, and any of its descendant nodes.

.. automethod:: StoryElementNode.all_locations

   A property that returns a queryset of all the unique location instances associated with this node, and any of its descendant nodes.

.. automethod:: StoryElementNode.impact_rating

   A property representing the impact/tension rating of this node (expressed as a `float`) in the outline. This rating is derived from associations with arc elements, with extra impact when mulitple arcs overlap in the same node. Impact also affects ancestor and descendant nodes with weakening influence the more generations away from the source node. However, impact bleed does not extend to sibling nodes.

.. automethod:: StoryElementNode.move

   Subclass of the ``treebeard`` move method, but also sends signal :ref:`tree_manipulation` which you can use with your signal receivers.

.. automethod:: StoryElementNode.add_child

   Subclass of the ``treebeard`` method, but adds instantiation logic for this model.

   Example:

   .. code-block:: python

      new_node = node.add_child(story_element_type='chapter', outline=o1, name='Chapter 1', description='Our story begins.')

.. automethod:: StoryElementNode.add_sibling

   Subclass of the ``treebeard`` method, but adds model instantiation logic.

   Example:

   .. code-block:: python

      chap2 = new_node.add_sibling(story_element_type='chapter', outline=o1, name='Chapter 2', description='Meanwhile, on the other side of the world')

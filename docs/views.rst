================
Views
================

.. module:: fiction_outlines.views

Views are provided for the majority of common tasks when working with fiction_outlines. Once again, these views are where the object permission model is enforced, so always subclass rather than just replace them.

For the most part, these operate as generic views and all the same functionality applies.

.. note::
   Basic templates for all of these views are provided, but it is expected that you will override them with your own as needed.

.. autoclass:: SeriesListView
   :show-inheritance:

.. autoclass:: SeriesDetailView
   :show-inheritance:

.. autoclass:: SeriesUpdateView
   :show-inheritance:

.. autoclass:: SeriesCreateView
   :show-inheritance:

.. autoclass:: SeriesDeleteView
   :show-inheritance:

.. autoclass:: CharacterListView
   :show-inheritance:

.. autoclass:: CharacterDetailView
   :show-inheritance:

.. autoclass:: CharacterUpdateView
   :show-inheritance:

.. autoclass:: CharacterCreateView
   :show-inheritance:

.. autoclass:: CharacterDeleteView
   :show-inheritance:

.. autoclass:: CharacterInstanceListView
   :show-inheritance:

.. autoclass:: CharacterInstanceDetailView
   :show-inheritance:

.. autoclass:: CharacterInstanceUpdateView
   :show-inheritance:

.. autoclass:: CharacterInstanceCreateView
   :show-inheritance:

.. autoclass:: CharacterInstanceDeleteView
   :show-inheritance:

.. autoclass:: LocationListView
   :show-inheritance:

.. autoclass:: LocationDetailView
   :show-inheritance:

.. autoclass:: LocationUpdateView
   :show-inheritance:

.. autoclass:: LocationCreateView
   :show-inheritance:

.. autoclass:: LocationDeleteView
   :show-inheritance:

.. autoclass:: LocationInstanceListView
   :show-inheritance:

.. autoclass:: LocationInstanceDetailView
   :show-inheritance:

.. autoclass:: LocationInstanceUpdateView
   :show-inheritance:

.. autoclass:: LocationInstanceCreateView
   :show-inheritance:

.. autoclass:: LocationInstanceDeleteView
   :show-inheritance:

.. autoclass:: OutlineListView
   :show-inheritance:

.. autoclass:: OutlineDetailView
   :show-inheritance:

.. autoclass:: OutlineUpdateView
   :show-inheritance:

.. autoclass:: OutlineCreateView
   :show-inheritance:

.. autoclass:: OutlineDeleteView
   :show-inheritance:

.. autoclass:: ArcListView
   :show-inheritance:

.. autoclass:: ArcDetailView
   :show-inheritance:

.. autoclass:: ArcUpdateView
   :show-inheritance:

.. autoclass:: ArcCreateView
   :show-inheritance:

.. autoclass:: ArcDeleteView
   :show-inheritance:

.. autoclass:: ArcNodeDetailView
   :show-inheritance:

.. autoclass:: ArcNodeUpdateView
   :show-inheritance:

.. autoclass:: ArcNodeCreateView
   :show-inheritance:

.. autoclass:: ArcNodeDeleteView
   :show-inheritance:

   Incorporates logic to ensure that if the node represents the Hook or Resolution of the :ref:`7PSS`, it cannot be deleted.

.. autoclass:: ArcNodeMoveView
   :show-inheritance:

.. autoclass:: StoryNodeCreateView
   :show-inheritance:

.. autoclass:: StoryNodeMoveView
   :show-inheritance:

.. autoclass:: StoryNodeDetailView
   :show-inheritance:

.. autoclass:: StoryNodeUpdateView
   :show-inheritance:

   Will add additional form errors if it is attempted to edit the ``story_element_type`` in a manner which would break the structure of the outline.

.. autoclass:: StoryNodeCreateView
   :show-inheritance:

.. autoclass:: StoryNodeDeleteView
   :show-inheritance:

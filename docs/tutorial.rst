==========
Tutorial
==========

When working with Django fiction outlines, it is important to understand that it is an opinionated library, and leans heavily on three concepts.

.. _concepts:

Concepts
--------

.. _maceq:

M.A.C.E. Quotient
~~~~~~~~~~~~~~~~~

The principle that each story thread (or arc) is one of four primary types.
   * Milieu: About the journey through a place.
   * Answers: A question or mystery that must be answered.
   * Character: The journey and change within a character for better or worse.
   * Event: An external event that must be dealt with.

This is author `Mary Robinette Kowal's`_ version of Orson Scott Card's orgiinal `M.I.C.E. quotient`_, and I think her version is easier to follow.

.. _Mary Robinette Kowal's: http://www.writingexcuses.com/tag/mace-quotient/

.. _M.I.C.E. quotient: http://www.writersdigest.com/writing-articles/by-writing-goal/write-first-chapter-get-started/4-story-structures-that-dominate-novels

.. _nesting:

Nesting
~~~~~~~

Again, `from Kowal`_, that story threads, regardless of MACE type, should be resolved in the opposite order in which they were introduced. Last in, first out. [#mslen]_

.. [#mslen] Savvy watchers of this lecture will note that ``fiction_outlines`` also draws its formula for estimating overall manuscript length from Kowal as well.

.. _from Kowal: https://youtu.be/yAJT_-gpG4U

.. _7PSS:

Seven Point Story Structure
~~~~~~~~~~~~~~~~~~~~~~~~~~~

This one comes from author Dan Wells, whose `talk on story structure`_ has helped countless writers out there. Essentially, a well-crafted arc consists of seven milestones:

.. _talk on story structure: https://www.youtube.com/watch?v=KcmiqQ9NpPE

1. Hook: the starting state.
2. Plot Turn 1: What changes that starts this part of the story?
3. Pinch 1: The first **major** road block faced along the path.
4. Midpoint: The halfway mark.
5. Pinch 2: The great challenge. All seems lost.
6. Plot Turn 2: What change or realization occurs to make the resolution possible.
7. Resolution: Completion of the arc. Should be the opposite state of the hook.

Try/Fail cycles should be inserted in-between milestones to direct the pacing and ensure the story earns its milestone moments.

Intro to ``fiction_outlines`` Models
------------------------------------

First Tier Models
~~~~~~~~~~~~~~~~~

There are four elements in ``fiction_outlines`` from which everything else descends. Those are:

1. :ref:`Outline <Outline>`: The actual outline container object.
2. :ref:`Series <Series>`: A collection of related outlines and other objects.
3. :ref:`Character <Character>`: A single character which can in turn be used in multiple series and outlines.
4. :ref:`Location <Location>`: Settings/locations which can in turn be used in multiple series and outlines.

The purpose of each should be relatively clear.

Second Tier Models
~~~~~~~~~~~~~~~~~~

1. :ref:`CharacterInstance <CharacterInstance>`: A related record for a character with an individual outline. Contains additional metadata as to the character's role in the outline.
2. :ref:`LocationInstance <LocationInstance>`: Same as a CharacterInstance, but for Location.
3. :ref:`StoryElementNode <StoryElementNode>`: This model makes up the actual outline elements for the story. It descends from the outline, and represents the structure of the story using a materialized path tree.
4. :ref:`Arc <Arc>`: A story arc, associated with a single MACE type. An outline can have 1 to *n* arcs. For example, a short story may only have one arc, but a novel will have many. An arc is expected to conform to seven point story structure, and its default state will consist of those milestones.
  a. :ref:`ArcElementNode <ArcElementNode>`: This model represents the nodes of the materialized path tree describing all the points of the arc. One of more character or location instances may be associated with each node. In turn, an arc element node can be associated with a StoryElementNode allowing the outliner to visualize the overall story structure of the entire outline.

Usage
-----

Let's say you want to represent a user who is outlining a new series. We'll call them ``user1``.

.. code-block:: python

   series = Series(
                title='My new franchise',
                description='This is gonna be the next Harry Potter, I just know it.',
                tags='urban fantasy, high hopes',
                user=user1
   )
   series.save()
   my_outline = Outline(
                title='It begins',
                description='A twenty-something discovers that they are the chosen one to defend the city against all harm.',
                tags='heroine, fae',
                user=user1
   )
   my_outline.save()
   # You now have the series and outline, and can proceed to add arcs or start working at the overall plot level.
   main_arc = my_outline.create_arc(name='Chosen One', mace_type='character', description='Coming into her own')
   # The above command, creates the arc instance and also generates the initial skeleton of the arc using seven
   # point story structure.

   # Let's add a character.
   samantha = Character(
                name='Samantha Cowler',
                description='A cyncial and disaffected young woman destined to be a hero',
                tags='heroine',
                user=user1
   )
   samantha.save()
   samantha_first_book = CharacterInstance(character=samantha, outline=my_outline, pov_character=True, protagonist=True, main_character=True)
   samantha_first_book.save()
   # Add a location
   sam_job = Location(name='The Damn Bar', description='The tavern where Samantha works.', tags='human, normality', user=user1)
   sam_job.save()
   sam_job_first_book = LocationInstance(location=sam_job, outline=my_outline)
   sam_job_first_book.save()
   # Want to fetch the arc or story structure?
   arc_tree = arc.arc_root_node.get_descendants()
   story_tree = my_outline.story_tree_root.get_descendants()

For more detail on how to work with these objects, please review the :ref:`apiref <API reference>`.

NOTE: It is almost always better to use ``fiction_outlines``\' provided :ref:`views` as opposed to manually manipulating the models. The views make working with the objects less complex, and also provide an object-level security model. If you must work with them directly, it is recommended that you subclass the view itself and make your modifications there.

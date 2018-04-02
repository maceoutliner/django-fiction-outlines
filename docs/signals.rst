.. _`signals`:

=============
Signals
=============

.. _`tree_manipulation`:

tree_manipulation
-----------------
   Fires off a signal on tree manipulation, e.g. a ``move()`` method. Sends the following:

  +-------------------+----------------+------------------------+
  |     Variable      |Description     |Allowed values          |
  |                   |                |                        |
  +===================+================+========================+
  |      action       |What tree       |add\_child              |
  |                   |manipulation    |                        |
  |                   |method was      |add\_sibling            |
  |                   |called?         |                        |
  |                   |                |move                    |
  |                   |                |                        |
  |                   |                |update                  |
  +-------------------+----------------+------------------------+
  |target\_node\_type |Class of the    |If a                    |
  |                   |target node.    |``StoryElementNode``,   |
  |                   |                |this will be the value  |
  |                   |                |of                      |
  |                   |                |``story_element_type``. |
  |                   |                |                        |
  |                   |                |If an                   |
  |                   |                |``ArcElementNode``, it  |
  |                   |                |will be the value of    |
  |                   |                |``arc_element_type``.   |
  |                   |                |                        |
  |                   |                |                        |
  +-------------------+----------------+------------------------+
  |   target\_node    |The node to     |If this is a move       |
  |                   |which this is   |action, this will be    |
  |                   |being move in   |populated with the      |
  |                   |relation to.    |target node for the     |
  |                   |                |move.                   |
  +-------------------+----------------+------------------------+
  |        pos        |Position        |left                    |
  |                   |relative to the |                        |
  |                   |target\_node    |right                   |
  |                   |that this cell  |                        |
  |                   |should be added |first-child             |
  |                   |to. Only        |                        |
  |                   |populated when  |last-child              |
  |                   |action is equal |                        |
  |                   |to ``move``.    |first-sibling           |
  |                   |                |                        |
  |                   |                |last-sibling            |
  |                   |                |                        |
  +-------------------+----------------+------------------------+


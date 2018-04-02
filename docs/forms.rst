===========
Forms
===========

.. module:: fiction_outlines.forms

.. _forms:

Model forms are provided for convenience and can be fed specific kwargs in order to ensure that users are not presented with choices that should not be permitted.

.. autoclass:: CharacterInstanceForm
   :show-inheritance:

   Takes an additional kwarg of ``character`` which should represent a :ref:`Character` instance.

.. autoclass:: LocationInstanceForm
   :show-inheritance:

   Takes an additional kwarg of ``location`` which should represent an instance of :ref:`Location`.

.. autoclass:: CharacterForm
   :show-inheritance:

   Takes an additional kwarg of ``user`` which should represent an instance of ``AUTH_USER_MODEL``.

.. autoclass:: LocationForm
   :show-inheritance:

   Takes an additional kwarg of ``user`` which should represent an instance of ``AUTH_USER_MODEL``.

.. autoclass:: OutlineForm
   :show-inheritance:

   Takes an additional kwarg of ``user`` which should represent an instance of ``AUTH_USER_MODEL``.

.. autoclass:: OutlineMoveNodeForm
   :show-inheritance:

   .. warning::

   It is recommended that you do not subclass or directly call this form, but instead use `treebeard.forms.movenodeform_factory`_.

   .. _`treebeard.forms.movenodeform_factory`: http://django-treebeard.readthedocs.io/en/latest/forms.html#treebeard.forms.movenodeform_factory

   Example:

      .. code-block:: python

         from treebeard.forms import movenodeform_factory
         from fiction_outlines import forms
         from fiction_outlines.views import ArcNodeMoveView

         class SomeFormOrModelView(ArcNodeMoveView):

             model = ArcElementNode  # As an example
             form_class = movenodeform_factory(ArcElementNode, form=forms.OutlineMoveNodeForm, ...)
             ...



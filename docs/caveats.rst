.. _Caveats:

==========
Caveats
==========

Be aware that as tree models are descendents of the ``django-treebeard`` ``MP_Node`` class, the same `Known Caveats`_ apply.

.. _`Known Caveats`: http://django-treebeard.readthedocs.io/en/latest/caveats.html

.. warning::
   - Do **NOT** attempt to create a new node using the Django-provided construction method. Use dedicated methods such as ``add_root``, ``add_child``, and ``add_sibling`` instead. 
   - Do **NOT** attempt to directly edit ``path``, ``step``, ``depth``, ``num_child``, etc. Use the provided `move` method. 
   - ``MP_Node`` uses a lot of raw SQL, so always retrieve the node from the db again after tree manipulation before calling it to do anything else. 
   - Object permissions come from `django-rules`_, and the permission logic lies in the view layer. If you want to introduce your own custom logic, you should subclass the provided views in order to reduce the risk of security breaches.
   - For the same reason, if you must define a custom manager, you **NEED** to subclass ``treebeard``'s base ``MP_Node`` manager.

.. _`django-rules`: https://github.com/dfunckt/django-rules

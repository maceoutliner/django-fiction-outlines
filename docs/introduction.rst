==============
Introduction
==============

Welcome to Django Fiction Outlines!

Being a reusable Django app for managing fiction outlines. Part of the broader `maceoutliner`_ project.

.. _maceoutliner: https://github.com/maceoutliner/

Documentation
-------------

The full documentation is at https://django-fiction-outlines.readthedocs.io.

Code Repo and Issue Tracker
---------------------------

The code repository and issue list for this project can be found at `Github`_.

.. _Github: https://github.com/maceoutliner/django-fiction-outlines/

License
-------

:ref:`BSD` for your convenience.


Features
--------

* Provides models for managing series, outlines, characters, locations, and arcs.
* Provides tools for managing multiple arcs within the context of a broader story outline.
* Validates that arcs and outlines follow principles of MACE nesting, and seven point story structure.
* Calculates estimated length of final manuscript based on complexity of outline.
* Objects are associated with users to enable permission management.
* Export outlines to OPML, JSON, or Markdown documents.

  * NOTE: Django Fiction Outlines uses an object permission manager called `django-rules`_. This allows extremely flexible permission schemes without crufting up your database or model logic. By default, `fiction_outlines` will restrict any view or editing to the owner of the object. 
    
.. _django-rules: https://github.com/dfunckt/django-rules

What It Doesn't Do
------------------

* Provide a full UI for managing the changes. An API and views are provided, but templates are very basic. It is expected that you will override the templates to match your overall project.
* Outline the whole story for you.
* Write the story for you.
* Do your laundry.

Running Tests
-------------

Does the code actually work?

::

    $ pip install -r test_requirements.txt 
    $ pytest
    $ pytest --flake8

Credits
-------

Tools used in rendering this package:

*  Cookiecutter_
*  `cookiecutter-djangopackage`_

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`cookiecutter-djangopackage`: https://github.com/pydanny/cookiecutter-djangopackage

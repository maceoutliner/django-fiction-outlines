=============================
Django Fiction Outlines
=============================

.. image:: https://badge.fury.io/py/django-fiction-outlines.svg
    :target: https://badge.fury.io/py/django-fiction-outlines

.. image:: https://github.com/maceoutliner/django-fiction-outlines/actions/workflows/tests.yml/badge.svg?branch=master
   :target: https://github.com/maceoutliner/django-fiction-outlines/actions/workflows/tests.yml

.. image:: https://coveralls.io/repos/github/maceoutliner/django-fiction-outlines/badge.svg?branch=master
        :target: https://coveralls.io/github/maceoutliner/django-fiction-outlines?branch=master

.. image:: https://readthedocs.org/projects/django-fiction-outlines/badge/?version=latest
        :target: http://django-fiction-outlines.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

A reusable Django app for managing fiction outlines. Part of the broader maceoutliner project.

Documentation
-------------

The full documentation is at https://django-fiction-outlines.readthedocs.io.

Quickstart
----------

Install Django Fiction Outlines::

    pip install django-fiction-outlines

Add it and dependencies to your `INSTALLED_APPS`:

.. code-block:: python

    INSTALLED_APPS = (
        ...
        'taggit',
        'rules.apps.AutodiscoverRulesConfig',
        'fiction_outlines',
        ...
    )

Add rules_ to your `AUTHENTICATION_BACKENDS`:

.. code-block:: python

   AUTHENTICATION_BACKENDS = (
       'rules.permissions.ObjectPermissionBackend',
       'django.contrib.auth.backends.ModelBackend',
   )

Unless you like to live dangerously, it is **STRONGLY** recommend you configure whichever database you use for outlines to have ``ATOMIC_REQUESTS`` to ``True``.

.. code-block:: python

   DATABASES = {
       "default": {
           "ENGINE": "django.db.backends.postgresql",
           "NAME": "outlines",
           "ATOMIC_REQUESTS": True,
       }}

.. _rules: https://github.com/dfunckt/django-rules

Add Django Fiction Outlines's URL patterns:

.. code-block:: python

    from fiction_outlines import urls as fiction_outlines_urls


    urlpatterns = [
        ...
        url(r'^', include(fiction_outlines_urls)),
        ...
    ]


Features
--------

* Provides models for managing series, outlines, characters, locations, and arcs.
* Provides tools for managing multiple arcs within the context of a broader story outline.
* Validates that arcs and outlines follow principles of MACE nesting, and seven point story structure.
* Calculates estimated length of final manuscript based on complexity of outline.
* Objects are associated with users to enable permission management.

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

============
Installation
============

At the command line::

    $ easy_install django-fiction-outlines

Or, if you have virtualenvwrapper installed::

    $ mkvirtualenv django-fiction-outlines
    $ pip install django-fiction-outlines
    
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

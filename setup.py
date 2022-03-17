#!/usr/bin/env python

import os
import re
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


def get_version(*file_paths):
    """Retrieves the version from fiction_outlines/__init__.py"""
    filename = os.path.join(os.path.dirname(__file__), *file_paths)
    version_file = open(filename).read()
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError('Unable to find version string.')


version = get_version("fiction_outlines", "__init__.py")


if sys.argv[-1] == 'publish':
    try:
        import wheel
        print("Wheel version: ", wheel.__version__)
    except ImportError:
        print('Wheel library missing. Please run "pip install wheel"')
        sys.exit()
    os.system('python setup.py sdist upload')
    os.system('python setup.py bdist_wheel upload')
    sys.exit()

if sys.argv[-1] == 'tag':
    print("Tagging the version on git:")
    os.system("git tag -a %s -m 'version %s'" % (version, version))
    os.system("git push --tags")
    sys.exit()

readme = open('README.rst').read()
history = open('HISTORY.rst').read().replace('.. :changelog:', '')

setup(
    name='django-fiction-outlines',
    version=version,
    description="""A reusable Django app for managing fiction outlines. Part of the broader maceoutliner project.""",
    long_description=readme + '\n\n' + history,
    author='Daniel Andrlik',
    author_email='daniel@andrlik.org',
    url='https://github.com/maceoutliner/django-fiction-outlines',
    packages=[
        'fiction_outlines',
    ],
    include_package_data=True,
    install_requires=[
        'django-braces>=1.15.0',
        'django-model-utils>=4.2.0',
        'django-taggit>=2.1.0',
        'django-treebeard>=4.5.1',
        'django>=3.2.12',
        'pytz',
        'rules>=3.2.1',
    ],
    license="BSD",
    zip_safe=False,
    keywords='django-fiction-outlines',
    project_urls={
        'Documentation': 'http://django-fiction-outlines.readthedocs.io/en/latest/index.html',
        'Source': 'https://github.com/maceoutliner/django-fiction-outlines/',
        'Issue Tracker': 'https://github.com/maceoutliner/django-fiction-outlines/issues',
    },
    python_requires='~=3.6',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
)

"""PyLinks: Create, Modify and Manage URLs in Python.

PyLinks implements a URL object, making it easy to create, manipulate and work with URLs.
It also offers a number of URL generators for popular online platforms
such as GitHub, PyPI, Anaconda, ReadTheDocs etc., allowing for facile and dynamic
creation of many useful links.

To create a URL, use the `url` function; it is located in the `url` module,
but can be used directly from the root. It returns a URL object, also defined in the `url` module.

Other available modules offer shortcuts for creating useful URLs for popular online services.
"""

OFFLINE_MODE: bool = False
"""Global variable to set whether URL generators should verify the created URLs online."""


from .url import url
from . import binder, conda, github, pypi, readthedocs
from .http import request


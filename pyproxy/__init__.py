"""
This module defines the version of the application. It contains a single constant
that holds the current version number of the application.
"""

import os

__version__ = "0.5.1"

if os.path.isdir("pyproxy/monitoring"):
    __slim__ = False
else:
    __slim__ = True

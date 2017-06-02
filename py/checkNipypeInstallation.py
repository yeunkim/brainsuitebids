# -*- coding: utf-8 -*-
"""
checkNipypeInstallation.py

Checks that nipype import works, and that brainsuite interface import works
Handles printing out error messages
exit(1) on error, exit(0) on success

"""

from __future__ import unicode_literals, print_function

try:
    from builtins import str
except:
    print("Error: builtins module not found. You can install it with: pip install future")
    exit(1)

try:
    import nipype
except:
    print("Error: Could not import Nipype module in python script. Check installation. Exiting")
    exit(1)

try:
    import nipype.interfaces.brainsuite as bs
except:
    print("Error: Could not import BrainSuite Nipype interface in python scrit. Upgrade Nipype package to latest version.")
    exit(1)

exit(0)


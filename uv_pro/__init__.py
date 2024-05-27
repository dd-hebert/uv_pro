"""
uv_pro
======
A tool for processing UV-vis data files (.KD or .csv formats) exported from the
Agilent 845x UV-vis Chemstation software. UV-vis data files in either .KD or
.csv formats can be imported, processed, and exported as .csv.

You can run uv_pro directly from the command line using::

    uvp -p <"path"> <optional_args>

Or you can run uv_pro using runpy with::

    python -m uv_pro -p <"path"> <optional_args>

See the documentation or the uv_pro.scripts.cli docstring from more information
on the optional command line arguments.

github: https://github.com/dd-hebert/uv_pro

@author: David Hebert
"""
__author__ = 'David Hebert'
__version__ = '0.4.1'

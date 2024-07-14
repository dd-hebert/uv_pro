# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys
from sphinx.ext.autodoc import cut_lines

sys.path.insert(0, os.path.abspath(".."))

project = 'uv_pro'
copyright = '2023, David Hebert'
author = 'David Hebert'
release = '0.5.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    # "autoapi.extension",
    # "autoclasstoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "sphinx.ext.autosectionlabel"
]

def setup(app):
    app.connect('autodoc-process-docstring', cut_lines(0, 1, what=['module']))

napoleon_include_init_with_doc = True

# autoapi_type = 'python'
# autoapi_dirs = ['../uv_pro']
# autoapi_options = [
#     'members',
#     'inherited-members',
#     # 'undoc-members', # show objects that do not have doc strings
#     # 'private_members', # show private objects (_variable)
#     # 'show-inheritance',
#     'show-module-summary',
#     # 'special-members', # show things like __str__
#     # 'imported-members', # document things imported within each module
# ]
# autoapi_member_order = 'groupwise' # groups into classes, functions, etc.
# autoapi_python_class_content = 'class' # include class docstring from class and/or __init__

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# Links to outside documentation for the intersphinx extension.
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'numpy': ('https://numpy.org/doc/stable/', None),
    'pandas': ('https://pandas.pydata.org/docs/', None),
    'pybaselines': ('https://pybaselines.readthedocs.io/en/latest/', None)
}

# Cache remote doc inventories for 14 days.
intersphinx_cache_limit = 14

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_favicon = 'favicon.ico'

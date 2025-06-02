"""
Functions for the ``tree`` command.

@author: David Hebert
"""

import argparse

from uv_pro.commands import command
from uv_pro.utils.filepicker import FilePicker


@command()
def tree(args: argparse.Namespace) -> None:
    """
    Parser Info
    -----------
    *desc : Show the root directory file tree.
    *help : Show the root directory file tree.
    """
    if args.root_directory:
        FilePicker(args.root_directory, '.KD').tree()

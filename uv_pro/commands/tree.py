"""
Functions for the ``tree`` command.

@author: David Hebert
"""
import argparse
from uv_pro.utils.filepicker import FilePicker


def tree(args: argparse.Namespace) -> None:
    if args.root_dir:
        FilePicker(args.root_dir, '.KD').tree()

"""
Functions for the ``browse`` command.

@author: David Hebert
"""
import argparse
from uv_pro.utils.filepicker import FilePicker
from uv_pro.commands.process import process


def browse(args: argparse.Namespace) -> None:
    if args.root_dir:
        if file := FilePicker(args.root_dir, '.KD').pick_file():
            args.path = file[0]
            args.view = True
            process(args)

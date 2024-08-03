"""
Functions for the ``browse`` command.

@author: David Hebert
"""
import argparse
from uv_pro.commands import command
from uv_pro.utils.filepicker import FilePicker
from uv_pro.commands.process import process


@command(aliases=['br'])
def browse(args: argparse.Namespace) -> None:
    """
    Parser Info
    -----------
    *aliases : br
    *desc : Browse for a .KD file in the root directory and open it in view-only mode.
    *help : Browse for a .KD file in the root directory and open it in view-only mode.
    """
    if args.root_dir:
        if file := FilePicker(args.root_dir, '.KD').pick_file():
            args.path = file[0]
            args.view = True
            process(args)

"""
Functions for the ``browse`` command.

@author: David Hebert
"""

import argparse
from pathlib import Path

from uv_pro.commands import command
from uv_pro.commands.process import process
from uv_pro.utils.prompts import select


def get_files_in_root_dir(root_dir: Path, ext: str = 'KD'):
    paths = sorted({str(p.relative_to(root_dir)) for p in root_dir.rglob(f'*.{ext}')}, key=str.lower)
    return paths


@command(aliases=['br'])
def browse(args: argparse.Namespace) -> None:
    """
    Parser Info
    -----------
    *aliases : br
    *desc : Browse for a .KD file in the root directory and open it in view-only mode.
    *help : Browse for a .KD file in the root directory and open it in view-only mode.
    """
    if args.root_directory:
        file = select(
            'Select a file:',
            choices=get_files_in_root_dir(Path(args.root_directory)),
            use_search_filter=True,
            use_jk_keys=False
        )

        if file is not None:
            args.path = file
            args.view = True
            args.list_colormaps = False
            process(args)

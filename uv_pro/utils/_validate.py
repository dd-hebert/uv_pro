"""
Helper functions for config file validation.

@author: David Hebert
"""

import argparse
import difflib
import re
from pathlib import Path

from rich import print

from uv_pro.const import CMAPS


def _error_msg(error_msg: str, verbose_msg: str, verbose: bool = False) -> bool:
    print(error_msg)
    if verbose:
        print(verbose_msg)
    return False


def validate_root_dir(root_dir: str, verbose: bool = False) -> bool:
    """Validate root_directory config setting. Return True if valid."""
    if root_dir == '' or Path(root_dir).exists():
        return True

    error_msg = (
        f'[repr.error]Config error:[/repr.error] Path "{root_dir}" does not exist.'
    )

    verbose_msg = 'Clearing root directory...'

    return _error_msg(error_msg, verbose_msg, verbose)


def validate_plot_size(plot_size: str, verbose: bool = False) -> bool:
    """Validate plot_size config setting. Return True if valid."""
    pattern = re.compile(r'^\s*(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s*$')
    if re.match(pattern, plot_size):
        return True

    error_msg = (
        f'[repr.error]Config error:[/repr.error] Plot size {plot_size} is invalid.'
    )

    verbose_msg = 'Resetting to plot size to default...'

    return _error_msg(error_msg, verbose_msg, verbose)


def validate_primary_color(color: str, verbose: bool = False) -> bool:
    """Validate plot_size config setting. Return True if valid."""
    valid_colors = {
        'red',
        'yellow',
        'green',
        'cyan',
        'blue',
        'magenta',
        'black',
    }
    if color in valid_colors:
        return True

    error_msg = (
        '[repr.error]Config error:[/repr.error] ',
        f'Primary color {color} is invalid.',
    )

    verbose_msg = 'Resetting to primary color to default...'

    return _error_msg(error_msg, verbose_msg, verbose)


def validate_colormap(name: str) -> str:
    if name in CMAPS.keys():
        return name

    suggestion = difflib.get_close_matches(name, CMAPS.keys(), n=1)
    message = f'Invalid colormap name: "{name}".'
    if suggestion:
        message += f' Did you mean "{suggestion[0]}"?'
    else:
        message += ' Run with `--list-colormaps` to list all available options.'
    raise argparse.ArgumentTypeError(message)

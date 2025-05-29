"""
Helper functions for config file validation.

@author: David Hebert
"""

import os
import re

from rich import print

def validate_root_dir(root_dir: str, verbose: bool = False) -> bool:
    """Validate root_directory config setting. Return True if valid."""
    if root_dir == '' or os.path.exists(root_dir):
        return True

    print(
        f'[repr.error]Config Error:[/repr.error]',
        f'[repr.error]Path [reset]{root_dir}[/reset] does not exist.[/repr.error]'
    )

    if verbose:
        print('Clearing root directory...')

    return False


def validate_plot_size(plot_size: str, verbose: bool = False) -> bool:
    """Validate plot_size config setting. Return True if valid."""
    pattern = re.compile(r'^\s*(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s*$')
    if re.match(pattern, plot_size):
        return True

    print(
        f'[repr.error]Config error:[/repr.error]',
        f'[repr.error]Plot size [reset]{plot_size}[/reset] is invalid.[/repr.error]',
    )

    if verbose:
        print('Resetting to plot size to default...')

    return False

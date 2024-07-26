"""
Helper functions for config file validation.

@author: David Hebert
"""

import os
import re


def validate_root_dir(root_dir: str, verbose: bool) -> bool:
    """Validate root_directory config setting. Return True if valid."""
    if root_dir == '' or os.path.exists(root_dir):
        return True

    print(f'Config Error: {root_dir} does not exist.')

    if verbose:
        print('Clearing root directory...')

    return False


def validate_plot_size(plot_size: str, verbose: bool) -> bool:
    """Validate plot_size config setting. Return True if valid."""
    pattern = re.compile(r'[\d]+\s+[\d]+')
    if re.match(pattern, plot_size):
        return True

    print(f'Config error: Plot size {plot_size} is invalid.')

    if verbose:
        print('Resetting to default...')

    return False

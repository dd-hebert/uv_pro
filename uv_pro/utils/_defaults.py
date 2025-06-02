"""
Config mapping and default values for uv_pro.

@author: David Hebert
"""

from pathlib import Path

from uv_pro.utils.paths import cleanup_path
from uv_pro.utils._validate import validate_plot_size, validate_primary_color, validate_root_dir

CONFIG_MAP = {
    'root_directory': {
        'section': 'Settings',
        'type': Path,
        'default_str': '',
        'default_val': None,
        'cleanup_func': cleanup_path,
        'validate_func': validate_root_dir,
    },
    'plot_size': {
        'section': 'Settings',
        'type': lambda x: tuple(map(float, x.split())),
        'default_str': '10 5',
        'default_val': (10, 5),
        'cleanup_func': lambda x: ' '.join(x.split()),
        'validate_func': validate_plot_size,
    },
    'primary_color': {
        'section': 'Settings',
        'type': str,
        'default_str': 'magenta',
        'default_val': 'magenta',
        'cleanup_func': str.strip,
        'validate_func': validate_primary_color,
    },
}

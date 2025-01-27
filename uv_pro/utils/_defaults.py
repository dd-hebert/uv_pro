"""
Config mapping and default values for uv_pro.
"""
from uv_pro.utils._validate import validate_root_dir, validate_plot_size

CONFIG_MAP = {
    'root_dir': {
        'section': 'Settings',
        'key': 'root_directory',
        'type': str,
        'default_str': '',
        'default_val': None,
        'validate_func': validate_root_dir
    },
    'plot_size': {
        'section': 'Settings',
        'key': 'plot_size',
        'type': lambda x: tuple(map(int, x.split())),
        'default_str': '10 5',
        'default_val': (10, 5),
        'validate_func': validate_plot_size
    },
}

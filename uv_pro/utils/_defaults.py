"""
Config mapping and default values for uv_pro.
"""

CONFIG_MAP = {
    'root_dir': {
        'section': 'Settings',
        'key': 'root_directory',
        'type': str,
        'default_str': '',
        'default_val': None
    },
    'plot_size': {
        'section': 'Settings',
        'key': 'plot_size',
        'type': lambda x: tuple(map(int, x.split())),
        'default_str': '10 5',
        'default_val': (10, 5)
    },
}

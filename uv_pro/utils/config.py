"""
Configuration handler for ``uv_pro``.

The config file is saved as ``settings.ini`` inside ``.config/uv_pro``, which
can be found in the user's home directory.

@author: David Hebert
"""

import os
from configparser import ConfigParser

from uv_pro.utils._defaults import CONFIG_MAP

NAME = 'uv_pro'
CONFIG_DIR = os.path.join(os.path.expanduser('~'), '.config', f'{NAME}')
CONFIG_FILENAME = 'settings.ini'
CONFIG_PATH = os.path.join(CONFIG_DIR, CONFIG_FILENAME)
DEFAULTS = {cfg['key']: cfg['default_str'] for (_, cfg) in CONFIG_MAP.items()}


class Config(ConfigParser):
    """wrapper for ConfigParser"""

    def __init__(self):
        super().__init__(defaults=DEFAULTS, default_section='Settings')

        if not os.path.exists(CONFIG_PATH):
            os.makedirs(CONFIG_DIR, exist_ok=True)
            self._write()

        else:
            self.read(CONFIG_PATH)
            self.validate(verbose=True)
            self._write()

    def _write(self) -> None:
        """Write settings to the config file."""
        with open(CONFIG_PATH, 'w') as f:
            self.write(f)

    def validate(self, verbose: bool = False) -> bool:
        """Validate config values. Return True if validated."""
        valid = True

        for _, config_mapping in CONFIG_MAP.items():
            if self.has_option('Settings', config_mapping['key']):
                config_value = self.get('Settings', config_mapping['key'])
                validation_func = config_mapping['validate_func']

                if not validation_func(config_value, verbose):
                    self.remove_option('Settings', config_mapping['key'])
                    valid = False

        return valid

    def delete(self) -> Exception | None:
        """Delete the config file and directory."""
        try:
            os.remove(os.path.join(Config.directory, Config.filename))
            os.rmdir(Config.directory)
            return

        except (OSError, FileNotFoundError) as e:
            return e

    def broadcast(self) -> list[tuple]:
        """
        Broadcast formatted config values.

        Useful when config parameters are to be used programmatically.

        Returns
        -------
        list[tuple[str, Any]]
            A list of tuples with config parameter names (str) and formatted values (any).
        """

        def get_val(section: str, key: str, type: callable, default_val=None, **kwargs):
            try:
                if value := self.get(section, key):
                    return type(value)

            except Exception as e:
                print(
                    f'Warning: Could not retrieve config value for [{section}] {key}: {e}'
                )

            return default_val

        return [
            (arg_name, get_val(**config_mapping))
            for arg_name, config_mapping in CONFIG_MAP.items()
        ]

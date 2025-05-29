"""
Configuration handler for ``uv_pro``.

The config file is saved as ``settings.ini`` inside ``.config/uv_pro``, which
can be found in the user's home directory.

@author: David Hebert
"""

import os
from configparser import ConfigParser
from typing import Callable, Optional

from uv_pro.utils._defaults import CONFIG_MAP

NAME = 'uv_pro'
CONFIG_DIR = os.path.join(os.path.expanduser('~'), '.config', f'{NAME}')
CONFIG_FILENAME = 'settings.ini'
CONFIG_PATH = os.path.join(CONFIG_DIR, CONFIG_FILENAME)
DEFAULTS = {option: info['default_str'] for option, info in CONFIG_MAP.items()}


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
        all_valid = True

        for option, info in CONFIG_MAP.items():
            if self.has_option('Settings', option):
                value = self.get('Settings', option)

                cleanup_func: Optional[Callable] = info.get('cleanup_func')
                if cleanup_func:
                    value = cleanup_func(value)

                validation_func: Callable = info.get('validate_func')
                if validation_func(value, verbose):
                    self.set('Settings', option, value)

            else:
                self.set('Settings', option, info.get('default_str'))
                all_valid = False

        return all_valid

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

        def get_val(option: str, section: str, type: callable, default_val=None, **kwargs):
            try:
                if value := self.get(section, option):
                    return type(value)

            except Exception as e:
                print(
                    f'Warning: Could not retrieve config value for [{section}] {option}: {e}'
                )

            return default_val

        return [
            (option, get_val(option, **info))
            for option, info in CONFIG_MAP.items()
        ]

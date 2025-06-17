"""
Configuration handler for ``uv_pro``.

The config file is saved as ``settings.ini`` inside ``.config/uv_pro``, which
can be found in the user's home directory.

@author: David Hebert
"""

from configparser import ConfigParser
from pathlib import Path
from typing import Callable, Optional

from uv_pro.utils._defaults import CONFIG_MAP

NAME = 'uv_pro'
CONFIG_DIR = Path('~').expanduser() / '.config' / NAME
CONFIG_FILENAME = 'settings.ini'
CONFIG_PATH = CONFIG_DIR / CONFIG_FILENAME
DEFAULTS = {option: info['default_str'] for option, info in CONFIG_MAP.items()}


class Config(ConfigParser):
    """wrapper for ConfigParser"""

    def __init__(self):
        super().__init__(defaults=DEFAULTS, default_section='Settings')

        if not CONFIG_PATH.exists():
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            self._write()

        else:
            self.read(CONFIG_PATH)
            self.validate(verbose=True)
            self._write()

    def _write(self) -> None:
        """Write settings to the config file."""
        with open(CONFIG_PATH, 'w') as f:
            self.write(f)

    def validate_option(self, option: str, verbose: bool = False) -> bool:
        """Validate a config value. Return True if valid."""
        option_info = CONFIG_MAP.get(option)
        if self.has_option('Settings', option):
            if value := self.get('Settings', option):
                cleanup_func: Optional[Callable] = option_info.get('cleanup_func')
                if cleanup_func:
                    value = cleanup_func(value)

                validation_func: Callable = option_info.get('validate_func')
                if validation_func(value, verbose):
                    self.set('Settings', option, str(value))
                    return True

        self.set('Settings', option, option_info.get('default_str'))

        return False

    def validate(self, verbose: bool = False) -> bool:
        """Validate all config values. Return True if all valid."""
        return all(
            [self.validate_option(option, verbose) for option in CONFIG_MAP.keys()]
        )

    def delete(self) -> Exception | None:
        """Delete the config file and directory."""
        try:
            config_file = CONFIG_DIR / CONFIG_FILENAME
            config_file.unlink()
            CONFIG_DIR.rmdir()
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

        def get_val(
            option: str, section: str, type: callable, default_val=None, **kwargs
        ):
            try:
                if value := self.get(section, option):
                    return type(value)

            except Exception as e:
                print(
                    f'Warning: Could not retrieve config value for [{section}] {option}: {e}'
                )

            return default_val

        return [
            (option, get_val(option, **info)) for option, info in CONFIG_MAP.items()
        ]


CONFIG = Config()
PRIMARY_COLOR = CONFIG.get('Settings', 'primary_color', fallback='white')

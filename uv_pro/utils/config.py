"""
Configuration handler for ``uv_pro``.

The config file is saved as ``settings.ini`` inside ``.config/uv_pro``, which
can be found in the user's home directory.

@author: David Hebert
"""

import os
import re
from configparser import ConfigParser


class Config:
    """
    A class for handling config files.

    Attributes
    ----------
    config : :class:`configparser.ConfigParser`
        The current configuration.
    directory : str
        The path to the configuration file directory.
    filename : str
        The name of the configuration file.
    name : str
        The name of the configuration file.
    """

    name = 'uv_pro'
    directory = os.path.join(os.path.expanduser("~"), ".config", f"{name}")
    filename = "settings.ini"
    defaults = {
        "Root Directory": {"root_directory": ""},
        "Settings": {"plot_size": "10 5"}
    }

    def __init__(self) -> None:
        if not self.exists():
            self.create()
            self.write_config(self.get_defaults())
        self.config = self.read_config()
        self.validate()

    def exists(self) -> bool:
        """Check if config file exists."""
        return os.path.exists(os.path.join(Config.directory, Config.filename))

    def create(self) -> None:
        """Create the config file directory."""
        os.makedirs(Config.directory, exist_ok=True)

    def get(self, section: str, option: str) -> str:
        return self.config.get(section, option)

    def items(self, section: str) -> list[tuple[str, str]]:
        return self.config.items(section)

    def get_defaults(self) -> ConfigParser:
        """Get the default configuration."""
        default_config = ConfigParser()
        default_config['Root Directory'] = Config.defaults['Root Directory']
        default_config['Settings'] = Config.defaults['Settings']
        return default_config

    def reset(self) -> None:
        """Reset the configuration to the default values."""
        self.write_config(self.get_defaults())

    def write_config(self, config: ConfigParser) -> None:
        """Write settings to the config file."""
        with open(os.path.join(Config.directory, Config.filename), "w") as f:
            config.write(f)

    def read_config(self) -> ConfigParser:
        """Get the current configuration."""
        config = ConfigParser()
        config.read(os.path.join(Config.directory, Config.filename))
        return config

    def modify(self, section: str, key: str, value: str) -> bool:
        """Modify a config value. Return True if successful."""
        self.config.set(section, key, value)

        if self.validate():
            self.write_config(self.config)
            return True

        return False

    def validate(self) -> bool:
        """Validate config values. Return True if validated."""
        pattern = re.compile(r'[\d]+\s*[\d]+')
        if not re.match(pattern, self.config.get('Settings', 'plot_size')):
            self.config.set('Settings', 'plot_size', Config.defaults['plot_size'])
            self.write_config(self.config)
            return False

        return True

    def delete(self) -> None:
        """Delete the config file and directory."""
        try:
            os.remove(os.path.join(Config.directory, Config.filename))
            os.rmdir(Config.directory)
        except (OSError, FileNotFoundError):
            pass

"""
Configuration handler for ``uv_pro``.

The config file is saved as ``settings.ini`` inside ``.config/uv_pro``, which
can be found in the user's home directory.

@author: David Hebert
"""

import os
import shutil
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

    def __init__(self) -> None:
        if not self.exists():
            self.create()
            self.write_config(self.get_defaults())
        self.config = self.get_config()

    def exists(self) -> bool:
        """Check if config file exists."""
        return os.path.exists(os.path.join(Config.directory, Config.filename))

    def create(self) -> None:
        """Create the config file directory."""
        os.makedirs(Config.directory, exist_ok=True)

    def get_defaults(self) -> ConfigParser:
        """Get the default configuration."""
        default_config = ConfigParser()
        default_config['Settings'] = {"root_directory": Config.directory}
        return default_config

    def reset(self) -> None:
        """Reset the configuration to the default values."""
        self.write_config(self.get_defaults())

    def write_config(self, config: ConfigParser) -> None:
        """Write settings to the config file."""
        with open(os.path.join(Config.directory, Config.filename), "w") as f:
            config.write(f)

    def get_config(self) -> ConfigParser:
        """Get the current configuration."""
        config = ConfigParser()
        config.read(os.path.join(Config.directory, Config.filename))
        return config

    def modify(self, section: str, key: str, value: str) -> None:
        """Modify a config value."""
        self.config.set(section, key, value)
        self.write_config(self.config)

    def delete(self) -> None:
        """Delete the config file directory and everything inside it."""
        shutil.rmtree(Config.directory)

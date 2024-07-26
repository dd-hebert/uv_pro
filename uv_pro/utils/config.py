"""
Configuration handler for ``uv_pro``.

The config file is saved as ``settings.ini`` inside ``.config/uv_pro``, which
can be found in the user's home directory.

@author: David Hebert
"""

import os
from configparser import ConfigParser
from uv_pro.utils._validate import validate_root_dir, validate_plot_size


class Config:
    """
    A class for handling config files.

    Attributes
    ----------
    config : :class:`configparser.ConfigParser`
        The current configuration.
    defaults : dict
        The default config values.
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
        "root_directory": "",
        "plot_size": "10 5"
    }

    def __init__(self) -> None:
        if not self.exists():
            self.create()
            self.write(self.get_defaults())

        self.config = self.read()
        self.validate(self.config, fallback=Config.defaults, verbose=True)

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
        default_config['Settings'] = Config.defaults
        return default_config

    def reset(self) -> None:
        """Reset the configuration to the default values."""
        self.write(self.get_defaults())

    def write(self, config: ConfigParser) -> None:
        """Write settings to the config file."""
        with open(os.path.join(Config.directory, Config.filename), "w") as f:
            config.write(f)

    def read(self) -> ConfigParser:
        """Get the current configuration."""
        config = ConfigParser()
        config.read(os.path.join(Config.directory, Config.filename))
        return config

    def modify(self, section: str, key: str, value: str) -> bool:
        """Modify a config value and write to file if valid. Return True if successful."""
        new_config = self.read()
        new_config.set(section, key, value)
        return self.validate(new_config, fallback=dict(self.config['Settings']))

    def validate(self, config: ConfigParser, fallback: dict, verbose: bool = False) -> bool:
        """Validate config values. Return True if validated."""
        valid = True
        root_dir = config.get('Settings', 'root_directory')
        plot_size = config.get('Settings', 'plot_size')

        if not validate_root_dir(root_dir, verbose):
            config.set('Settings', 'root_directory', fallback['root_directory'])
            valid = False

        if not validate_plot_size(plot_size, verbose):
            config.set('Settings', 'plot_size', fallback['plot_size'])
            valid = False

        self.write(config)

        return valid

    def delete(self) -> Exception | None:
        """Delete the config file and directory."""
        try:
            os.remove(os.path.join(Config.directory, Config.filename))
            os.rmdir(Config.directory)
            return

        except (OSError, FileNotFoundError) as e:
            return e

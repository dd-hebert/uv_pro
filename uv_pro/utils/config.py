# -*- coding: utf-8 -*-
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
    filename : str
        The name of the configuration file.
    path : str
        The path to the configuration file directory.
    config : :class:`configparser.ConfigParser`
        The current configuration.

    """

    name = 'uv_pro'
    directory = os.path.join(os.path.expanduser("~"), ".config", f"{name}")
    filename = "settings.ini"

    def __init__(self):
        """
        Initialize the Config object.

        Parameters
        ----------
        app_name : str
            The name of the application.

        Returns
        -------
        None.

        """
        if not self.exists():
            self.create()
            self.write_config(self.get_defaults())

        self.config = self.get_config()

    def exists(self):
        """
        Check if the config file exists.

        Returns
        -------
        bool
            True if it exists.

        """
        return os.path.exists(os.path.join(Config.directory, Config.filename))

    def create(self):
        """
        Create the config file directory.

        Returns
        -------
        None.

        """
        os.makedirs(Config.directory, exist_ok=True)

    def get_defaults(self):
        """
        Get the default configuration.

        Returns
        -------
        default_config : :class:`configparser.ConfigParser`
            The default configuration.

        """
        default_config = ConfigParser()
        default_config['Settings'] = {"root_directory": Config.directory}

        return default_config

    def reset(self):
        """
        Reset the configuration to the default values.

        Returns
        -------
        None.

        """
        self.write_config(self.get_defaults())

    def write_config(self, config):
        """
        Write a configuration.

        Parameters
        ----------
        config : :class:`configparser.ConfigParser`
            The configuration to write.

        Returns
        -------
        None.

        """
        with open(os.path.join(Config.directory, Config.filename), "w") as f:
            config.write(f)

    def get_config(self):
        """
        Get the current configuration.

        Returns
        -------
        config : :class:`configparser.ConfigParser`
            The current configuration.

        """
        config = ConfigParser()
        config.read(os.path.join(Config.directory, Config.filename))
        return config

    def modify(self, section, key, value):
        """
        Modify a config value.

        Parameters
        ----------
        section : str
            The section containing the key to modify.
        key : str
            The key to modify.
        value : str
            The new key value.

        Returns
        -------
        None.

        """
        self.config.set(section, key, value)
        self.write_config(self.config)

    def delete(self):
        """
        Delete the config file directory and everything inside it.

        Returns
        -------
        None.

        """
        shutil.rmtree(Config.directory)

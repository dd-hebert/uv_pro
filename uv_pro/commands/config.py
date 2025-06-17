"""
Functions for the ``config`` command.

@author: David Hebert
"""

import argparse
from typing import Callable

from uv_pro.commands import Argument, MutuallyExclusiveGroup, command
from uv_pro.utils.config import DEFAULTS, Config
from uv_pro.utils.prompts import ask, checkbox

HELP = {
    'delete': 'Delete the config file.',
    'edit': 'Edit config settings.',
    'list': 'Print the current config settings to the console.',
    'reset': 'Reset config settings back to their default value.',
}
ARGS = [
    MutuallyExclusiveGroup(
        Argument(
            '--delete',
            action='store_true',
            default=False,
            help=HELP['delete'],
        ),
        Argument(
            '-e',
            '--edit',
            action='store_true',
            default=False,
            help=HELP['edit'],
        ),
        Argument(
            '-l',
            '--list',
            action='store_true',
            default=False,
            help=HELP['list'],
        ),
        Argument(
            '-r',
            '--reset',
            action='store_true',
            default=False,
            help=HELP['reset'],
        ),
    )
]


@command(args=ARGS, aliases=['cfg'])
def config(args: argparse.Namespace) -> None:
    """
    View and modify config settings.

    Parser Info
    -----------
    *aliases : cfg
    *desc : View and modify the config settings. Available config settings: \
        root_directory, plot_size.
    *help : View and modify the config settings.
    """
    if args.edit or args.reset:
        if args.edit:
            message = 'Edit config settings'
            func = _edit_config
        if args.reset:
            message = 'Reset config settings'
            func = _reset_config

        _config_prompt(args.config, message, func)

    elif args.list:
        _print_config(args.config)

    elif args.delete:
        _delete_config(args.config)


def _config_prompt(config: Config, message: str, func: Callable) -> None:
    settings = list(config.items('Settings'))
    options = {f'{setting}: {value}': setting for setting, value in settings}

    selected_options = checkbox(message, options)
    if not selected_options:
        return

    for option in selected_options:
        setting = options[option]
        func(config, setting)


def _delete_config(config: Config) -> None:
    if input('Delete config file? (Y/N): ').lower() == 'y':
        delete = config.delete()
        if isinstance(delete, BaseException):
            print('Error deleting config.')
            print(delete)

        else:
            print('Config deleted.')


def _edit_config(config: Config, setting: str) -> None:
    while True:
        value = ask(message=f'Enter new {setting}:')
        if value is None:
            return

        config.set('Settings', setting, value)

        if config.validate_option(setting):
            config._write()
            return


def _reset_config(config: Config, setting: str) -> None:
    config.set('Settings', setting, DEFAULTS.get(setting))
    config._write()


def _print_config(config: Config) -> None:
    print('\nConfig settings')
    print('===============')
    for setting, value in config.items('Settings'):
        print(f'{setting}: {value}')

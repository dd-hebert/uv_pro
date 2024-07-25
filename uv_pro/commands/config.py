"""
Functions for the ``config`` command.

@author: David Hebert
"""
import argparse
from uv_pro.utils.config import Config
from uv_pro.utils.prompts import user_choice, get_value


def config(args: argparse.Namespace, config: Config) -> None:
    if args.edit or args.reset:
        if args.edit:
            header = 'Edit config settings'
            func = _edit_config
        if args.reset:
            header = 'Reset config settings'
            func = _reset_config

        _config_prompt(config, header, func)

    elif args.list:
        _print_config(config)

    elif args.delete:
        _delete_config(config)


def _config_prompt(config: Config, header: str, func: callable) -> None:
    options = []
    settings_keys = {}
    for key, (setting, value) in enumerate(config.items('Settings'), start=1):
        options.append({'key': str(key), 'name': f'{setting}: {value}'})
        settings_keys[str(key)] = setting

    if user_choices := user_choice(header=header, options=options):
        for choice in user_choices:
            func(config, settings_keys[choice])


def _delete_config(config: Config) -> None:
    if input('Delete config file? (Y/N): ').lower() == 'y':
        delete = config.delete()
        if isinstance(delete, BaseException):
            print('Error deleting config.')
            print(delete)

        else:
            print('Config deleted.')


def _edit_config(config: Config, setting: str) -> None:
    if value := get_value(title=setting, prompt='Enter a new value: '):
        if config.modify(section='Settings', key=setting, value=value):
            return

        else:
            _edit_config(config, setting)


def _reset_config(config: Config, setting: str) -> None:
    config.modify(
        'Settings',
        setting,
        config.defaults['Settings'][setting]
    )


def _print_config(config: Config) -> None:
    print('\nConfig settings')
    print('===============')
    for setting, value in config.items('Settings'):
        print(f'{setting}: {value}')
    print('')

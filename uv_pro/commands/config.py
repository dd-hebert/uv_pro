"""
Functions for the ``config`` command.

@author: David Hebert
"""
import argparse
from uv_pro.commands import command, argument, mutually_exclusive_group
from uv_pro.utils.config import Config
from uv_pro.utils.prompts import user_choice, get_value


HELP = {
    'delete': '''Delete the config file.''',
    'edit': '''Edit config settings.''',
    'list': '''Print the current config settings to the console.''',
    'reset': '''Reset config settings back to their default value.''',
}
MUTEX_ARGS = [
    mutually_exclusive_group(
        argument(
            '-delete',
            action='store_true',
            default=False,
            help=HELP['delete']
        ),
        argument(
            '-edit',
            action='store_true',
            default=False,
            help=HELP['edit']
        ),
        argument(
            '-list',
            action='store_true',
            default=False,
            help=HELP['list']
        ),
        argument(
            '-reset',
            action='store_true',
            default=False,
            help=HELP['reset']
        )
    )
]


@command(mutually_exclusive_args=MUTEX_ARGS, aliases=['cfg'])
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
            header = 'Edit config settings'
            func = _edit_config
        if args.reset:
            header = 'Reset config settings'
            func = _reset_config

        _config_prompt(args.config, header, func)

    elif args.list:
        _print_config(args.config)

    elif args.delete:
        _delete_config(args.config)


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
    config.modify('Settings', setting, config.defaults['Settings'][setting])


def _print_config(config: Config) -> None:
    print('\nConfig settings')
    print('===============')
    for setting, value in config.items('Settings'):
        print(f'{setting}: {value}')
    print('')

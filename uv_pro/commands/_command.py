"""
Helper functions for argparse boilerplate.
Provides a decorator for adding commands and arguments to the CLI.

@author: David Hebert
"""

import argparse
import re

main_parser = argparse.ArgumentParser(description='Process UV-vis Data Files')
subparsers = main_parser.add_subparsers(help='Commands')


def get_args() -> argparse.Namespace:
    """Collect and parse all command-line args."""
    return main_parser.parse_args()


def command(
    args: list[dict] = [],
    mutually_exclusive_args: list[dict] = [],
    aliases: list[str] = [],
    parent: argparse._SubParsersAction = subparsers,
):
    """
    Add a command and args to the CLI via a decorator.

    The command's description and help messages are extracted from the function's docstring.
    These messages are identified by the `*desc :` and `*help :` tags within the docstring.
    See the usage example below.

    Parameters
    ----------
    args : list[dict], optional
        The formatted arguments for the command, by default [].
    mutually_exclusive_args : list[dict], optional
        Groups of mutually exclusive arguments for the command, by default [].
    aliases : list[str], optional
        Aliases for the command, by default [].
    parent : argparse._SubParsersAction, optional
        The parent parser to add commands to, by default subparsers.

    Usage Example
    -------------
    ```
    @command(args=[argument('-arg1', action='store_true')])
    def hello_world(args):
    '''
    docstring for hello_world()
    *desc : hello_world command description
    *help : hello_world command help
    '''
        print('hello world!')
    ```

    Returns
    -------
    function
        The function to add as a command.
    """

    def _decorator(func):
        subparser: argparse.ArgumentParser = parent.add_parser(
            name=func.__name__,
            # aliases=_get_aliases(func.__doc__),
            aliases=aliases,
            description=_get_description(func.__doc__),
            help=_get_help(func.__doc__),
        )
        _add_args(args, subparser)
        _add_mutex_args(mutually_exclusive_args, subparser)
        subparser.set_defaults(func=func)
        return func

    return _decorator


def argument(*name_or_flags: str, **kwargs) -> dict:
    """
    Helper function to format CLI arguments to pass to the @command decorator.

    Refer to :meth:`argparse.ArgumentParser.add_argument` for help with parameters \
    and accepted keyword arguments.

    Returns
    -------
    dict
        Keys: 'name_or_flags': The argument name and flags, a list[str]. \
        'kwargs': The keyword arguments to pass to the argparse `add_argument()` method.
    """
    return {'name_or_flags': [*name_or_flags], 'kwargs': kwargs}


def mutually_exclusive_group(*args, required=False) -> dict:
    """
    Helper function for adding mutually exclusive arguments to the @command decorator.

    Parameters
    ----------
    args : list[dict], required
        A list of formatted arguments to add to the group. To properly \
        format the arguments, use :func:`~uv_pro.commands._command.argument`.
    required : bool, optional
        Indicates that one of the args in the group must be given. \
        By default False.

    Returns
    -------
    dict
        Keys: 'args': The formatted arguments in the group, a list[dict]. \
        'required': bool.
    """
    return {'args': [*args], 'required': required}


def _add_args(args: list[dict], parser_or_group: argparse._ActionsContainer) -> None:
    for arg in args:
        parser_or_group.add_argument(*arg['name_or_flags'], **arg['kwargs'])


def _add_mutex_args(arg_groups: list[dict], parser: argparse.ArgumentParser) -> None:
    for group in arg_groups:
        required = group.get('required', False)
        mutually_exclusive_group = parser.add_mutually_exclusive_group(required=required)
        _add_args(group['args'], mutually_exclusive_group)


def _parse_docstring(pattern: str, docstring: str | None) -> str | None:
    if docstring:
        if match := re.search(pattern, docstring):
            return match.group(1).strip()

    return None


def _get_description(docstring: str | None) -> str | None:
    return _parse_docstring(r'\*desc :\s*(.*)', docstring)


def _get_help(docstring: str | None) -> str | None:
    return _parse_docstring(r'\*help :\s*(.*)', docstring)


def _get_aliases(docstring: str | None) -> list[str]:
    if aliases := _parse_docstring(r'\*aliases :\s*(.*)', docstring):
            return aliases.split(', ')

    return []

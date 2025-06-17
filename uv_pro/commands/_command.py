"""
Helper functions for argparse boilerplate.
Provides a decorator for adding commands and arguments to the CLI.

@author: David Hebert
"""

import argparse
import re

from uv_pro.commands._parsers import main_parser, subparsers


def get_args() -> argparse.Namespace:
    """Collect and parse all command-line args."""
    return main_parser.parse_args()


class Argument:
    """
    Helper class for adding CLI arguments with the `@command` decorator.

    Refer to :meth:`argparse.ArgumentParser.add_argument` for help with parameters \
    and accepted keyword arguments.
    """

    def __init__(self, *name_or_flags: str, **kwargs) -> None:
        self.name_or_flags = list(name_or_flags)
        self.kwargs = kwargs


class MutuallyExclusiveGroup:
    """
    Helper function for adding mutually exclusive arguments to the `@command` decorator.
    """

    def __init__(self, *args: Argument, required=False) -> None:
        self.args = list(args)
        self.required = required


class ArgGroup:
    """
    Helper class for adding grouped arguments to the `@command` decorator.
    """

    def __init__(
        self,
        *args: Argument | MutuallyExclusiveGroup,
        title: str | None = None,
        description: str | None = None,
    ) -> None:
        self.args = list(args)
        self.title = title
        self.description = description


def command(
    args: list[Argument | ArgGroup | MutuallyExclusiveGroup] = [],
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
    args : list[Argument | ArgGroup | MutuallyExclusiveGroup], optional
        The arguments for the command, by default [].
    aliases : list[str], optional
        Aliases for the command, by default [].
    parent : argparse._SubParsersAction, optional
        The parent parser to add commands to, by default subparsers.

    Usage Example
    -------------
    ```
    from uv_pro.commands import Argument, MutuallyExclusiveGroup

    args = [
        Argument('-arg1', action='store_true'),
        MutuallyExclusiveGroup(
            Argument('-arg2', action='store_true'),
            Argument('-arg3', action='store_true'),
        )
    ]

    @command(args=args)
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
        subparser.set_defaults(func=func)
        return func

    return _decorator


def _add_argument_to_parser(parser: argparse.ArgumentParser, arg: Argument):
    parser.add_argument(*arg.name_or_flags, **arg.kwargs)


def _add_group_to_parser(parser: argparse.ArgumentParser, group: ArgGroup):
    group_parser = parser.add_argument_group(group.title, group.description)
    _add_args(group.args, group_parser)


def _add_mutex_to_parser(
    parser: argparse.ArgumentParser | argparse._ArgumentGroup,
    mutex_group: MutuallyExclusiveGroup,
):
    mutex_parser = parser.add_mutually_exclusive_group(required=mutex_group.required)
    for arg in mutex_group.args:
        _add_argument_to_parser(mutex_parser, arg)


def _add_args(args: list, parser: argparse.ArgumentParser) -> None:
    for item in args:
        if isinstance(item, Argument):
            _add_argument_to_parser(parser, item)

        elif isinstance(item, ArgGroup):
            _add_group_to_parser(parser, item)

        elif isinstance(item, MutuallyExclusiveGroup):
            _add_mutex_to_parser(parser, item)

        else:
            raise TypeError(f'Unknown argument type: {item}')


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

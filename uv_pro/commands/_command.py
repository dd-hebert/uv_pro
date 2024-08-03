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
    """Collect all command-line args."""
    return main_parser.parse_args()


def command(args: list[dict] = [], mutually_exclusive_args: list[dict] = [],
            parent=subparsers, aliases: list[str] = []):
    def _decorator(func):
        subparser: argparse.ArgumentParser = parent.add_parser(
            name=func.__name__,
            # aliases=_get_aliases(func.__doc__),
            aliases=aliases,
            description=_get_description(func.__doc__),
            help=_get_help(func.__doc__)
        )

        _add_args(args, subparser)
        _add_mutually_exclusive_args(mutually_exclusive_args, subparser)
        subparser.set_defaults(func=func)

        return func

    return _decorator


def argument(*name_or_flags: str, **kwargs) -> dict:
    return {'name_or_flags': [*name_or_flags], 'kwargs': kwargs}


def mutually_exclusive_group(*args, required=False) -> dict:
    return {'args': [*args], 'required': required}


def _add_args(args: list[dict], destination: argparse.ArgumentParser | argparse._MutuallyExclusiveGroup) -> None:
    for arg in args:
        destination.add_argument(*arg['name_or_flags'], **arg['kwargs'])


def _add_mutually_exclusive_args(arg_groups: list[dict], parser: argparse.ArgumentParser) -> None:
    for group in arg_groups:
        required = group.get('required', False)
        mutually_exclusive_group = parser.add_mutually_exclusive_group(required=required)
        _add_args(group['args'], mutually_exclusive_group)


def _get_aliases(docstring: str | None) -> list[str]:
    if docstring:
        if aliases := re.search(r'\*aliases :\s*(.*)', docstring):
            return aliases.group(1).strip().split(', ')
    return []


def _get_description(docstring: str | None) -> str | None:
    if docstring:
        if description := re.search(r'\*desc :\s*(.*)', docstring):
            return description.group(1).strip()
    return None


def _get_help(docstring: str | None) -> str | None:
    if docstring:
        if help_msg := re.search(r'\*help :\s*(.*)', docstring):
            return help_msg.group(1).strip()
    return None

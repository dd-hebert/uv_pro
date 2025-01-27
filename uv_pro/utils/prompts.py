"""
Helper functions for interactive terminal prompts.

@author: David Hebert
"""

from rich import print
from rich.console import Console
from rich.text import Text


def user_choice(header: str, options: list[dict]) -> list[str] | list:
    """
    Prompt the user for input.

    Parameters
    ----------
    header : str
        The prompt header.
    options : list[dict]
        The input choices, a list of dicts. Example: [{'key': 'q', 'name': 'Quit'}]
        An option's 'key' is the accepted input for that option.

    Returns
    -------
    list[str]
        The user's input selections.
    """
    prompt = Text(f'\n{header}\n{"=" * len(header)}\n', style='prompt')
    for opt in options:
        choice = Text(f'({opt["key"]}) {opt["name"]}\n')
        choice.stylize('prompt.choices', 1, 2)
        prompt.append(choice)

    prompt.append('\nChoice: ', style='none')
    _input = Console().input
    valid_choices = [option['key'] for option in options]

    try:
        user_choices = [key for key in _input(prompt).strip().split() if key in valid_choices]

        while not user_choices:
            print('\nInvalid selection. Enter one or more of the displayed options or ctrl-c to quit.')
            user_choices = [key for key in _input(prompt).strip().split() if key in valid_choices]

        return user_choices

    except (EOFError, KeyboardInterrupt):  # ctrl-c
        return []


def get_value(title: str, prompt: str, func: callable = None):
    """Prompt the user for some value. Apply ``func`` to input if provided."""
    print(f'\n{title}')

    try:
        value = input(prompt)
        return func(value) if func else value

    except (ValueError, NameError, SyntaxError):
        print('Invalid entry.')
        return

    except (EOFError, KeyboardInterrupt):
        return

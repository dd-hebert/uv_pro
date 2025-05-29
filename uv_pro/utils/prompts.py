"""
Helper functions for interactive terminal prompts.

@author: David Hebert
"""

from collections.abc import Sequence
from typing import Any

import questionary
from questionary import Style
from rich import print


STYLE = Style(
    [
        ('qmark', 'fg:#ff00ff bold'),
        ('question', 'bold'),
        ('highlighted', 'fg:#af87ff bold'),
        ('selected', 'fg:#875fd7 bg:ansiwhite bold'),
        ('answer', 'fg:#d7afff'),
        ('instruction', 'fg:#5f819d'),
        ('pointer', 'fg:#ff00ff')
    ]
)

def checkbox(message: str, choices: Sequence[str | dict[str, Any]], **kwargs) -> list:
    """
    Prompt the user to select from a list of choices.

    Parameters
    ----------
    message : str
        The prompt message.
    choices : Sequence[str | dict[str, Any]]
        The choices, a list of strings.

    Returns
    -------
    list[str]
        The user's selections.
    """
    question = questionary.checkbox(
        message,
        choices,
        qmark='✓',
        pointer='⮞',
        style=STYLE,
        **kwargs,
    )

    print()
    return question.ask(kbi_msg='')


def ask(prompt: str, **kwargs) -> str:
    """Prompt the user for some input."""
    question = questionary.text(
        prompt,
        qmark='❯',
        style=STYLE,
        **kwargs,
    )

    print()
    return question.ask(kbi_msg='')

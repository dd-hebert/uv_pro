"""
Helper functions for interactive terminal prompts.

@author: David Hebert
"""

from collections.abc import Sequence, Callable
from pathlib import Path
from typing import Any, Union, Optional

import questionary
from questionary import Style, Question
from rich import print

from uv_pro.utils.config import PRIMARY_COLOR

STYLE = Style(
    [
        ('qmark', f'fg:ansibright{PRIMARY_COLOR} bold'),
        ('question', 'bold'),
        ('highlighted', f'fg:ansi{PRIMARY_COLOR} bold'),
        ('selected', f'fg:ansibright{PRIMARY_COLOR} bg:ansiwhite bold'),
        ('answer', f'fg:ansi{PRIMARY_COLOR}'),
        ('instruction', 'fg:ansibrightblack'),
        ('pointer', f'fg:ansibright{PRIMARY_COLOR}')
    ]
)

def _prompt(prompt_func: Question, message: str, **kwargs) -> Any:
    """Generic prompt function."""
    question: Question = prompt_func(message, style=STYLE, **kwargs)
    print()
    return question.ask(kbi_msg='')


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
    return _prompt(
        questionary.checkbox,
        message,
        choices=choices,
        qmark='✓',
        pointer='⮞',
        **kwargs
    )


def ask(message: str, **kwargs) -> str:
    """Prompt the user for some input."""
    return _prompt(
        questionary.text,
        message,
        qmark='❯',
        **kwargs
    )


def autocomplete(message: str, choices: list[str], **kwargs) -> str:
    """Prompt the user for choice with autocomplete."""
    return _prompt(
        questionary.autocomplete,
        message,
        choices=choices,
        qmark='❯',
        complete_style='MULTI_COLUMN',
        **kwargs
    )


def select(message: str, choices: list[str], **kwargs) -> str:
    """Prompt the user for a choice from a list."""
    return _prompt(
        questionary.select,
        message,
        choices=choices,
        qmark='❯',
        **kwargs
    )

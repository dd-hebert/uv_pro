"""
Functions for the ``process`` command.

@author: David Hebert
"""

import argparse
import os
from pathlib import Path

from rich import print
from rich.columns import Columns

from uv_pro.commands import argument, command, mutually_exclusive_group
from uv_pro.dataset import Dataset
from uv_pro.io.export import export_csv
from uv_pro.plots import CMAPS, plot_2x2, plot_spectra
from uv_pro.quickfig import QuickFig
from uv_pro.utils._rich import splash
from uv_pro.utils.paths import cleanup_path, handle_args_dir
from uv_pro.utils.prompts import ask, pick_files


HELP = {
    'directory': """An optional directory to search for kinetics files. Default is current working directory.""",
}
ARGS = [
    argument(
        'directory',
        action='store',
        type=cleanup_path,
        nargs='?',
        default=None,
        help=HELP['directory'],
    ),
]


@command(args=ARGS)
def k2(args: argparse.Namespace) -> None:
    """
    Process kinetics data to get second-order rate constants.

    Reads kinetics 'params' .csv files, fits the data, and plots
    the result.

    Parser Info
    -----------
    *desc : Process kinetics data to get second-order rate constants.
    *help : Process kinetics data.
    """
    if args.directory is None:
        args.directory = Path.cwd()

    else:
        handle_args_dir(args)

    print(args.directory)

    chosen_files = pick_files(search_dir=str(args.directory), ext='.csv', show_relative_path=True)

    if chosen_files is None:
            return

    concs = prompt_for_conc([Path(p).relative_to(args.directory) for p in chosen_files])



def prompt_for_conc(files: list) -> list | None:
    """
    Prompt the user for substrate concentration (in M) for each kinetics data series.
    Allows arithmetic expressions and going back with 'b' or 'back'.

    Args:
        kinetics_data (list): List of pd.Series (or similar) with .name attribute.

    Returns:
        list: Updated kinetics_data with renamed series based on user input.
    """

    def safe_eval(expr: str) -> float:
        # Limit builtins to prevent malicious code execution
        allowed_names = {
            '__builtins__': None,
            'abs': abs,
            'round': round,
            'min': min,
            'max': max,
            # Add any math functions if needed, or import math and expose selected ones
        }
        return float(eval(expr, allowed_names))

    concentrations = []
    index = 0
    err_msg = 'Please enter a number or numeric expression or <b> to go back.'

    while index < len(files):
        file = files[index]
        user_input = ask(
            f"Enter substrate concentration for '{file}' (in M):",
            instruction='(<b> to go back): '
        )

        if user_input is None:
            break

        if user_input == '':
            print(err_msg)

        if user_input.lower() in {'b', 'back'}:
            if index == 0:
                print("Already at the first entry; can't go back further.")
            else:
                index -= 1
        else:
            try:
                conc = safe_eval(user_input)
                if conc < 0:
                    print('Concentration must be positive. Please try again.')
                    continue

                concentrations.append(conc)
                index += 1
            except Exception as e:
                print(f'Invalid input: {err_msg}')

    return concentrations

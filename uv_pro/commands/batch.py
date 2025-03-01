"""
Functions for the ``batch`` command.

@author: David Hebert
"""

import argparse

from uv_pro.commands import argument, command
from uv_pro.commands.multiview import filter_files
from uv_pro.dataset import Dataset
from uv_pro.io.export import export_csv

HELP = {
    'search_filters': 'An arbitrary number of search filters',
    'wavelengths': 'The time trace wavelengths (in nm) to batch export.',
}
ARGS = [
    argument(
        'wavelengths',
        action='store',
        nargs='+',
        type=int,
        default=None,
        help=HELP['wavelengths'],
    ),
    argument(
        '-f',
        '--search_filters',
        action='store',
        nargs='*',
        default='*',
        metavar='',
        help=HELP['search_filters'],
    ),
]


@command(args=ARGS)
def batch(args: argparse.Namespace) -> None:
    """
    Search for .KD files in the current working directory (with optional \
    search filters) and batch export time traces.

    Parser Info
    -----------
    *desc : Batch export time traces from .KD files in the current working directory.
    *help : Batch export time traces from .KD files.
    """
    if files := filter_files(args.search_filters):
        files_exported = []

        for file in files:
            dataset = Dataset(path=file, view_only=True)

            try:
                files_exported.append(
                    export_csv(
                        dataset=dataset,
                        data=dataset.get_chosen_traces(args.wavelengths),
                        suffix='Traces',
                    )
                )

            except AttributeError:
                msg = [
                    f'Error: {file}',
                    '\n\tNo time traces to export. Invalid wavelength(s): ',
                    f'{", ".join(map(str, args.wavelengths))} nm.',
                ]
                print(''.join(msg))
                continue

        print('Files exported:')
        if files_exported:
            print('\n'.join(['\t' + file for file in files_exported]))
        else:
            print('\tNone')

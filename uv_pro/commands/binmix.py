"""
Functions for the ``binmix`` command.

@author: David Hebert
"""

import argparse
import os
from collections import namedtuple
import pandas as pd
from uv_pro.commands import command, argument
from uv_pro.binarymixture import BinaryMixture
from uv_pro.plots import plot_binarymixture
from uv_pro.io.export import prompt_for_export, export_csv
from uv_pro.utils.prompts import user_choice


HELP = {
    'path': '''Path to a UV-vis data file (.csv format) of binary mixture spectra.''',
    'component_a': '''Path to a UV-vis spectrum (.csv format) of pure component "A".''',
    'component_b': '''Path to a UV-vis spectrum (.csv format) of pure component "B".''',
    'columns': '''The columns of the binary mixture .csv file to perform fitting on.
                  Default is None (fit all columns).''',
    'window': '''Set the range of wavelengths (in nm) to use from the given spectra
                 for fitting. Default is (300, 1100).''',
    'interactive': '''Enable interactive mode. Show an interactive matplotlib figure
                      of the binary mixture fitting.''',
    'no_export': '''Skip the export results prompt at the end of the script.''',
}
ARGS = [
    argument(
        'path',
        action='store',
        default=None,
        help=HELP['path']
    ),
    argument(
        'component_a',
        action='store',
        default=None,
        help=HELP['component_a']
    ),
    argument(
        'component_b',
        action='store',
        default=None,
        help=HELP['component_b']
    ),
    argument(
        '-a',
        '--molarity_a',
        action='store',
        type=float,
        default=None,
        metavar='',
        help=HELP['columns']
    ),
    argument(
        '-b',
        '--molarity_b',
        action='store',
        type=float,
        default=None,
        metavar='',
        help=HELP['columns']
    ),
    argument(
        '-cols',
        '--columns',
        action='store',
        nargs='*',
        default=[],
        metavar='',
        help=HELP['columns']
    ),
    argument(
        '-win',
        '--window',
        action='store',
        type=int,
        nargs=2,
        default=[300, 1100],
        metavar='',
        help=HELP['window']
    ),
    argument(
        '-i',
        '--interactive',
        action='store_true',
        default=False,
        help=HELP['interactive']
    ),
    argument(
        '-ne',
        '--no_export',
        action='store_true',
        default=False,
        help=HELP['no_export']
    ),
]


@command(args=ARGS)
def binmix(args: argparse.Namespace) -> None:
    """
    Parser Info
    -----------
    *desc : Estimate the relative composition of two species in a binary mixture.
    *help : Fit the spectra of two species in a binary mixture.
    """
    mixture = pd.read_csv(args.path, index_col=0)
    component_a = pd.read_csv(args.component_a, index_col=0, usecols=[0, 1])
    component_b = pd.read_csv(args.component_b, index_col=0, usecols=[0, 1])
    columns = args.columns if args.columns else mixture.columns
    # args.interactive = args.interactive if len(columns) == 1 else False

    fit_results = []
    fit_specta = []

    for column in columns:
        try:
            bm = BinaryMixture(
                mixture=mixture[column],
                component_a=component_a.iloc[:, 0],
                component_b=component_b.iloc[:, 0],
                window=args.window
            )

            if args.interactive:
                plot_binarymixture(bm, figsize=args.plot_size)

            results = {
                'label': column,
                'coeff_a': round(bm.coeff_a, 3),
                'conc_a': bm.coeff_a * args.molarity_a if args.molarity_a else None,
                'coeff_b': round(bm.coeff_b, 3),
                'conc_b': bm.coeff_b * args.molarity_b if args.molarity_b else None,
                'MSE': bm.mean_squared_error()
            }

            fit_results.append(results)
            fit_specta.append(bm.linear_combination(bm.coeff_a, bm.coeff_b).rename(column))

        except KeyError:
            continue

    if fit_results:
        print(_to_string(args, fit_results))

        if args.no_export is False:
            prompt_for_export(args, fit_results, fit_specta)


def _to_string(args, results: list[dict]) -> str:
    headings = [('label', 10), ('coeff_a', 7), ('coeff_b', 7), ('MSE', 8)]
    if args.molarity_a:
        headings.append(('conc_a', 8))
    if args.molarity_b:
        headings.append(('conc_b', 8))

    formatters = {
        'label': lambda x: f'{x:<10}',
        'coeff_a': lambda x: f'{x:.3}',
        'coeff_b': lambda x: f'{x:.3}',
        'MSE': lambda x: f'{x:.2e}',
        'conc_a': lambda x: f'{x:.2e}',
        'conc_b': lambda x: f'{x:.2e}',
    }

    table_width = sum(width + 3 for _, width in headings) - 1
    table_headings = '│ ' + '   '.join(f"\033[1m{{:^{width}}}" for _, width in headings) + '\033[22m │'
    table_row = '│ ' + '   '.join(f"{{:<{width}}}" for _, width in headings) + ' │'

    out = [
        f'Binary mixture: {os.path.basename(args.path)}',
        f'Component A: {os.path.basename(args.component_a)}',
        f'Component B: {os.path.basename(args.component_b)}\n',
        '┌' + '─' * table_width + '┐',
        table_headings.format(*(name for name, _ in headings)),
        '├' + '─' * table_width + '┤',
    ]

    for result in results:
        row_data = [
            formatters[name](result[name]) if name in result else ''
            for name, _ in headings
        ]
        out.append(table_row.format(*row_data))

    out.append('└' + '─' * table_width + '┘')

    return '\n'.join(out)


def prompt_for_export(args: argparse.Namespace, results: list[dict], spectra: list[pd.Series]) -> None:
    """
    Prompt the user for data export.

    Parameters
    ----------
    args : :class:`argparse.Namepsace`
        The parsed command line arguments.
    results: list[dict]
        A list of dicts with binary mixture fitting results.
    spectra: list[:class:`pandas.Series`]
        A list of best-fit spectra.

    Returns
    -------
    files_exported : list[str]
        The names of the exported files.
    """
    key = 1
    header = 'Export results?'
    options = [{'key': str(key), 'name': 'Fitting results'}]
    files_exported = []

    dummy = namedtuple('Dummy_Dataset', ['path', 'name'])  # Hacky way to get around having to use a real Dataset
    ds = dummy(path=args.path, name=os.path.basename(args.path))

    spectra_key = None

    if spectra:
        key += 1
        spectra_key = key
        options.append({'key': str(spectra_key), 'name': 'Best-fit spectra'})

    if user_choices := user_choice(header=header, options=options):
        if '1' in user_choices:
            out = pd.DataFrame(results).set_index('label')
            files_exported.append(export_csv(ds, out, suffix='Binmix Params'))

        if str(spectra_key) in user_choices:
            out = pd.DataFrame(spectra).T
            files_exported.append(export_csv(ds, out, suffix='Binmix Fit'))

    if files_exported:
        print(f'\nExport location: {os.path.dirname(args.path)}')
        print('Files exported:')
        [print(f'\t{file}') for file in files_exported]

    return files_exported

# TODO
# Add options for concentrations/equivalents

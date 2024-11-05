"""
Functions for the ``binmix`` command.

@author: David Hebert
"""

import argparse
import pandas as pd
from uv_pro.commands import command, argument
from uv_pro.binarymixture import BinaryMixture
from uv_pro.plots import plot_binarymixture


HELP = {
    'path': '''Path to a UV-vis data file (.csv format) of binary mixture spectra.''',
    'component_a': '''Path to a UV-vis spectrum (.csv format) of pure component "A".''',
    'component_b': '''Path to a UV-vis spectrum (.csv format) of pure component "B".''',
    'columns': '''The columns of the binary mixture .csv file to perform fitting on.
                  Default is None (fit all columns).''',
    'window': '''Set the range of wavelengths (in nm) to use from the given spectra
                 for fitting. Default is (300, 1100).''',
    'interactive': '''Enable interactive mode. Show an interactive matplotlib figure
                      of the binary mixture fitting.'''
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

    out = []

    for column in columns:
        try:
            bm = BinaryMixture(
                mixture=mixture[column],
                component_a=component_a[component_a.columns[0]],
                component_b=component_b[component_b.columns[0]],
                window=args.window
            )

            if args.interactive:
                plot_binarymixture(bm, figsize=args.plot_size)

            out.append(
                {
                    'spectrum': column,
                    'coeff_a': round(bm.coeff_a, 3),
                    'coeff_b': round(bm.coeff_b, 3),
                    'mse': bm.mean_squared_error()
                }
            )

        except KeyError:
            continue

    print(_to_string(out))


def _to_string(results: list[dict]) -> str:
    table_width = 43
    table_headings = '│ \033[1m{:^10}   {:^7}   {:^7}   {:^8}\033[22m │'

    out = []
    out.append('┌' + '─' * table_width + '┐')
    out.append(table_headings.format('Spectrum', 'coeff_a', 'coeff_b', 'MSE'))
    out.append('├' + '─' * table_width + '┤')

    for result in results:
        spectrum = '{}'.format(result['spectrum'])
        coeff_a = '{:.3}'.format(result['coeff_a'])
        coeff_b = '{:.3}'.format(result['coeff_b'])
        mse = '{:.2e}'.format(result['mse'])
        out.append('│ {:>10}   {:<7}   {:<7}   {:<8} │'.format(spectrum, coeff_a, coeff_b, mse))

    out.append('└' + '─' * table_width + '┘')

    return '\n'.join(out)

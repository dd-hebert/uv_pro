"""
Functions for the ``binmix`` command.

@author: David Hebert
"""

import argparse
import os
from collections import namedtuple
import pandas as pd
from rich import print
from uv_pro.commands import command, argument, mutually_exclusive_group
from uv_pro.binarymixture import BinaryMixture
from uv_pro.plots import plot_binarymixture
from uv_pro.io.export import export_csv
from uv_pro.utils.prompts import user_choice
from uv_pro.utils._rich import splash, BinmixOutput


HELP = {
    'path': '''Path to a UV-vis data file (.csv format) of binary mixture spectra.''',
    'component_a': '''Path to a UV-vis spectrum (.csv format) of pure component "A".''',
    'component_b': '''Path to a UV-vis spectrum (.csv format) of pure component "B".''',
    'molarity_a': '''Specify the concentration (in M) of pure component "A".''',
    'molarity_b': '''Specify the concentration (in M) of pure component "B".''',
    'columns': '''Specify the columns of the binary mixture .csv file to perform fitting on.
                  Provide the LABEL for each column. Default is None (fit all columns).''',
    'index_columns': '''Specify the columns of the binary mixture .csv file to perform fitting on.
                  Provide the IDX for each column. Default is None (fit all columns).''',
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
        help=HELP['molarity_a']
    ),
    argument(
        '-b',
        '--molarity_b',
        action='store',
        type=float,
        default=None,
        metavar='',
        help=HELP['molarity_b']
    ),
    argument(
        '-win',
        '--window',
        action='store',
        type=int,
        nargs=2,
        default=[300, 1100],
        metavar=('MIN', 'MAX'),
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
MUTEX_ARGS = [
    mutually_exclusive_group(
        argument(
            '-cols',
            '--columns',
            action='store',
            nargs='*',
            default=[],
            metavar='LABEL',
            help=HELP['columns']
        ),
        argument(
            '-icols',
            '--index_columns',
            action='store',
            type=int,
            nargs='*',
            default=[],
            metavar='IDX',
            help=HELP['index_columns']
        )
    )
]


@command(args=ARGS, mutually_exclusive_args=MUTEX_ARGS)
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
    # args.interactive = args.interactive if len(columns) == 1 else False
    first_iteration = True

    if args.columns:
        mixture = mixture.loc[:, args.columns]

    elif args.index_columns:
        idx_rng = range(-len(mixture.columns), len(mixture.columns))
        columns = set([idx for idx in sorted(args.index_columns) if idx in idx_rng])
        mixture = mixture.iloc[:, list(columns)].T.drop_duplicates().T

    fit_results = []
    fit_specta = []

    for column in mixture.columns:

        try:
            bm = BinaryMixture(
                mixture=mixture[column],
                component_a=component_a.iloc[:, 0],
                component_b=component_b.iloc[:, 0],
                window=args.window
            )

            if args.interactive:
                if first_iteration:
                    first_iteration = False
                    print('', splash(text='Close plot window to continue...', title='uv_pro Binary Mixture Fitter'))

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
        fit_df = pd.DataFrame(fit_results).set_index('label')
        print('', BinmixOutput(args, fit_df.T), sep='\n')

        if args.no_export is False:
            prompt_for_export(args, fit_df, fit_specta)


def prompt_for_export(args: argparse.Namespace, results: pd.DataFrame, spectra: list[pd.Series]) -> None:
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
            files_exported.append(export_csv(ds, results, suffix='Binmix Params'))

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

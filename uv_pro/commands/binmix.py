"""
Functions for the ``binmix`` command.

@author: David Hebert
"""

import argparse

import pandas as pd
from rich import print

from uv_pro.binarymixture import BinaryMixture
from uv_pro.commands import Argument, MutuallyExclusiveGroup, command
from uv_pro.io.export import export_csv
from uv_pro.plots import plot_binarymixture
from uv_pro.utils._rich import BinmixOutput, splash
from uv_pro.utils.paths import cleanup_path
from uv_pro.utils.prompts import checkbox

HELP = {
    'path': """Path to a UV-vis data file (.csv format) of binary mixture spectra.""",
    'component_a': """Path to a UV-vis spectrum (.csv format) of pure component "A".""",
    'component_b': """Path to a UV-vis spectrum (.csv format) of pure component "B".""",
    'molarity_a': """Specify the concentration (in M) of pure component "A".""",
    'molarity_b': """Specify the concentration (in M) of pure component "B".""",
    'columns': """Specify the columns of the binary mixture .csv file to perform fitting on.
                  Provide the LABEL for each column. Default is None (fit all columns).""",
    'index_columns': """Specify the columns of the binary mixture .csv file to perform fitting on.
                  Provide the IDX for each column. Default is None (fit all columns).""",
    'window': """Set the range of wavelengths (in nm) to use from the given spectra
                 for fitting. Default is (300, 1100).""",
    'interactive': """Enable interactive mode. Show an interactive matplotlib figure
                      of the binary mixture fitting.""",
    'no_export': """Skip the export results prompt at the end of the script.""",
}
ARGS = [
    Argument(
        'path',
        action='store',
        type=cleanup_path,
        default=None,
        help=HELP['path'],
    ),
    Argument(
        'component_a',
        action='store',
        type=cleanup_path,
        default=None,
        help=HELP['component_a'],
    ),
    Argument(
        'component_b',
        action='store',
        type=cleanup_path,
        default=None,
        help=HELP['component_b'],
    ),
    Argument(
        '-a',
        '--molarity_a',
        action='store',
        type=float,
        default=None,
        metavar='',
        help=HELP['molarity_a'],
    ),
    Argument(
        '-b',
        '--molarity_b',
        action='store',
        type=float,
        default=None,
        metavar='',
        help=HELP['molarity_b'],
    ),
    Argument(
        '-win',
        '--window',
        action='store',
        type=int,
        nargs=2,
        default=[300, 1100],
        metavar=('MIN', 'MAX'),
        help=HELP['window'],
    ),
    Argument(
        '-i',
        '--interactive',
        action='store_true',
        default=False,
        help=HELP['interactive'],
    ),
    Argument(
        '-ne',
        '--no_export',
        action='store_true',
        default=False,
        help=HELP['no_export'],
    ),
    MutuallyExclusiveGroup(
        Argument(
            '-cols',
            '--columns',
            action='store',
            nargs='*',
            default=[],
            metavar='LABEL',
            help=HELP['columns'],
        ),
        Argument(
            '-icols',
            '--index_columns',
            action='store',
            type=int,
            nargs='*',
            default=[],
            metavar='IDX',
            help=HELP['index_columns'],
        ),
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
    # args.interactive = args.interactive if len(columns) == 1 else False
    first_iteration = True

    if args.columns:
        mixture = mixture.loc[:, args.columns]

    elif args.index_columns:
        idx_rng = range(-len(mixture.columns), len(mixture.columns))
        columns = sorted(set([idx for idx in args.index_columns if idx in idx_rng]))
        mixture = mixture.iloc[:, list(columns)].T.drop_duplicates().T

    fit_results = []
    fit_specta = []

    for column in mixture.columns:
        try:
            bm = BinaryMixture(
                mixture=mixture[column],
                component_a=component_a.iloc[:, 0],
                component_b=component_b.iloc[:, 0],
                window=args.window,
            )

            if args.interactive:
                if first_iteration:
                    first_iteration = False
                    print(
                        '',
                        splash(
                            text='Close plot window to continue...',
                            title='uv_pro Binary Mixture Fitter',
                        ),
                    )

                plot_binarymixture(bm, figsize=args.plot_size)

            results = {
                'label': column,
                'coeff_a': round(bm.coeff_a, 3),
                'conc_a': bm.coeff_a * args.molarity_a if args.molarity_a else None,
                'coeff_b': round(bm.coeff_b, 3),
                'conc_b': bm.coeff_b * args.molarity_b if args.molarity_b else None,
                'MSE': bm.mean_squared_error(),
            }

            fit_results.append(results)
            fit_specta.append(
                bm.linear_combination(bm.coeff_a, bm.coeff_b).rename(column)
            )

        except KeyError:
            continue

    if fit_results:
        fit_df = pd.DataFrame(fit_results).set_index('label')
        print('', BinmixOutput(args, fit_df.T), sep='\n')

        if args.no_export is False:
            files_exported = prompt_for_export(args, fit_df, fit_specta)

            if files_exported:
                print(f'\nExport location: [repr.path]{args.path.parent}[/repr.path]')
                print('Files exported:')
                [
                    print(f'\t[repr.filename]{file}[/repr.filename]')
                    for file in files_exported
                ]


def prompt_for_export(
    args: argparse.Namespace, results: pd.DataFrame, spectra: list[pd.Series]
) -> None:
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
    header = 'Export results?'
    options = ['Fitting results']
    files_exported = []

    # Hacky way to get around having to use a real Dataset
    # dummy = namedtuple('Dummy_Dataset', ['path', 'name'])
    # ds = dummy(path=args.path, name=args.path.name)

    if spectra:
        options.append('Best-fit spectra')

    user_choices = checkbox(header, options)

    if user_choices is None:
        return []

    if 'Fitting results' in user_choices:
        files_exported.append(
            export_csv(
                results, args.path.parent, args.path.stem, suffix='binmix_params'
            )
        )

    if 'Best-fit spectra' in user_choices:
        out = pd.DataFrame(spectra).T
        files_exported.append(
            export_csv(out, args.path.parent, args.path.stem, suffix='binmix_fit')
        )

    return files_exported


# TODO
# Add options for concentrations/equivalents

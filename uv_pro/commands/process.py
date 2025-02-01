"""
Functions for the ``process`` command.

@author: David Hebert
"""

import os
import argparse
from rich import print
from rich.columns import Columns
from uv_pro.commands import command, argument, mutually_exclusive_group
from uv_pro.dataset import Dataset
from uv_pro.quickfig import QuickFig
from uv_pro.plots import plot_spectra, plot_2x2, CMAPS
from uv_pro.io.export import export_csv
from uv_pro.utils.prompts import user_choice
from uv_pro.utils._rich import splash


HELP = {
    'path': '''A path to a UV-vis data file (.KD format). Required unless using --list-colormaps.''',
    'view': '''Enable view-only mode (no data processing).''',
    'trim': '''Remove spectra outside the given time range.
               Data before time = T1 and after time = T2 will be removed.
               Use -1 for END to indicate the end of the data.''',
    'outlier-threshold': '''Set the threshold (0-1) for outlier detection. Default: 0.1.
                            Values closer to 0 result in higher sensitivity (more outliers).
                            Values closer to 1 result in lower sensitivity (fewer outliers).''',
    'slice': 'Set the number of slices to plot. Default: None (no slicing).',
    'variable-slice': '''Use non-equal spacing when slicing data. Takes 2 args: coefficient & exponent.
                         Default: None (no slicing).''',
    'specific-slice': '''Get spectra slices from specific times. Takes an arbitrary number of floats.''',
    'baseline-smoothness': 'Set the smoothness of the baseline. Default: 10.',
    'baseline-tolerance': 'Set the threshold (0-1) for outlier detection. Default: 0.1.',
    'low-signal-window': '''"narrow", "wide", or "none". Set the width of the low signal outlier detection window.
                             Default: "none". If "none", low signal outlier detection is skipped.''',
    'fit-exponential': 'Perform exponential fitting of specified time traces. Default: False.',
    'initial-rates': '''Perform linear regression of specified time traces for initial rates. Default False.
                    If performing initial rates fitting, you can supply an optional float value for
                    the change in absorbance cutoff. Default cutoff is 0.1 (10%% change in absorbance).''',
    'time-trace-window': '''Set the (min, max) wavelength (in nm) window for the time traces used in
                            outlier detection''',
    'time-trace-interval': '''Set the interval (in nm) for time traces. An interval of 10 will create time
                              traces from the window min to max every 10 nm. Smaller intervals may
                              increase loading times.''',
    'time-traces': 'Specific wavelengths (in nm) to create time traces for.',
    'no-export': 'Skip the export data prompt at the end of the script.',
    'quick-fig': 'Use the quick-figure generator.',
    'colormap': '''Set the colormap for the processed spectra plot. Accepts any built-in
                   Matplotlib colormap name. For a full description of colormaps see:
                   https://matplotlib.org/stable/tutorials/colors/colormaps.html.
                   Default is 'default'.''',
    'list-colormaps': 'List available colormaps and exit (path not required).'
}
ARGS = [
    argument(
        'path',
        action='store',
        nargs='?',
        default=None,
        help=HELP['path']
    ),
    argument(
        '-v',
        '--view',
        action='store_true',
        default=False,
        help=HELP['view']
    ),
    argument(
        '-tr',
        '--trim',
        action='store',
        type=int,
        nargs=2,
        default=None,
        metavar=('T1', 'T2'),
        help=HELP['trim']
    ),
    argument(
        '-ot',
        '--outlier-threshold',
        action='store',
        type=float,
        default=0.1,
        metavar='',
        help=HELP['outlier-threshold']
    ),
    argument(
        '-bs',
        '--baseline-smoothness',
        action='store',
        type=float,
        default=10,
        metavar='',
        help=HELP['baseline-smoothness']
    ),
    argument(
        '-bt',
        '--baseline-tolerance',
        action='store',
        type=float,
        default=0.1,
        metavar='',
        help=HELP['baseline-tolerance']
    ),
    argument(
        '-lw',
        '--low-signal-window',
        action='store',
        default='none',
        choices=['narrow', 'wide', 'none'],
        help=HELP['low-signal-window']
    ),
    argument(
        '-fx',
        '--fit-exponential',
        action='store_true',
        default=False,
        help=HELP['fit-exponential']
    ),
    argument(
        '-ir',
        '--initial-rates',
        action='store',
        type=float,
        nargs='?',
        const='0.1',
        default=None,
        metavar='',
        help=HELP['initial-rates']
    ),
    argument(
        '-tw',
        '--time-trace-window',
        action='store',
        type=int,
        nargs=2,
        default=[300, 1060],
        metavar=('MIN', 'MAX'),
        help=HELP['time-trace-window']
    ),
    argument(
        '-ti',
        '--time-trace-interval',
        action='store',
        type=int,
        default=10,
        metavar='',
        help=HELP['time-trace-interval']
    ),
    argument(
        '-tt',
        '--time-traces',
        action='store',
        nargs='*',
        type=int,
        default=None,
        metavar='',
        help=HELP['time-traces']
    ),
    argument(
        '-ne',
        '--no-export',
        action='store_true',
        default=False,
        help=HELP['no-export']
    ),
    argument(
        '-qf',
        '--quick-fig',
        action='store_true',
        default=False,
        help=HELP['quick-fig']
    ),
    argument(
        '-c',
        '--colormap',
        action='store',
        metavar='NAME',
        default='default',
        choices=CMAPS,
        help=HELP['colormap']
    ),
    argument(
        '--list-colormaps',
        action='store_true',
        default=False,
        help=HELP['list-colormaps']
    )
]
MUTEX_ARGS = [
    mutually_exclusive_group(
        argument(
            '-sl',
            '--slice',
            action='store',
            type=int,
            default=None,
            metavar='',
            help=HELP['slice']
        ),
        argument(
            '-vsl',
            '--variable-slice',
            action='store',
            type=float,
            nargs=2,
            default=None,
            metavar='',
            help=HELP['variable-slice']
        ),
        argument(
            '-ssl',
            '--specific-slice',
            action='store',
            nargs='*',
            type=float,
            default=None,
            metavar='',
            help=HELP['specific-slice']
        )
    )
]


@command(args=ARGS, mutually_exclusive_args=MUTEX_ARGS, aliases=['p', 'proc'])
def process(args: argparse.Namespace) -> None:
    """
    Process data.

    Initializes a :class:`~uv_pro.dataset.Dataset` with the
    given ``args``, plots the result, and prompts the user
    for exporting.

    Parser Info
    -----------
    *aliases : p, proc
    *desc : Process a .KD UV-vis data file with the given args, \
        plot the result, and export data (optional).
    *help : Process .KD UV-vis data files.
    """
    if args.list_colormaps:
        return list_colormaps()

    _handle_path(args)

    if args.view is True:
        dataset = Dataset(args.path, view_only=True)

    else:
        dataset = Dataset(
            args.path,
            trim=args.trim,
            slicing=_handle_slicing(args),
            fit_exp=args.fit_exponential,
            fit_init_rate=args.initial_rates,
            outlier_threshold=args.outlier_threshold,
            baseline_smoothness=args.baseline_smoothness,
            baseline_tolerance=args.baseline_tolerance,
            low_signal_window=args.low_signal_window,
            time_trace_window=args.time_trace_window,
            time_trace_interval=args.time_trace_interval,
            wavelengths=args.time_traces
        )

    print('', dataset, sep='\n')
    _plot_and_export(args, dataset)


def _handle_path(args: argparse.Namespace) -> None:
    ext = os.path.splitext(args.path)[1]

    if not ext:
        args.path = args.path + '.KD'

    current_dir = os.getcwd()
    path_exists = os.path.exists(os.path.join(current_dir, args.path))

    if path_exists:
        args.path = os.path.join(current_dir, args.path)

    elif args.root_dir is not None and os.path.exists(os.path.join(args.root_dir, args.path)):
        args.path = os.path.join(args.root_dir, args.path)

    else:
        raise FileNotFoundError(f'No such file or directory could be found: "{args.path}"')


def _handle_slicing(args: argparse.Namespace) -> dict | None:
    if args.slice:
        return {'mode': 'equal', 'slices': args.slice}

    elif args.variable_slice:
        return {
            'mode': 'variable',
            'coeff': args.variable_slice[0],
            'expo': args.variable_slice[1]
        }

    elif args.specific_slice:
        return {
            'mode': 'specific',
            'times': args.specific_slice
        }

    return None


def list_colormaps():
    link = 'https://matplotlib.org/stable/tutorials/colors/colormaps.html'
    print(
        'Valid colormaps:\n',
        Columns(CMAPS, column_first=True),
        f'\nSee {link} for more info.'
    )


def prompt_for_export(dataset) -> list[str]:
    """
    Prompt the user for data export.

    Parameters
    ----------
    dataset : :class:`~uv_pro.dataset.Dataset`
        The :class:`~uv_pro.dataset.Dataset` to be exported.

    Returns
    -------
    files_exported : list[str]
        The names of the exported files.
    """
    key = 1
    header = 'Export data?'
    options = [{'key': str(key), 'name': 'Processed spectra'}]
    files_exported = []

    traces_key = None
    fit_key = None
    init_rate_key = None

    if dataset.chosen_traces is not None:
        key += 1
        traces_key = key
        options.append({'key': str(traces_key), 'name': 'Time traces'})

    if dataset.fit is not None:
        key += 1
        fit_key = key
        options.append({'key': str(fit_key), 'name': 'Exponential fit'})

    if dataset.init_rate is not None:
        key += 1
        init_rate_key = key
        options.append({'key': str(init_rate_key), 'name': 'Initial rates'})

    if user_choices := user_choice(header=header, options=options):
        if '1' in user_choices:
            files_exported.append(export_csv(dataset, dataset.processed_spectra))

        if str(traces_key) in user_choices:
            files_exported.append(export_csv(dataset, dataset.chosen_traces, suffix='Traces'))

        if str(fit_key) in user_choices:
            files_exported.extend(
                [
                    export_csv(dataset, dataset.fit['curves'], suffix='Fit curves'),
                    export_csv(dataset, dataset.fit['params'].transpose(), suffix='Fit params')
                ]
            )

        if str(init_rate_key) in user_choices:
            files_exported.extend(
                [
                    export_csv(dataset, dataset.init_rate['lines'], suffix='Init rate lines'),
                    export_csv(dataset, dataset.init_rate['params'].transpose(), suffix='Init rate params'),
                ]
            )

    return files_exported


def _plot_and_export(args: argparse.Namespace, dataset: Dataset) -> None:
    """Plot a :class:`~uv_pro.dataset.Dataset` and prompt the user for export."""
    print('\nPlotting data...')
    if dataset.is_processed:
        files_exported = []

        if args.quick_fig is True:
            try:
                print('', splash(text='Enter ctrl-c to quit', title='uv_pro Quick Figure'))

                files_exported.append(getattr(QuickFig(dataset, args.colormap), 'exported_figure'))

            except AttributeError:
                pass

        else:
            print('Close plot window to continue...')
            plot_2x2(dataset, figsize=args.plot_size, cmap=args.colormap)

        if args.no_export is False:
            files_exported.extend(prompt_for_export(dataset))

        if files_exported:
            print(f'\nExport location: [repr.path]{os.path.dirname(args.path)}[/repr.path]')
            print('Files exported:')
            [print(f'\t[repr.filename]{file}[/repr.filename]') for file in files_exported]

    else:
        plot_spectra(dataset, dataset.raw_spectra)

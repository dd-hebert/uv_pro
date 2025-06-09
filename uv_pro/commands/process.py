"""
Functions for the ``process`` command.

@author: David Hebert
"""

import argparse
from pathlib import Path

from rich import print
from rich.columns import Columns

from uv_pro.commands import argument, command, mutually_exclusive_group
from uv_pro.dataset import Dataset
from uv_pro.io.export import export_csv
from uv_pro.plots import CMAPS, plot_2x2, plot_spectra
from uv_pro.quickfig import QuickFig
from uv_pro.utils._rich import splash
from uv_pro.utils.paths import cleanup_path, handle_args_path
from uv_pro.utils.prompts import checkbox


HELP = {
    'path': """A path to a UV-vis data file (.KD format). Required unless using --list-colormaps.""",
    'view': """Enable view-only mode (no data processing).""",
    'trim': """Remove spectra outside the specified time range.
               Spectra before T1 and after T2 will be removed.
               Use -1 for T2 to include all spectra up to the final spectrum (e.g., --trim 10 -1).""",
    'outlier-threshold': """Set the threshold (0-1) for outlier detection.
                            Values closer to 0 result in higher sensitivity (more outliers).
                            Values closer to 1 result in lower sensitivity (fewer outliers).
                            Default: 0.1""",
    'slice': 'Set the number of slices to plot. Default: None (no slicing).',
    'variable-slice': """Use non-equal spacing when slicing data. Takes 2 args: coefficient & exponent.
                         Default: None (no slicing).""",
    'specific-slice': """Get spectra slices from specific times. Takes an arbitrary number of floats.""",
    'baseline-smoothness': 'Set the smoothness of the baseline. Default: 10',
    'baseline-tolerance': 'Set the tolerance for the baseline fitting algorithm. Default: 0.1',
    'low-signal-window': """Set the low-signal outlier detection window size: "narrow", "wide", or "none".
                            Low-signal outliers can occur when the cuvette is removed, causing sharp drops
                            in absorbance that affect data cleanup. If "none", low-signal outlier
                            detection is disabled. Default: none""",
    'fit-exponential': 'Perform exponential fitting of specified time traces.',
    'initial-rates': """Perform linear fitting of specified time traces for initial rates.
                        If performing initial rates fitting, you can supply an optional float value for
                        the change in absorbance cutoff (e.g., -ir 0.15).
                        Default cutoff is 0.1 (10%% change in absorbance).""",
    'time-trace-window': """Set the wavelength window (in nm) for the time traces used in
                            outlier detection. Default is 300 1060""",
    'time-trace-interval': """Set the interval (in nm) between time traces. An interval of 10
                              will create time traces from the window MIN to MAX every 10 nm.
                              Smaller intervals may increase loading times.""",
    'time-traces': 'Specific wavelengths (in nm) to create time traces for.',
    'no-export': 'Skip the export data prompt at the end of the script.',
    'quick-fig': 'Use the quick-figure generator.',
    'colormap': """Set the colormap for the processed spectra plot. Accepts any built-in
                   Matplotlib colormap name. For a full description of colormaps see:
                   https://matplotlib.org/stable/tutorials/colors/colormaps.html.
                   Default is 'default'.""",
    'list-colormaps': 'List available colormaps and exit (path not required).',
}
ARGS = [
    argument(
        'path',
        action='store',
        type=cleanup_path,
        nargs='?',
        default=None,
        help=HELP['path'],
    ),
    argument(
        '-v',
        '--view',
        action='store_true',
        default=False,
        help=HELP['view'],
    ),
    argument(
        '-tr',
        '--trim',
        action='store',
        type=int,
        nargs=2,
        default=None,
        metavar=('T1', 'T2'),
        help=HELP['trim'],
    ),
    argument(
        '-ot',
        '--outlier-threshold',
        action='store',
        type=float,
        default=0.1,
        metavar='',
        help=HELP['outlier-threshold'],
    ),
    argument(
        '-bs',
        '--baseline-smoothness',
        action='store',
        type=float,
        default=10,
        metavar='',
        help=HELP['baseline-smoothness'],
    ),
    argument(
        '-bt',
        '--baseline-tolerance',
        action='store',
        type=float,
        default=0.1,
        metavar='',
        help=HELP['baseline-tolerance'],
    ),
    argument(
        '-lw',
        '--low-signal-window',
        action='store',
        default='none',
        choices=['narrow', 'wide', 'none'],
        help=HELP['low-signal-window'],
    ),
    argument(
        '-fx',
        '--fit-exponential',
        action='store_true',
        default=False,
        help=HELP['fit-exponential'],
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
        help=HELP['initial-rates'],
    ),
    argument(
        '-tw',
        '--time-trace-window',
        action='store',
        type=int,
        nargs=2,
        default=[300, 1060],
        metavar=('MIN', 'MAX'),
        help=HELP['time-trace-window'],
    ),
    argument(
        '-ti',
        '--time-trace-interval',
        action='store',
        type=int,
        default=10,
        metavar='',
        help=HELP['time-trace-interval'],
    ),
    argument(
        '-tt',
        '--time-traces',
        action='store',
        nargs='*',
        type=int,
        default=None,
        metavar='',
        help=HELP['time-traces'],
    ),
    argument(
        '-ne',
        '--no-export',
        action='store_true',
        default=False,
        help=HELP['no-export'],
    ),
    argument(
        '-qf',
        '--quick-fig',
        action='store_true',
        default=False,
        help=HELP['quick-fig'],
    ),
    argument(
        '-c',
        '--colormap',
        action='store',
        type=lambda s: s.lower(),
        default='default',
        choices=CMAPS.values(),
        metavar='NAME',
        help=HELP['colormap'],
    ),
    argument(
        '--list-colormaps',
        action='store_true',
        default=False,
        help=HELP['list-colormaps'],
    ),
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
            help=HELP['slice'],
        ),
        argument(
            '-vsl',
            '--variable-slice',
            action='store',
            type=float,
            nargs=2,
            default=None,
            metavar='',
            help=HELP['variable-slice'],
        ),
        argument(
            '-ssl',
            '--specific-slice',
            action='store',
            nargs='*',
            type=float,
            default=None,
            metavar='',
            help=HELP['specific-slice'],
        ),
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

    handle_args_path(args)

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
            wavelengths=args.time_traces,
        )

    print('', dataset, sep='\n')
    _plot_and_export(args, dataset)


def _handle_slicing(args: argparse.Namespace) -> dict | None:
    if args.slice:
        return {'mode': 'equal', 'slices': args.slice}

    elif args.variable_slice:
        return {
            'mode': 'variable',
            'coeff': args.variable_slice[0],
            'expo': args.variable_slice[1],
        }

    elif args.specific_slice:
        return {'mode': 'specific', 'times': args.specific_slice}

    return None


def list_colormaps():
    link = 'https://matplotlib.org/stable/tutorials/colors/colormaps.html'
    print(
        '\nValid Colormaps',
        '\n===============',
        Columns(CMAPS.values(), column_first=True),
        f'\nSee {link} for more info.',
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
    message = 'Choose data to export'
    options = ['Processed spectra']
    files_exported = []

    if dataset.chosen_traces is not None:
        options.append('Time traces')

    if dataset.fit is not None:
        options.append('Exponential fit')

    if dataset.init_rate is not None:
        options.append('Initial rates')

    user_selection = checkbox(message, options)

    if user_selection is None:
        return []

    if 'Processed spectra' in user_selection:
        files_exported.append(export_csv(dataset, dataset.processed_spectra))

    if 'Time traces' in user_selection:
        files_exported.append(
            export_csv(dataset, dataset.chosen_traces, suffix='Traces')
        )

    if 'Exponential fit' in user_selection:
        files_exported.extend(
            [
                export_csv(
                    dataset,
                    dataset.fit['curves'],
                    suffix='Fit curves'
                ),
                export_csv(
                    dataset,
                    dataset.fit['params'].transpose(),
                    suffix='Fit params'
                ),
            ]
        )

    if 'Initial rates' in user_selection:
        files_exported.extend(
            [
                export_csv(
                    dataset,
                    dataset.init_rate['lines'],
                    suffix='Init rate lines',
                ),
                export_csv(
                    dataset,
                    dataset.init_rate['params'].transpose(),
                    suffix='Init rate params',
                ),
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
                print(
                    '', splash(text='Enter ctrl-c to quit', title='uv_pro Quick Figure')
                )
                files_exported.append(
                    getattr(QuickFig(dataset, args.colormap), 'exported_figure')
                )

            except AttributeError:
                pass

        else:
            print('Close plot window to continue...')
            plot_2x2(dataset, figsize=args.plot_size, cmap=args.colormap)

        if args.no_export is False:
            files_exported.extend(prompt_for_export(dataset))

        if files_exported:
            print(
                f'\nExport location: [repr.path]{args.path.parent}[/repr.path]'
            )
            print('Files exported:')
            [
                print(f'\t[repr.filename]{file}[/repr.filename]')
                for file in files_exported
            ]

    else:
        plot_spectra(dataset, dataset.raw_spectra)

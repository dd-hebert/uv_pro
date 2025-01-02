"""
Functions for the ``process`` command.

@author: David Hebert
"""

import os
import argparse
from uv_pro.commands import command, argument, mutually_exclusive_group
from uv_pro.dataset import Dataset
from uv_pro.quickfig import QuickFig
from uv_pro.plots import plot_spectra, plot_2x2
from uv_pro.io.export import prompt_for_export


HELP = {
    'path': '''A path to a UV-vis data file (.KD format).''',
    'view': '''Enable view-only mode (no data processing).''',
    'trim': '''2 args: trim data from START to END.
               Trim the data to remove spectra outside the given time range.
               Use -1 for END to indicate the end of the data.''',
    'outlier_threshold': '''Set the threshold (0-1) for outlier detection. Default: 0.1.
                            Values closer to 0 result in higher sensitivity (more outliers).
                            Values closer to 1 result in lower sensitivity (fewer outliers).''',
    'slice': 'Set the number of slices to plot. Default: None (no slicing).',
    'gradient_slice': '''Use non-equal spacing when slicing data. Takes 2 args: coefficient & exponent.
                         Default: None (no slicing).''',
    'specific_slice': '''Get spectra slices from specific times. Takes an arbitrary number of floats.''',
    'baseline_lambda': 'Set the smoothness of the baseline. Default: 10.',
    'baseline_tolerance': 'Set the threshold (0-1) for outlier detection. Default: 0.1.',
    'low_signal_window': '''"narrow", "wide", or "none". Set the width of the low signal outlier detection window.
                             Default: "none". If "none", low signal outlier detection is skipped.''',
    'fit_exp': 'Perform exponential fitting of specified time traces. Default: False.',
    'init_rate': '''Perform linear regression of specified time traces for initial rates. Default False.
                    If performing initial rates fitting, you can supply an optional float value for
                    the change in absorbance cutoff. Default cutoff is 0.1 (10%% change in absorbance).''',
    'time_trace_window': '''Set the (min, max) wavelength (in nm) window for the time traces used in
                            outlier detection''',
    'time_trace_interval': '''Set the interval (in nm) for time traces. An interval of 10 will create time
                              traces from the window min to max every 10 nm. Smaller intervals may
                              increase loading times.''',
    'time_traces': 'Specific wavelengths (in nm) to create time traces for.',
    'no_export': 'Skip the export data prompt at the end of the script.',
    'quick_fig': 'Use the quick-figure generator.'
}
ARGS = [
    argument(
        'path',
        action='store',
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
        metavar=('START', 'END'),
        help=HELP['trim']
    ),
    argument(
        '-ot',
        '--outlier_threshold',
        action='store',
        type=float,
        default=0.1,
        metavar='',
        help=HELP['outlier_threshold']
    ),
    argument(
        '-bll',
        '--baseline_lambda',
        action='store',
        type=float,
        default=10,
        metavar='',
        help=HELP['baseline_lambda']
    ),
    argument(
        '-blt',
        '--baseline_tolerance',
        action='store',
        type=float,
        default=0.1,
        metavar='',
        help=HELP['baseline_tolerance']
    ),
    argument(
        '-lsw',
        '--low_signal_window',
        action='store',
        default='none',
        choices=['narrow', 'wide', 'none'],
        help=HELP['low_signal_window']
    ),
    argument(
        '-fit',
        '--fit_exp',
        action='store_true',
        default=False,
        help=HELP['fit_exp']
    ),
    argument(
        '-ir',
        '--init_rate',
        action='store',
        type=float,
        nargs='?',
        const='0.1',
        default=None,
        metavar='',
        help=HELP['init_rate']
    ),
    argument(
        '-ttw',
        '--time_trace_window',
        action='store',
        type=int,
        nargs=2,
        default=[300, 1060],
        metavar=('MIN', 'MAX'),
        help=HELP['time_trace_window']
    ),
    argument(
        '-tti',
        '--time_trace_interval',
        action='store',
        type=int,
        default=10,
        metavar='',
        help=HELP['time_trace_interval']
    ),
    argument(
        '-tt',
        '--time_traces',
        action='store',
        nargs='*',
        type=int,
        default=None,
        metavar='',
        help=HELP['time_traces']
    ),
    argument(
        '-ne',
        '--no_export',
        action='store_true',
        default=False,
        help=HELP['no_export']
    ),
    argument(
        '-qf',
        '--quick_fig',
        action='store_true',
        default=False,
        help=HELP['quick_fig']
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
            '-gsl',
            '--gradient_slice',
            action='store',
            type=float,
            nargs=2,
            default=None,
            metavar='',
            help=HELP['gradient_slice']
        ),
        argument(
            '-ssl',
            '--specific_slice',
            action='store',
            nargs='*',
            type=float,
            default=None,
            metavar='',
            help=HELP['specific_slice']
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
    _handle_path(args)

    if args.view is True:
        dataset = Dataset(args.path, view_only=True)

    else:
        dataset = Dataset(
            args.path,
            trim=args.trim,
            slicing=_handle_slicing(args),
            fit_exp=args.fit_exp,
            fit_init_rate=args.init_rate,
            outlier_threshold=args.outlier_threshold,
            baseline_lambda=args.baseline_lambda,
            baseline_tolerance=args.baseline_tolerance,
            low_signal_window=args.low_signal_window,
            time_trace_window=args.time_trace_window,
            time_trace_interval=args.time_trace_interval,
            wavelengths=args.time_traces
        )

    print(dataset)
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

    elif args.gradient_slice:
        return {
            'mode': 'gradient',
            'coeff': args.gradient_slice[0],
            'expo': args.gradient_slice[1]
        }

    elif args.specific_slice:
        return {
            'mode': 'specific',
            'times': args.specific_slice
        }

    return None


def _plot_and_export(args: argparse.Namespace, dataset: Dataset) -> None:
    """Plot a :class:`~uv_pro.dataset.Dataset` and prompt the user for export."""
    print('\nPlotting data...')
    if dataset.is_processed:
        files_exported = []

        if args.quick_fig is True:
            try:
                files_exported.append(getattr(QuickFig(dataset), 'exported_figure'))

            except AttributeError:
                pass

        else:
            plot_2x2(dataset, figsize=args.plot_size)

        if args.no_export is False:
            files_exported.extend(prompt_for_export(dataset))

        if files_exported:
            print(f'\nExport location: {os.path.dirname(args.path)}')
            print('Files exported:')
            [print(f'\t{file}') for file in files_exported]

    else:
        plot_spectra(dataset, dataset.raw_spectra)

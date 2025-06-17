"""
Functions for the ``process`` command.

@author: David Hebert
"""

import argparse

from rich import print

from uv_pro.commands import ArgGroup, Argument, MutuallyExclusiveGroup, command
from uv_pro.dataset import Dataset
from uv_pro.plots import plot_2x2, plot_spectra
from uv_pro.quickfig import QuickFig
from uv_pro.utils._rich import splash
from uv_pro.utils._validate import validate_colormap
from uv_pro.utils.paths import cleanup_path, handle_args_path
from uv_pro.utils.prompts import checkbox

HELP = {
    'path': """A path to a UV-vis data file (.KD format).""",
    'view': """Enable view-only mode (no data processing).""",
    'no-export': 'Skip the export data prompt at the end of the script.',
    'time-traces': 'Specific wavelengths (in nm) to get time traces for.',
    'trim': """Remove spectra outside the specified time range.
               Spectra before START and after END will be removed.
               Use -1 for END to include all spectra up to the final spectrum (e.g., --trim 10 -1).""",
    'outlier-threshold': """Set the threshold (0-1) for outlier detection.
                            Values closer to 0 result in higher sensitivity (more outliers).
                            Values closer to 1 result in lower sensitivity (fewer outliers).
                            Default: 0.1""",
    'quick-fig': 'Use the quick-figure generator.',
    'colormap': """Set the colormap for the processed spectra plot. Accepts any built-in
                   Matplotlib colormap name. For a full description of colormaps see:
                   https://matplotlib.org/stable/tutorials/colors/colormaps.html.
                   Default is 'default'.""",
    'slice': 'Set the number of equally-spaced slices to plot. Default: None (no slicing).',
    'variable-slice': """Use non-equal spacing when slicing data. Takes 2 args: coefficient & exponent.
                         Default: None (no slicing).""",
    'specific-slice': """Get spectra slices from specific times. Takes an arbitrary number of floats (time values).
                         Example: --specific-slice 10 20 50 250""",
    'fit': """Fitting type to perform on specified time traces.
              Either "exponential" or "initial-rates". Default is None.""",
    'fit-strategy': 'Perform individual or global fitting on time traces.',
    'fit-cutoff': """Indicates the cutoff for the %% change in absorbance of the time trace.
                     Only applies to "initial-rates" fitting. The default is 0.1 (10%% change).""",
    'baseline-smoothness': 'Set the smoothness of the baseline. Default: 10',
    'baseline-tolerance': 'Set the tolerance for the baseline fitting algorithm. Default: 0.1',
    'low-signal-window': """Set the low-signal outlier detection window size: "narrow", "wide", or "none".
                            Low-signal outliers can occur when the cuvette is removed, causing sharp drops
                            in absorbance that affect data cleanup. If "none", low-signal outlier
                            detection is disabled. Default: none""",
    'time-trace-window': """Set the wavelength window (in nm) for the time traces used in
                            outlier detection. Default is 300 1060""",
    'time-trace-interval': """Set the interval (in nm) between time traces. An interval of 10
                              will get time traces from the window MIN to MAX every 10 nm.
                              Smaller intervals may increase loading times.""",
    'Slicing/Sampling': 'Options to reduce many spectra to a selection of slices.',
    'Kinetics & Fitting': """Perform fitting on time traces for kinetics analysis.
                             You must specify the time traces (wavelengths) to fit with `-tt`.""",
    'Outlier Detection (advanced)': """Advanced settings for tuning outlier detection.
                                       These settings rarely need to be changed.""",
}
ARGS = [
    Argument(
        'path',
        action='store',
        type=cleanup_path,
        nargs='?',
        default=None,
        help=HELP['path'],
    ),
    Argument(
        '-v',
        '--view',
        action='store_true',
        default=False,
        help=HELP['view'],
    ),
    Argument(
        '-ne',
        '--no-export',
        action='store_true',
        default=False,
        help=HELP['no-export'],
    ),
    Argument(
        '-tt',
        '--time-traces',
        action='store',
        nargs='+',
        type=int,
        default=None,
        metavar='λ',
        help=HELP['time-traces'],
    ),
    Argument(
        '-tr',
        '--trim',
        action='store',
        type=int,
        nargs=2,
        default=None,
        metavar=('START', 'END'),
        help=HELP['trim'],
    ),
    Argument(
        '-ot',
        '--outlier-threshold',
        action='store',
        type=float,
        default=0.1,
        metavar='THRESHOLD',
        help=HELP['outlier-threshold'],
    ),
    Argument(
        '-qf',
        '--quick-fig',
        action='store_true',
        default=False,
        help=HELP['quick-fig'],
    ),
    Argument(
        '-c',
        '--colormap',
        action='store',
        type=validate_colormap,
        default='default',
        metavar='NAME',
        help=HELP['colormap'],
    ),
    ArgGroup(
        MutuallyExclusiveGroup(
            Argument(
                '-sl',
                '--slice',
                action='store',
                type=int,
                default=None,
                metavar='NUM',
                help=HELP['slice'],
            ),
            Argument(
                '-vsl',
                '--variable-slice',
                action='store',
                type=float,
                nargs=2,
                default=None,
                metavar=('COEFF', 'EXPO'),
                help=HELP['variable-slice'],
            ),
            Argument(
                '-ssl',
                '--specific-slice',
                action='store',
                nargs='+',
                type=float,
                default=None,
                metavar='TIME',
                help=HELP['specific-slice'],
            ),
        ),
        title='Slicing/Sampling',
        description=HELP['Slicing/Sampling'],
    ),
    ArgGroup(
        Argument(
            '-f',
            '--fit',
            action='store',
            choices=['exponential', 'initial-rates'],
            default=None,
            help=HELP['fit'],
        ),
        Argument(
            '--cutoff',
            action='store',
            dest='fit_cutoff',
            type=float,
            default=0.1,
            metavar='',
            help=HELP['fit-cutoff'],
        ),
        Argument(
            '--global',
            action='store_const',
            dest='fit_strategy',
            const='global',
            default='individual',
            help=HELP['fit-strategy'],
        ),
        title='Kinetics & Fitting',
        description=HELP['Kinetics & Fitting'],
    ),
    ArgGroup(
        Argument(
            '-bs',
            '--baseline-smoothness',
            action='store',
            type=float,
            default=10,
            metavar='',
            help=HELP['baseline-smoothness'],
        ),
        Argument(
            '-bt',
            '--baseline-tolerance',
            action='store',
            type=float,
            default=0.1,
            metavar='',
            help=HELP['baseline-tolerance'],
        ),
        Argument(
            '-lw',
            '--low-signal-window',
            action='store',
            default='none',
            choices=['narrow', 'wide', 'none'],
            help=HELP['low-signal-window'],
        ),
        Argument(
            '-tw',
            '--time-trace-window',
            action='store',
            type=int,
            nargs=2,
            default=[300, 1060],
            metavar=('MIN', 'MAX'),
            help=HELP['time-trace-window'],
        ),
        Argument(
            '-ti',
            '--time-trace-interval',
            action='store',
            type=int,
            default=10,
            metavar='',
            help=HELP['time-trace-interval'],
        ),
        title='Outlier Detection (advanced)',
        description=HELP['Outlier Detection (advanced)'],
    ),
]


@command(args=ARGS, aliases=['p', 'proc'])
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
    handle_args_path(args)

    if args.view is True:
        dataset = Dataset(args.path, view_only=True)

    else:
        dataset = Dataset(
            args.path,
            trim=args.trim,
            slicing=_handle_slicing(args),
            fit=args.fit,
            fit_strategy=args.fit_strategy,
            fit_cutoff=args.fit_cutoff,
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
        options.append('Time traces (raw)')

    if dataset.processed_traces is not None:
        options.append('Time traces (processed)')

    if dataset.fit == 'exponential' and dataset.fit_result is not None:
        options.append('Exponential fit')

    if dataset.fit == 'initial-rates' and dataset.fit_result is not None:
        options.append('Initial rates')

    user_selection = checkbox(message, options)

    if user_selection is None:
        return []

    if 'Processed spectra' in user_selection:
        files_exported.append(dataset.export_csv(dataset.processed_spectra))

    if 'Time traces (raw)' in user_selection:
        files_exported.append(
            dataset.export_csv(dataset.chosen_traces, suffix='traces_raw')
        )

    if 'Time traces (processed)' in user_selection:
        files_exported.append(
            dataset.export_csv(dataset.processed_traces, suffix='traces_processed')
        )

    if 'Exponential fit' in user_selection:
        files_exported.extend(
            [
                dataset.export_csv(dataset.fit_result.fitted_data, suffix='fit_curves'),
                dataset.export_csv(
                    dataset.fit_result.params.transpose(), suffix='fit_params'
                ),
            ]
        )

    if 'Initial rates' in user_selection:
        files_exported.extend(
            [
                dataset.export_csv(
                    dataset.fit_result.fitted_data,
                    suffix='init_rate_lines',
                ),
                dataset.export_csv(
                    dataset.fit_result.params.transpose(),
                    suffix='init_rate_params',
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
            print(f'\nExport location: [repr.path]{args.path.parent}[/repr.path]')
            print('Files exported:')
            [
                print(f'\t[repr.filename]{file}[/repr.filename]')
                for file in files_exported
            ]

    else:
        plot_spectra(dataset, dataset.raw_spectra)

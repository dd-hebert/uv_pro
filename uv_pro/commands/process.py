"""
Functions for the ``process`` command.

@author: David Hebert
"""

import os
import argparse
from rich import print, box
from rich.console import RenderableType
from rich.columns import Columns
from rich.panel import Panel
from rich.table import Table, Column
from rich.text import Text
from uv_pro.commands import command, argument, mutually_exclusive_group
from uv_pro.dataset import Dataset
from uv_pro.quickfig import QuickFig
from uv_pro.plots import plot_spectra, plot_2x2
from uv_pro.io.export import export_csv
from uv_pro.utils.prompts import user_choice


HELP = {
    'path': '''A path to a UV-vis data file (.KD format).''',
    'view': '''Enable view-only mode (no data processing).''',
    'trim': '''Remove spectra outside the given time range.
               Data before time = T1 and after time = T2 will be removed.
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
        metavar=('T1', 'T2'),
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

    print(*_rich_text(dataset), sep='\n')
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


def _rich_text(dataset: Dataset) -> list[RenderableType]:
    def processing_panel(dataset: Dataset) -> Panel:
        title = dataset.name
        if len(title) > 74:
            title = title[:36] + '...' + title[-35:]

        subtitle = [
            f'Total Spectra: {len(dataset.raw_spectra.columns)}',
            f'Total time: {dataset.spectra_times.max()} s'
        ]

        subtitle += [f'Cycle time: {dataset.cycle_time} s'] if dataset.cycle_time else []

        left = Table('', '', show_header=False, box=box.SIMPLE, expand=False)
        right = Table('', '', show_header=False, box=box.SIMPLE, expand=False)

        if dataset.is_processed:
            if dataset.trim:
                start, end = dataset.trim
                left.add_row(
                    'Trimmed start (s)',
                    Text(f'{start}', style='medium_purple1')
                )
                left.add_row(
                    'Trimmed end (s)',
                    Text(f'{end}', style='medium_purple1')
                )

            left.add_row(
                'Outliers found ',
                Text(f'{len(dataset.outliers)}', style='medium_purple1')
            )

            if dataset.slicing is None:
                right.add_row(
                    'Spectra remaining ',
                    Text(f'{len(dataset.processed_spectra.columns)}', style='medium_purple1')
                )

            else:
                right.add_row(
                    'Slicing mode',
                    Text(f'{dataset.slicing["mode"]}', style='medium_purple1')
                )

                if dataset.slicing['mode'] == 'gradient':
                    right.add_row(
                        'Slicing coefficient',
                        Text(f'{dataset.slicing["coeff"]}', style='medium_purple1')
                    )
                    right.add_row(
                        'Slicing exponent',
                        Text(f'{dataset.slicing["expo"]}', style='medium_purple1')
                    )

                right.add_row(
                    'Slices ',
                    Text(f'{len(dataset.processed_spectra.columns)}', style='medium_purple1')
                )

        return Panel(
            Columns([left, right], expand=True, align='left'),
            title=Text(title, style='grey0 on medium_purple3'),
            subtitle=Text('\t'.join(subtitle), style='table.caption'),
            width=80,
            box=box.ROUNDED,
            expand=True
        )

    def fit_panel(fit: dict) -> Panel:
        equation = 'f(t) = abs_f + (abs_0 - abs_f) * exp(-kobs * t)'
        table = Table(
            Column('λ (nm)', justify='right', ratio=1),
            Column('kobs (s-1)', justify='center', style='medium_purple1', ratio=3),
            Column('abs_0 (a.u.)', justify='center', ratio=2),
            Column('abs_f (a.u.)', justify='center', ratio=2),
            Column('r²', justify='center', ratio=2),
            width=80,
            box=box.HORIZONTALS,
            row_styles=['grey100', 'white'],
        )

        for wavelength in fit['params'].columns:
            params = fit['params'][wavelength]
            color = 'red' if params['r2'] < 0.85 else 'none'
            table.add_row(
                str(wavelength),
                '{: .2e} ± {:.2e}'.format(params['kobs'], params['kobs err']),
                '{: .3f}'.format(params['abs_0']),
                '{: .3f}'.format(params['abs_f']),
                Text('{:.4f}'.format(params['r2']), style=color)
            )

        return Panel(
            table,
            title=Text('Exponential Fit Results', style='grey0 on medium_purple3'),
            subtitle=Text(f'Fit function: {equation}', style='table.caption'),
            width=80,
            box=box.SIMPLE
        )

    def init_rate_panel(init_rate: dict) -> Panel:
        table = Table(
            Column('λ (nm)', justify='right', ratio=1),
            Column('rate (a.u./s)', justify='center', style='medium_purple1', ratio=3),
            Column('Δabs (%)', justify='center', ratio=2),
            Column('Δt (s)', justify='center', ratio=2),
            Column('r²', justify='center', ratio=2),
            width=80,
            expand=True,
            box=box.HORIZONTALS,
            row_styles=['grey100', 'white'],
        )

        for wavelength in init_rate['params'].columns:
            params = init_rate['params'][wavelength]
            color = 'red' if params['r2'] < 0.85 else 'none'
            table.add_row(
                str(wavelength),
                '{: .2e} ± {:.2e}'.format(params['slope'], params['slope err']),
                '{:.2%}'.format(abs(params['delta_abs_%'])),
                '{:.1f}'.format(params['delta_t']),
                Text('{:.4f}'.format(params['r2']), style=color)
            )

        return Panel(
            table,
            title=Text('Initial Rates Results', style='grey0 on medium_purple3'),
            width=80,
            box=box.SIMPLE
        )

    renderables = ['', processing_panel(dataset)]
    log = []

    if dataset.fit is not None:
        renderables.extend(['', fit_panel(dataset.fit)])

        if unable_to_fit := set(dataset.chosen_traces.columns).difference(set(dataset.fit['curves'].columns)):
            log.append(Text(f'Unable to fit exponential to: {", ".join(map(str, unable_to_fit))} nm.', style='red'))

    if dataset.init_rate is not None:
        renderables.extend(['', init_rate_panel(dataset.init_rate)])

    if log:
        renderables.extend(log)

    return renderables


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
                print(
                    '',
                    Panel(
                        Text('Enter ctrl-c to quit', style='bold grey100', justify='center'),
                        title=Text('uv_pro Quick Figure', style='table.title'),
                        border_style='grey27',
                        width=80,
                        box=box.SIMPLE
                    )
                )

                files_exported.append(getattr(QuickFig(dataset), 'exported_figure'))

            except AttributeError:
                pass

        else:
            print('Close plot window to continue...')
            plot_2x2(dataset, figsize=args.plot_size)

        if args.no_export is False:
            files_exported.extend(prompt_for_export(dataset))

        if files_exported:
            print(f'\nExport location: [repr.path]{os.path.dirname(args.path)}[/repr.path]')
            print('Files exported:')
            [print(f'\t[repr.filename]{file}[/repr.filename]') for file in files_exported]

    else:
        plot_spectra(dataset, dataset.raw_spectra)


def nm_to_color(wavelength: int) -> str:
    colors = [
        ((685, 740), 'dark_red'),
        ((625, 685), 'red1'),
        ((607, 625), 'orange_red1'),
        ((590, 607), 'orange1'),
        ((577, 590), 'gold1'),
        ((565, 577), 'yellow1'),
        ((532, 565), 'green_yellow'),
        ((500, 532), 'green1'),
        ((492, 500), 'aquamarine1'),
        ((485, 492), 'cyan1'),
        ((462, 485), 'deep_sky_blue1'),
        ((440, 462), 'blue1'),
        ((410, 440), 'blue_violet'),
        ((380, 410), 'dark_violet')
    ]

    for (low, high), color in colors:
        if low < wavelength <= high:
            return color

    return 'none'

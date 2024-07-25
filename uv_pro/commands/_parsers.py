"""
Helper functions for argparse boilerplate.
Gets subparsers for CLI commands and parses command line args.

@author: David Hebert
"""

import argparse
from uv_pro.commands.process import process
from uv_pro.commands.multiview import multiview
from uv_pro.commands.config import config
from uv_pro.commands.browse import browse
from uv_pro.commands.batch import batch
from uv_pro.commands.tree import tree


def get_args() -> argparse.Namespace:
    """Collect all command-line args."""
    main_parser = argparse.ArgumentParser(description='Process UV-vis Data Files')
    subparsers = main_parser.add_subparsers(help='Subcommands')

    _batch(subparsers)
    _browse(subparsers)
    _config(subparsers)
    _multiview(subparsers)
    _process(subparsers)
    _tree(subparsers)

    return main_parser.parse_args()


def _batch(subparser: argparse._SubParsersAction) -> None:
    """Get args for ``batch`` subcommand."""
    help_msg = {
        'search_filters': '''An arbitrary number of search filters''',
        'wavelengths': 'The time trace wavelengths (in nm) to batch export.'
    }

    batch_subparser: argparse.ArgumentParser = subparser.add_parser(
        'batch',
        description='Batch exporting of multiple .KD files.',
        help='Batch exporting of multiple .KD files.'
    )

    batch_subparser.add_argument(
        'wavelengths',
        action='store',
        nargs='+',
        type=int,
        default=None,
        help=help_msg['wavelengths']
    )
    batch_subparser.add_argument(
        '-f',
        '--search_filters',
        action='store',
        nargs='*',
        default='*',
        metavar='',
        help=help_msg['search_filters']
    )

    batch_subparser.set_defaults(func=batch)


def _browse(subparser: argparse._SubParsersAction) -> None:
    """Get args for ``browse`` subcommand."""
    browse_subparser: argparse.ArgumentParser = subparser.add_parser(
        'browse',
        description='Browse for a .KD file in the root directory and open it in view-only mode.',
        aliases=['br'],
        help='Browse for a .KD file in the root directory and open it in view-only mode.'
    )

    browse_subparser.set_defaults(func=browse)


def _config(subparser: argparse._SubParsersAction) -> None:
    """Get args for ``config`` subcommand."""
    help_msg = {
        'delete': '''Delete the config file.''',
        'edit': '''Edit config settings.''',
        'list': '''Print the current config settings to the console.''',
        'reset': '''Reset config settings back to their default value.''',
    }

    config_subparser: argparse.ArgumentParser = subparser.add_parser(
        'config',
        description='View and modify config settings. Available config settings: root_directory, plot_size',
        aliases=['cfg'],
        help='View and modify config settings.'
    )

    config_subparser.set_defaults(func=config)

    mutually_exclusive = config_subparser.add_mutually_exclusive_group()
    mutually_exclusive.add_argument(
        '-delete',
        action='store_true',
        default=False,
        help=help_msg['delete']
    )
    mutually_exclusive.add_argument(
        '-edit',
        action='store_true',
        default=False,
        help=help_msg['edit']
    )
    mutually_exclusive.add_argument(
        '-list',
        action='store_true',
        default=False,
        help=help_msg['list']
    )
    mutually_exclusive.add_argument(
        '-reset',
        action='store_true',
        default=False,
        help=help_msg['reset']
    )


def _multiview(subparser: argparse._SubParsersAction) -> None:
    """Get args for ``multiview`` subcommand."""
    help_msg = {
        'search_filters': '''An arbitrary number of search filters''',
        'and_filter': '``and`` filter mode.',
        'or_filter': '``or`` filter mode.'
    }

    multiview_subparser: argparse.ArgumentParser = subparser.add_parser(
        'multiview',
        description='Open multiple UV-vis data files in view-only mode.',
        aliases=['mv'],
        help='Open multiple UV-vis data files in view-only mode.'
    )

    multiview_subparser.set_defaults(
        filter_mode='or',
        func=multiview
    )

    multiview_subparser.add_argument(
        '-f',
        '--search_filters',
        action='store',
        nargs='*',
        default='*',
        metavar='',
        help=help_msg['search_filters']
    )
    filter_args = multiview_subparser.add_mutually_exclusive_group(required=False)
    filter_args.add_argument(
        '-a',
        '--and_filter',
        dest='filter_mode',
        action='store_const',
        const='and',
        help=help_msg['and_filter']
    )
    filter_args.add_argument(
        '-o',
        '--or_filter',
        dest='filter_mode',
        action='store_const',
        const='or',
        help=help_msg['or_filter']
    )


def _process(subparser: argparse._SubParsersAction) -> None:
    """Get args for ``process`` subcommand."""
    help_msg = {
        'path': '''A path to a UV-vis Data File (.KD format).''',
        'view': '''Enable view-only mode (no data processing).''',
        'trim': '''2 args: trim data from __ to __.
                    Trim the data to remove spectra outside the given time range.''',
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
                                    Default: "narrow". If "none", low signal outlier detection is skipped.''',
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

    process_subparser: argparse.ArgumentParser = subparser.add_parser(
        'process',
        description='Process UV-vis Data',
        aliases=['p', 'proc'],
        help='Process .KD UV-vis data files.'
    )

    process_subparser.set_defaults(func=process)

    process_subparser.add_argument(
        'path',
        action='store',
        default=None,
        help=help_msg['path']
    )
    process_subparser.add_argument(
        '-v',
        '--view',
        action='store_true',
        default=False,
        help=help_msg['view']
    )
    process_subparser.add_argument(
        '-tr',
        '--trim',
        action='store',
        type=int,
        nargs=2,
        default=None,
        metavar='',
        help=help_msg['trim']
    )
    process_subparser.add_argument(
        '-ot',
        '--outlier_threshold',
        action='store',
        type=float,
        default=0.1,
        metavar='',
        help=help_msg['outlier_threshold']
    )
    slicing_args = process_subparser.add_mutually_exclusive_group()
    slicing_args.add_argument(
        '-sl',
        '--slice',
        action='store',
        type=int,
        default=None,
        metavar='',
        help=help_msg['slice']
    )
    slicing_args.add_argument(
        '-gsl',
        '--gradient_slice',
        action='store',
        type=float,
        nargs=2,
        default=None,
        metavar='',
        help=help_msg['gradient_slice']
    )
    slicing_args.add_argument(
        '-ssl',
        '--specific_slice',
        action='store',
        nargs='*',
        type=float,
        default=None,
        metavar='',
        help=help_msg['specific_slice']
    )
    process_subparser.add_argument(
        '-bll',
        '--baseline_lambda',
        action='store',
        type=float,
        default=10,
        metavar='',
        help=help_msg['baseline_lambda']
    )
    process_subparser.add_argument(
        '-blt',
        '--baseline_tolerance',
        action='store',
        type=float,
        default=0.1,
        metavar='',
        help=help_msg['baseline_tolerance']
    )
    process_subparser.add_argument(
        '-lsw',
        '--low_signal_window',
        action='store',
        default='narrow',
        choices=['narrow', 'wide', 'none'],
        metavar='',
        help=help_msg['low_signal_window']
    )
    process_subparser.add_argument(
        '-fit',
        '--fit_exp',
        action='store_true',
        default=False,
        help=help_msg['fit_exp']
    )
    process_subparser.add_argument(
        '-ir',
        '--init_rate',
        action='store',
        type=float,
        nargs='?',
        const='0.1',
        default=None,
        metavar='',
        help=help_msg['init_rate']
    )
    process_subparser.add_argument(
        '-ttw',
        '--time_trace_window',
        action='store',
        type=int,
        nargs=2,
        default=[300, 1060],
        metavar='',
        help=help_msg['time_trace_window']
    )
    process_subparser.add_argument(
        '-tti',
        '--time_trace_interval',
        action='store',
        type=int,
        default=10,
        metavar='',
        help=help_msg['time_trace_interval']
    )
    process_subparser.add_argument(
        '-tt',
        '--time_traces',
        action='store',
        nargs='*',
        type=int,
        default=None,
        metavar='',
        help=help_msg['time_traces']
    )
    process_subparser.add_argument(
        '-ne',
        '--no_export',
        action='store_true',
        default=False,
        help=help_msg['no_export']
    )
    process_subparser.add_argument(
        '-qf',
        '--quick_fig',
        action='store_true',
        default=False,
        help=help_msg['quick_fig']
    )


def _tree(subparser: argparse._SubParsersAction) -> None:
    """Get args for ``tree`` subcommand."""
    tree_subparser: argparse.ArgumentParser = subparser.add_parser(
        'tree',
        description='Show the root directory file tree.',
        help='Show the root directory file tree.'
    )

    tree_subparser.set_defaults(func=tree)

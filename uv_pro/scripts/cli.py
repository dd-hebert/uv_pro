"""
Run ``uv_pro`` from the command line.

With the ``uv_pro`` package installed, this script can be called directly from
the command line with::

    uvp process myfile.KD

The accepted commands and their options are given below. The shorthand for commands
are given in parenthesis.

Commands
========

process (p, proc)
-----------------
Usage: ``uvp p <path> <options>``, ``uvp proc <path> <options>``, or ``uvp process <path> <options>``

path : str, required
    The path to a .KD file. Paths containing spaces should be wrapped in double
    quotes "". The script will first look for the file inside the current
    working directory, then look at the absolute path, and lastly
    inside the root directory (if a root directory has been set).
-bll, --baseline_lambda : float, optional
    Set the smoothness of the baseline (for outlier detection). Higher values
    give smoother baselines. Try values between 0.001 and 10000. The
    default is 10. See :func:`pybaselines.whittaker.asls()` for more information.
-blt, --baseline_tolerance : float, optional
    Set the exit criteria for the baseline algorithm. Try values between
    0.001 and 10000. The default is 0.1. See :func:`pybaselines.whittaker.asls()`
    for more information.
-fit, --fitting : flag, optional
    Perform exponential fitting on time traces given by ``-tt``.
-gsl, --gradient_slice : float float, optional
    Slice the data in non-equally spaced slices. Give a coefficient
    and an exponent. The data slicing will be determined by the equation
    y = coefficient*x^exponent + 1, where y is the step size between slices.
    The default is None, where all spectra are plotted or exported.
-lsw, --low_signal_window : ``"narrow"`` or ``"wide"``, optional
    Set the width of the low signal outlier detection window (see
    :func:`~uv_pro.outliers.find_outliers()`). Set to ``"wide"`` if low
    signals are interfering with the baseline.
-ne, --no_export : flag, optional
    Use this argument to bypass the export data prompt at the end of the script.
-ot, --outlier_threshold : float, optional
    The threshold by which spectra are considered outliers. Values closer to 0
    produce more outliers. Values closer to 1 produce fewer outliers. A value
    >> 1 will produce no outliers. The default value is 0.1.
-qf, --quick_fig : flag, optional
    Use the quick figure generator to create and export plot figures.
-sl, --slice : int, optional
    The number of equally-spaced slices to plot or export. Example: if
    :attr:`~uv_pro.process.Dataset.processed_spectra` contains 100 spectra and
    ``slice`` is 10, then every tenth spectrum will be kept. The
    default is None, where all spectra are plotted or exported.
-ssl, --specific_slice : list[int], optional
    Get slices at specific times. Takes an arbitrary number of floats.
    The default is None, where all spectra are plotted or exported.
-tr, --trim : int int, optional
    Trim data outside a given time range: ``[trim_before, trim_after]``.
    Default value is None (no trimming).
-tt, --time_traces : arbitrary number of ints, optional
    A list of specific wavelengths (in nm) to create time traces for.
    These time traces are independent from the time traces created by
    :meth:`~uv_pro.process.Dataset.get_time_traces()`.
-tti, --time_trace_interval : int, optional
    Set the interval (in nm) for time traces. An interval of 10 will create
    time traces from the window min to max every 10 nm. Smaller intervals
    may increase loading times. Used in :meth:`~uv_pro.process.Dataset.get_time_traces()`.
    The default is 10.
-ttw, --time_trace_window : int int, optional
    Set the (min, max) wavelength (in nm) range to get time traces for.
    Used in :meth:`~uv_pro.process.Dataset.get_time_traces()`.
    The default is 300 1060.
-v : flag, optional
    Enable view-only mode. No data processing is performed and a plot of
    the data set is shown. Default is False.

browse (br)
-----------
Usage: ``uvp browse`` or ``uvp br``

Interactively pick a .KD file from the console. The file is opened in view-
only mode. The .KD file must be located inside the root directory.

multiview (mv)
--------------
Usage: ``uvp multiview <options>`` or ``uvp mv <options>``

View multiple .KD files from the command line.

-f, --search_filters : arbitrary number of strings, optional
    A sequence of search filter strings. For example, passing ``-f copper A``
    will open .KD files which contain 'copper' OR 'A' in their filename.
    Passing no filters opens all .KD files in the current working directory.
-a, --and_filter: flag, optional
    Enable AND filter mode. For example, passing ``-f copper A -a`` will open
    .KD files which contain both 'copper' AND 'A' in their filename. Default False.
-o, --or_filter: flag, optional
    Enable OR filter mode (the default filter mode). For example, passing
    ``-f copper A -a`` will open .KD files which contain both 'copper' OR 'A'
    in their filename. Default True.

root (rt)
---------
Usage: ``uvp rt <options>`` or ``uvp root <options>``

-clear : flag, optional
    Clear the current root directory.
-get : flag, optional
    Print the current root directory to the console.
-set : str, optional
    Set a root directory to simplify file path entry. For instance, if
    you store all your UV-vis data files in a common folder, you can designate
    it as the root directory. Subsequently, you can omit the root directory
    portion of the path when processing data and just provide a relative path.

config (cfg)
------------
Usage: ``uvp config <option>`` or ``uvp cfg <option>``

View, edit, or reset the script configuration settings.

-get : flag, optional
    Print the current configuration settings to the console.
-reset : flag, optional
    Reset a configuration setting back to the default value. Will prompt the user
    for a selection of configuration settings to reset.
-set : flag, optional
    Edit and set a configuration setting. Will prompt the user for a selection of
    configuration settings to edit.

tree
----
Usage: ``uvp tree``

Print the root directory file tree to the console.

Examples
--------
::

    # Open myfile.KD in view-only mode.
    uvp process C:/Desktop/myfile.KD -v
    # or use abbreviation `p`
    uvp p C:/Desktop/myfile.KD -v

    # Set a root directory.
    uvp root -set C:/Desktop
    # Now C:/Desktop can be omitted from the given path.

    # Open C:/Desktop/myfile.KD, show 10 spectra from 50 to 250 seconds
    # with outlier threshold of 0.2. Get time traces at 780 nm and 1020 nm.
    # Fit exponential to time traces at 780 nm and 1020 nm.
    uvp p myfile.KD -tr 50 250 -ot 0.2 -sl 10 -tt 780 1020 -fit

@author: David Hebert
"""
import sys
import argparse
import os
from uv_pro.process import Dataset
import uv_pro.plots as uvplt
from uv_pro.io.export import prompt_for_export
from uv_pro.utils.config import Config
from uv_pro.utils.filepicker import FilePicker
from uv_pro.utils.printing import prompt_user_choice, prompt_for_value
from uv_pro.utils.quickfig import QuickFig
from uv_pro.scripts.multiview import multiview


sys.tracebacklimit = 0


class CLI:
    """
    Command line interface class.

    Attributes
    ----------
    args : :class:`argparse.Namespace`
        Parsed command-line arguments.
    cfg : :class:`~uv_pro.utils.config.Config`
        The current CLI settings configuration.
    """

    def __init__(self):
        self.cfg = Config()
        self.args = self.get_args()

        try:
            self.args.func()

        except AttributeError:
            pass

    def get_args(self) -> argparse.Namespace:
        """Collect all command-line args."""
        main_parser = argparse.ArgumentParser(description='Process UV-vis Data Files')

        subparsers = main_parser.add_subparsers(
            help='Subcommands'
        )

        self._process_args(subparsers)
        self._browse_args(subparsers)
        self._multiview_args(subparsers)
        self._tree_args(subparsers)
        self._root_args(subparsers)
        self._config_args(subparsers)
        self._test_args(subparsers)

        return main_parser.parse_args()

    def _process_args(self, subparsers: argparse._SubParsersAction) -> None:
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
            'time_traces': 'A list of specific wavelengths (in nm) to create time traces for.',
            'no_export': 'Skip the export data prompt at the end of the script.',
            'quick_fig': 'Use the quick-figure generator.'
        }

        process_subparser: argparse.ArgumentParser = subparsers.add_parser(
            'process',
            description='Process UV-vis Data',
            aliases=['p', 'proc'],
            help='Process .KD UV-vis data files.'
        )

        process_subparser.set_defaults(
            func=self.process
        )

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

    def _browse_args(self, subparsers: argparse._SubParsersAction) -> None:
        """Get args for ``browse`` subcommand."""
        help_msg = {
            'browse': 'Browse for a .KD file in the root directory \
                       and open it in view-only mode.',
        }

        filepicker_subparser: argparse.ArgumentParser = subparsers.add_parser(
            'browse',
            description='Browse for a .KD file in the root directory \
                         and open it in view-only mode.',
            aliases=['br'],
            help=help_msg['browse']
        )

        filepicker_subparser.set_defaults(
            func=self.browse,
            selectfile=True
        )

    def _multiview_args(self, subparsers: argparse._SubParsersAction) -> None:
        help_msg = {
        'search_filters': '''An arbitrary number of search filters''',
        'and_filter': '``and`` filter mode.',
        'or_filter': '``or`` filter mode.'
        }

        multiview_subparser: argparse.ArgumentParser = subparsers.add_parser(
            'multiview',
            description='Open multiple UV-vis data files in view-only mode.',
            aliases=['mv'],
            help='Open multiple UV-vis data files in view-only mode.'
        )

        multiview_subparser.set_defaults(
            filter_mode='or',
            func=self.multiview
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

    def _tree_args(self, subparsers: argparse._SubParsersAction) -> None:
        """Get args for ``tree`` subcommand."""
        help_msg = {
            'tree': 'Show the root directory file tree.'
        }

        tree_subparser: argparse.ArgumentParser = subparsers.add_parser(
            'tree',
            description='Show the root directory file tree.',
            help=help_msg['tree']
        )

        tree_subparser.set_defaults(
            func=self.tree,
            tree=True
        )

    def _root_args(self, subparsers: argparse._SubParsersAction) -> None:
        """Get args for ``root`` subcommand."""
        help_msg = {
            'set': '''Set a root directory where data files are located to enable
                      typing shorter relative file paths.''',
            'get': '''Print the root directory to the console.''',
            'clear': '''Clear the current root directory.''',
        }

        rootdir_subparser: argparse.ArgumentParser = subparsers.add_parser(
            'root',
            description='Root directory settings.',
            aliases=['rt'],
            help='Root directory settings.',
        )

        rootdir_subparser.set_defaults(
            func=self.root
        )

        mutually_exclusive = rootdir_subparser.add_mutually_exclusive_group()
        mutually_exclusive.add_argument(
            '-clear',
            action='store_true',
            default=False,
            help=help_msg['clear']
        )
        mutually_exclusive.add_argument(
            '-get',
            action='store_true',
            default=False,
            help=help_msg['get']
        )
        mutually_exclusive.add_argument(
            '-set',
            action='store',
            default=None,
            metavar='',
            help=help_msg['set']
        )

    def _config_args(self, subparsers: argparse._SubParsersAction) -> None:
        help_msg = {
            'set': '''Edit config settings.''',
            'get': '''Print the current config settings to the console.''',
            'reset': '''Reset config settings back to their default value.''',
        }

        config_subparser: argparse.ArgumentParser = subparsers.add_parser(
            'config',
            description='View and modify config settings. Available config settings: root_directory, plot_size',
            aliases=['cfg'],
            help='View and modify config settings.'
        )

        config_subparser.set_defaults(
            func=self.config
        )

        mutually_exclusive = config_subparser.add_mutually_exclusive_group()
        mutually_exclusive.add_argument(
            '-set',
            action='store_true',
            default=False,
            help=help_msg['set']
        )
        mutually_exclusive.add_argument(
            '-get',
            action='store_true',
            default=False,
            help=help_msg['get']
        )
        mutually_exclusive.add_argument(
            '-reset',
            action='store_true',
            default=False,
            help=help_msg['reset']
        )

    def _test_args(self, subparsers: argparse._SubParsersAction) -> None:
        help_msg = {
            'test_mode': 'For testing purposes.',
        }

        test_subparser: argparse.ArgumentParser = subparsers.add_parser(
            'test',
            description='For testing purposes.',
            help=help_msg['test_mode']
        )

        test_subparser.set_defaults(
            func=self.test_mode,
            test=True
        )

    def process(self) -> None:
        """
        Process data.

        Initializes a :class:`~uv_pro.process.Dataset` with the
        given ``args``, plots the result, and prompts the user
        for exporting.
        """
        self._handle_path(self.get_root_dir())

        if self.args.view is True:
            dataset = Dataset(self.args.path, view_only=True)

        else:
            dataset = Dataset(
                self.args.path,
                trim=self.args.trim,
                slicing=self._handle_slicing(),
                fit_exp=self.args.fit_exp,
                fit_init_rate=self.args.init_rate,
                outlier_threshold=self.args.outlier_threshold,
                baseline_lambda=self.args.baseline_lambda,
                baseline_tolerance=self.args.baseline_tolerance,
                low_signal_window=self.args.low_signal_window,
                time_trace_window=self.args.time_trace_window,
                time_trace_interval=self.args.time_trace_interval,
                wavelengths=self.args.time_traces
            )

        print(dataset)
        self._plot_and_export(dataset)

    def _handle_path(self, root_dir: str | None) -> None:
        current_dir = os.getcwd()
        path_exists = os.path.exists(os.path.join(current_dir, self.args.path))

        if path_exists:
            self.args.path = os.path.join(current_dir, self.args.path)

        elif root_dir is not None and os.path.exists(os.path.join(root_dir, self.args.path)):
            self.args.path = os.path.join(root_dir, self.args.path)

        else:
            raise FileNotFoundError(f'No such file or directory could be found: "{self.args.path}"')

    def _handle_slicing(self) -> dict | None:
        if self.args.slice:
            return {'mode': 'equal', 'slices': self.args.slice}

        elif self.args.gradient_slice:
            return {
                'mode': 'gradient',
                'coeff': self.args.gradient_slice[0],
                'expo': self.args.gradient_slice[1]
            }

        elif self.args.specific_slice:
            return {
                'mode': 'specific',
                'times': self.args.specific_slice
            }

        return None

    def _plot_and_export(self, dataset: Dataset) -> None:
        """Plot a :class:`~uv_pro.process.Dataset` and prompt the user for export."""
        print('\nPlotting data...')
        if dataset.is_processed:
            files_exported = []

            if self.args.quick_fig is True:
                try:
                    files_exported.append(getattr(QuickFig(dataset), 'exported_figure'))

                except AttributeError:
                    pass

            else:
                uvplt.plot_2x2(dataset, figsize=self._get_figsize())

            if self.args.no_export is False:
                files_exported.extend(prompt_for_export(dataset))

            if files_exported:
                print(f'\nExport location: {os.path.dirname(self.args.path)}')
                print('Files exported:')
                [print(f'\t{file}') for file in files_exported]

        else:
            uvplt.plot_spectra(dataset, dataset.raw_spectra)

    def _get_figsize(self) -> tuple[int, int]:
        return tuple(map(int, self.cfg.get('Settings', 'plot_size').split()))

    def browse(self) -> None:
        if root_dir := self.get_root_dir():
            if file := FilePicker(root_dir, '.KD').pick_file():
                self.args.path = file[0]
                self.args.view = True
                self.process()

    def multiview(self):
        multiview(
            search_filters=self.args.search_filters,
            filter_mode=self.args.filter_mode
        )

    def tree(self) -> None:
        if root_dir := self.get_root_dir():
            FilePicker(root_dir, '.KD').tree()

    def root(self):
        if self.args.set is not None:
            self.modify_root_dir(self.args.set)

        if self.args.clear:
            self.clear_root_dir()

        if self.args.get:
            print(f'root directory: {self.get_root_dir()}')

    def get_root_dir(self) -> str:
        root_dir = self.cfg.get('Root Directory', 'root_directory')
        return root_dir if root_dir else None

    def modify_root_dir(self, directory: str) -> None:
        if os.path.exists(directory):
            self.cfg.modify('Root Directory', 'root_directory', directory)
        else:
            raise FileNotFoundError(f'The directory does not exist: {directory}')

    def clear_root_dir(self) -> None:
        self.cfg.reset()

    def config(self) -> None:
        if self.args.get:
            print('\nConfig settings')
            print('===============')
            for setting, value in self.cfg.items('Settings'):
                print(f'{setting}: {value}')
            print('')

        else:
            if self.args.set:
                header = 'Set config settings'
                func = self._config_set
            if self.args.reset:
                header = 'Reset config settings'
                func = self._config_reset

            options = []
            settings_keys = {}
            for key, (setting, value) in enumerate(self.cfg.items('Settings'), start=1):
                options.append({'key': str(key), 'name': f'{setting}: {value}'})
                settings_keys[str(key)] = setting

            if user_choices := prompt_user_choice(header=header, options=options):
                for choice in user_choices:
                    func(settings_keys[choice])

    def _config_set(self, setting: str) -> None:
        if value := prompt_for_value(title=setting, prompt='Enter a new value: '):
            if self.cfg.modify(
                section='Settings',
                key=setting,
                value=value
            ):

                return

            else:
                print(f'Invalid config value format.')
                self._config_set(setting)

    def _config_reset(self, setting: str):
        self.cfg.modify(
            'Settings',
            setting,
            self.cfg.defaults[setting]
        )

    def test_mode(self) -> None:
        r"""Test mode `-qq` only works from inside the repo \...\uv_pro\uv_pro."""
        test_data = os.path.normpath(
            os.path.join(os.path.abspath(os.pardir), 'test data\\test_data1.KD')
        )
        self.args.path = test_data
        self.process()


def main() -> None:
    CLI()

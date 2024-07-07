"""
Run ``uv_pro`` from the command line.

With the ``uv_pro`` package installed, this script can be called directly from
the command line with::

    uvp process myfile.KD

The accepted commands and their options are given below. The shorthand for commands
are given in parenthesis.

Commands
========

root (rt)
---------
Usage: ``uvp rt <options>`` or ``uvp root <options>``

-clear, --clear_root_dir : flag, optional
    Clear the current root directory.
-get, --get_root_dir : flag, optional
    Print the current root directory to the console.
-set, --set_root_dir : str, optional
    Set a root directory to simplify file path entry. For instance, if
    you store all your UV-vis data files in a common folder, you can designate
    it as the root directory. Subsequently, you can omit the root directory
    portion of the path when processing data and just provide a relative path.

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

plot
----
Usage: ``uvp plot <options>``

-k2 : flag, optional
    Generate a second-order rate constant plot from exponential fit data.

select (sel)
------------
Usage: ``uvp select``

Interactively pick a .KD file from the console. The file is opened in view-
only mode. The .KD file must be located inside the root directory.

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
from uv_pro.utils.quickfig import QuickFig
from uv_pro.utils.k2_plot import K2Plot


sys.tracebacklimit = 0


class CLI:
    """
    Command line interface class.

    Attributes
    ----------
    args : :class:`argparse.Namespace`
        Parsed command-line arguments.
    config : :class:`configparser.ConfigParser`
        The current CLI settings configuration.
    """

    def __init__(self):
        self.args = self.get_args()
        self.config = Config()
        self.main()

        try:
            self.args.func()

        except AttributeError:
            pass

    def get_args(self) -> argparse.Namespace:
        """Collect all command-line args."""
        main_parser = argparse.ArgumentParser(description='Process UV-vis Data Files')
        help_msg = {
            'test_mode': 'For testing purposes.',
        }

        main_parser.add_argument(
            '-qq',
            '--test_mode',
            action='store_true',
            default=False,
            help=help_msg['test_mode']
        )

        subparsers = main_parser.add_subparsers(
            help='Subcommands'
        )

        self._process_args(subparsers)
        self._plot_args(subparsers)
        self._root_args(subparsers)
        self._select_args(subparsers)
        self._tree_args(subparsers)

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
            'baseline_lambda': 'Set the smoothness of the baseline. Default: 10.',
            'baseline_tolerance': 'Set the threshold (0-1) for outlier detection. Default: 0.1.',
            'low_signal_window': '''"narrow" or "wide". Set the width of the low signal outlier detection window.
                                     Default: "narrow"''',
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
            choices=['narrow', 'wide'],
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

    def _plot_args(self, subparsers: argparse._SubParsersAction) -> None:
        """Get args for ``plot`` subcommand."""
        help_msg = {
            'k2_plot': 'Generate a second-order rate constant plot from exponential fit data.'
        }

        plot_subparser: argparse.ArgumentParser = subparsers.add_parser(
            'plot',
            description='Generate plots.',
            help='Generate plots.'
        )

        plot_subparser.set_defaults(
            func=self.plot
        )

        plot_subparser.add_argument(
            '-k2',
            '--k2_plot',
            action='store_true',
            default=False,
            help=help_msg['k2_plot']
        )

    def _root_args(self, subparsers: argparse._SubParsersAction) -> None:
        """Get args for ``root`` subcommand."""
        help_msg = {
            'set_root_dir': '''Set a root directory where data files are located to enable \
                               typing shorter relative paths.''',
            'get_root_dir': '''Print the root directory to the console.''',
            'clear_root_dir': '''Clear the current root directory.''',
        }

        rootdir_subparser: argparse.ArgumentParser = subparsers.add_parser(
            'root',
            description='Root directory settings',
            aliases=['rt'],
            help='Root directory settings.'
        )

        rootdir_subparser.set_defaults(
            func=self.root
        )

        mutually_exclusive = rootdir_subparser.add_mutually_exclusive_group()
        mutually_exclusive.add_argument(
            '-set',
            action='store',
            default=None,
            metavar='',
            help=help_msg['set_root_dir']
        )
        mutually_exclusive.add_argument(
            '-get',
            action='store_true',
            default=False,
            help=help_msg['get_root_dir']
        )
        mutually_exclusive.add_argument(
            '-clear',
            action='store_true',
            default=False,
            help=help_msg['clear_root_dir']
        )

    def _select_args(self, subparsers: argparse._SubParsersAction) -> None:
        """Get args for ``select`` subcommand."""
        help_msg = {
            'select': 'Select a .KD file from the root directory in the terminal and open it in \
                            view-only mode.',
        }

        filepicker_subparser: argparse.ArgumentParser = subparsers.add_parser(
            'select',
            description='Select a .KD file from the root directory in the terminal \
                         and open it in view-only mode.',
            help=help_msg['select']
        )

        filepicker_subparser.set_defaults(
            func=self._handle_file_picker,
            select=True
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
            func=self._handle_file_picker,
            tree=True
        )

    def _test_args(self, subparsers: argparse._SubParsersAction) -> None:
        help_msg = {
            'test_mode': 'For testing purposes.',
        }

        test_subparser: argparse.ArgumentParser = subparsers.add_parser(
            'tree',
            description='Show the root directory file tree.',
            help=help_msg['tree']
        )

        test_subparser.set_defaults(
            func=self._handle_test_mode,
            tree=True
        )

    def main(self) -> None:
        """
        Prehandles command line args.

        Handles the args ``-qq``, ``-crd``, ``-srd``, ``-grd``, ``--tree``, and ``-fp``.
        Then handles the path before starting the processing routine
        :meth:`~uv_pro.scripts.cli.CLI.proc()`.
        """
        if self.args.test_mode is True:
            self._handle_test_mode()  # [-qq]
            return

    def _handle_test_mode(self) -> None:
        r"""Test mode `-qq` only works from inside the repo \...\uv_pro\uv_pro."""
        test_data = os.path.normpath(
            os.path.join(os.path.abspath(os.pardir), 'test data\\test_data1.KD')
        )
        self.args.path = test_data
        self.process()

    def _handle_file_picker(self) -> None:
        if root_dir := self.get_root_dir():
            if self.args.select is True:
                if file := FilePicker(root_dir, '.KD').pick_file():
                    self.args.path = file[0]
                    self.args.view = True
                    self.process()

            if self.args.tree is True:
                FilePicker(root_dir, '.KD').tree()

    def root(self):
        if self.args.set is not None:
            self.modify_root_dir(self.args.set)  # [-srd]

        if self.args.clear is True:
            self.reset_root_dir()  # [-crd]

        if self.args.get is True:
            print(f'root directory: {self.get_root_dir()}')  # [-gdr]

    def get_root_dir(self) -> str:
        root_dir = self.config.config['Settings']['root_directory']
        return root_dir if root_dir else None

    def modify_root_dir(self, directory: str) -> None:
        if os.path.exists(directory):
            self.config.modify('Settings', 'root_directory', directory)
        else:
            raise FileNotFoundError(f'The directory does not exist: {directory}')

    def reset_root_dir(self) -> None:
        self.config.reset()

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
        if self.args.slice is None and self.args.gradient_slice is None:
            return None

        elif self.args.slice:
            return {'mode': 'equal', 'slices': self.args.slice}

        elif self.args.gradient_slice:
            return {'mode': 'gradient',
                    'coeff': self.args.gradient_slice[0],
                    'expo': self.args.gradient_slice[1]
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
                uvplt.plot_2x2(dataset)

            if self.args.no_export is False:
                files_exported.extend(prompt_for_export(dataset))

            if files_exported:
                print(f'\nExport location: {os.path.dirname(self.args.path)}')
                print('Files exported:')
                [print(f'\t{file}') for file in files_exported]

        else:
            uvplt.plot_spectra(dataset, dataset.raw_spectra)

    def plot(self) -> None:
        if self.args.k2_plot is True:
            K2Plot()


def main() -> None:
    """Run the CLI."""
    CLI()

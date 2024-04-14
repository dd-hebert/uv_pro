"""
Run ``uv_pro`` from the command line.

With the ``uv_pro`` package installed, this script can be called directly from
the command line with::

    uvp -p myfile.KD

Command Line Arguments
----------------------
-p, --path : string, required
    The path to a .KD file Paths containing spaces may need to be wrapped
    in double quotes "". The script will first look for the given path inside
    the current working directory, then look at the absolute path, and lastly
    inside the root directory (if a root directory has been set).
-srd, --set_root_dir : string, optional
    Set a root directory to simplify file path entry. For instance, if
    you store all your UV-Vis data files in a common folder, you can designate
    it as the root directory. Subsequently, any path provided with ``-p`` is
    assumed to be relative to the root directory.
-grd, --get_root_dir : flag, optional
    Print the current root directory to the console.
-crd, --clear_root_dir : flag, optional
    Clear the current root directory.
-v : flag, optional
    Enable view-only mode. No data processing is performed and a plot of
    the data set is shown. Default is False.
-t, --trim : int int, optional
    Select a spectra within a given time range ``start end``. The first value
    is the time (in seconds) of the start of the time range and the second value
    is the end of the range. Default is None (no trimming).
-ot, --outlier_threshold : float, optional
    The threshold by which spectra are considered outliers. Values closer to 0
    produce more outliers. Values closer to 1 produce fewer outliers.
    The default value is 0.1.
-sl, --slice_spectra : int, optional
    The number of equally-spaced slices to plot or export. Example: if
    :attr:`uv_pro.process.Dataset.trimmed_spectra` contains 100 spectra and
    ``slice_spectra`` is 10, then every tenth spectrum will be plotted. The
    default is None, where all spectra are plotted or exported.
-gsl, --gradient_slice : float float, optional
    Slice the data in non-equally spaced slices. Give a coefficient
    and an exponent and the data slicing will be determined by the equation
    y = coefficient*x^exponent + 1, where y is the step size between slices.
    The default is None, where all spectra are plotted or exported.
-bll, --baseline_lambda : float, optional
    Set the smoothness of the baseline (for outlier detection). Higher values
    give smoother baselines. Try values between 0.001 and 10000. The
    default is 10. See :func:`pybaselines.whittaker.asls()` for more information.
-blt, --baseline_tolerance : float, optional
    Set the exit criteria for the baseline algorithm. Try values between
    0.001 and 10000. The default is 0.1. See :func:`pybaselines.whittaker.asls()`
    for more information.
-lsw, --low_signal_window : ``"narrow"`` or ``"wide"``, optional
    Set the width of the low signal outlier detection window (see
    :meth:`uv_pro.process.Dataset.find_outliers()`). Set to ``"wide"`` if low
    signals are interfering with the baseline.
--tree : flag, optional
    Print the root directory file tree to the console.
-fp, --file_picker : flag, optional
    Interactively pick a .KD file from the console. The file is opened in view-
    only mode. The .KD file must be located inside the root directory.
-ttw, --time_trace_window : int int, optional
    Set the (min, max) wavelength (in nm) range to get time traces for.
    The default is 300 1060.
-tti, --time_trace_interval : int, optional
    Set the interval (in nm) for time traces. An interval of 10 will create
    time traces from the window min to max every 10 nm. Smaller intervals
    may increase loading times. The default is 10.
-tt, --time_traces : arbitrary number of ints, optional
    A list of specific wavelengths (in nm) to create time traces for.
-ne, --no_export : flag, optional
    Use this argument to bypass the export data prompt at the end of the script.

Examples
--------
::

    # Open myfile.KD in view-only mode.
    uvp -p C:/Desktop/myfile.KD -v

    # Set a root directory.
    uvp -srd C:/Desktop
    # Now C:/Desktop can be omitted from the given path.

    # Open C:/Desktop/myfile.KD, show 10 spectra from 50 to 250 seconds
    # with outlier threshold of 0.2. Get time traces at 780 nm and 1020 nm.
    uvp -p myfile.KD -t 50 250 -ot 0.2 -sl 10 -tt 780 1020

@author: David Hebert
"""

import argparse
import os
from uv_pro.process import Dataset
import uv_pro.plots as uvplt
from uv_pro.io.export import export_csv
from uv_pro.io.export import export_time_trace
from uv_pro.utils.config import Config
from uv_pro.utils.filepicker import FilePicker


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

    def get_args(self) -> argparse.Namespace:
        parser = argparse.ArgumentParser(description='Process UV-Vis Data Files')
        help_msg = {
            'path': '''Process UV-Vis data at the given path.
                        Either a .KD file or a folder (.csv format).''',
            'set_root_dir': '''Set a root directory where data files are located so you
                           don't have to type a full path every time.''',
            'get_root_dir': '''Print the root directory to the console.''',
            'clear_root_dir': '''Clear the current root directory.''',
            'view': '''Enable view only mode (no data processing).''',
            'trim': '''2 args: trim data from __ to __.
                        Trim the data to remove spectra outside the given time range.''',
            'outlier_threshold': '''Set the threshold (0-1) for outlier detection. Default: 0.1.
                                    Values closer to 0 result in higher sensitivity (more outliers).
                                    Values closer to 1 result in lower sensitivity (fewer outliers).''',
            'slice_spectra': 'Set the number of slices to plot. Default: None (no slicing).',
            'gradient_slice': '''Use non-equal spacing when slicing data. Takes 2 args: coefficient & exponent.
                                    Default: None (no slicing).''',
            'baseline_lambda': 'Set the smoothness of the baseline. Default: 10.',
            'baseline_tolerance': 'Set the threshold (0-1) for outlier detection. Default: 0.1.',
            'low_signal_window': '''"narrow" or "wide". Set the width of the low signal outlier detection window.
                                    Default: "narrow"''',
            'fitting': 'Perform exponential fitting of specified time traces. Default: False.',
            'tree': 'Show the root directory file tree.',
            'file_picker': 'Choose a .KD file interactively from the command line instead of using -p.',
            'test_mode': 'For testing purposes.',
            'time_trace_window': '''Set the (min, max) wavelength (in nm) window for time traces during
                                    outlier detection''',
            'time_trace_interval': '''Set the interval (in nm) for time traces. An interval of 10 will create time
                                        traces from the window min to max every 10 nm. Smaller intervals will
                                        increase loading times.''',
            'time_traces': 'A list of specific wavelengths (in nm) to create time traces for.',
            'no_export': 'Skip the export data prompt at the end of the script.'}
        parser.add_argument('-p', '--path',
                            action='store',
                            default=None,
                            metavar='',
                            help=help_msg['path'])

        parser.add_argument('-srd', '--set_root_dir',
                            action='store',
                            default=None,
                            metavar='',
                            help=help_msg['set_root_dir'])

        parser.add_argument('-grd', '--get_root_dir',
                            action='store_true',
                            default=False,
                            help=help_msg['get_root_dir'])

        parser.add_argument('-crd', '--clear_root_dir',
                            action='store_true',
                            default=False,
                            help=help_msg['clear_root_dir'])

        parser.add_argument('-v', '--view',
                            action='store_true',
                            default=False,
                            help=help_msg['view'])

        parser.add_argument('-tr', '--trim',
                            action='store',
                            type=int,
                            nargs=2,
                            default=None,
                            metavar='',
                            help=help_msg['trim'])

        parser.add_argument('-ot', '--outlier_threshold',
                            action='store',
                            type=float,
                            default=0.1,
                            metavar='',
                            help=help_msg['outlier_threshold'])

        slicing_args = parser.add_mutually_exclusive_group()
        slicing_args.add_argument('-sl', '--slice_spectra',
                                  action='store',
                                  type=int,
                                  default=None,
                                  metavar='',
                                  help=help_msg['slice_spectra'])

        slicing_args.add_argument('-gsl', '--gradient_slice',
                                  action='store',
                                  type=float,
                                  nargs=2,
                                  default=None,
                                  metavar='',
                                  help=help_msg['gradient_slice'])

        parser.add_argument('-bll', '--baseline_lambda',
                            action='store',
                            type=float,
                            default=10,
                            metavar='',
                            help=help_msg['baseline_lambda'])

        parser.add_argument('-blt', '--baseline_tolerance',
                            action='store',
                            type=float,
                            default=0.1,
                            metavar='',
                            help=help_msg['baseline_tolerance'])

        parser.add_argument('-lsw', '--low_signal_window',
                            action='store',
                            default='narrow',
                            choices=['narrow', 'wide'],
                            metavar='',
                            help=help_msg['low_signal_window'])

        parser.add_argument('-fit', '--fitting',
                            action='store_true',
                            default=False,
                            help=help_msg['fitting'])

        parser.add_argument('--tree',
                            action='store_true',
                            default=False,
                            help=help_msg['tree'])

        parser.add_argument('-fp', '--file_picker',
                            action='store_true',
                            default=False,
                            help=help_msg['file_picker'])

        parser.add_argument('-qq', '--test_mode',
                            action='store_true',
                            default=False,
                            help=help_msg['test_mode'])

        parser.add_argument('-ttw', '--time_trace_window',
                            action='store',
                            type=int,
                            nargs=2,
                            default=[300, 1060],
                            metavar='',
                            help=help_msg['time_trace_window'])

        parser.add_argument('-tti', '--time_trace_interval',
                            action='store',
                            type=int,
                            default=10,
                            metavar='',
                            help=help_msg['time_trace_interval'])

        parser.add_argument('-tt', '--time_traces',
                            action='store',
                            nargs='*',
                            default=None,
                            metavar='',
                            help=help_msg['time_traces'])

        parser.add_argument('-ne', '--no_export',
                            action='store_true',
                            default=False,
                            help=help_msg['no_export'])

        return parser.parse_args()

    def get_root_dir(self) -> str:
        return self.config.config['Settings']['root_directory']

    def modify_root_dir(self, directory: str) -> None:
        self.config.modify('Settings', 'root_directory', directory)

    def reset_root_dir(self) -> None:
        self.config.reset()

    def handle_test_mode(self) -> None:
        r"""Test mode `-qq` only works from inside the repo \...\uv_pro\uv_pro."""
        test_data = os.path.normpath(
            os.path.join(os.path.abspath(os.pardir), 'test data\\test_data1.KD'))
        self.args.path = test_data
        self.proc()

    def handle_file_picker(self, root_dir: str | None) -> None:
        if self.args.file_picker is True and root_dir is not None:
            self.args.path = FilePicker(root_dir, '.KD').pick_file()
            self.args.view = True
        if self.args.tree is True:
            FilePicker(root_dir, '.KD').tree()

    def handle_path(self, root_dir: str | None) -> None:
        current_dir = os.getcwd()
        path_exists = os.path.exists(os.path.join(current_dir, self.args.path))
        if path_exists:
            self.args.path = os.path.join(current_dir, self.args.path)
        elif root_dir is not None and os.path.exists(os.path.join(root_dir, self.args.path)):
            self.args.path = os.path.join(root_dir, self.args.path)
        else:
            raise FileNotFoundError(f'No such file or directory could be found: "{self.args.path}"')

    def handle_slicing(self) -> dict | None:
        if self.args.slice_spectra is None and self.args.gradient_slice is None:
            return None
        elif self.args.slice_spectra:
            return {'mode': 'equal',
                    'slices': self.args.slice_spectra}
        elif self.args.gradient_slice:
            return {'mode': 'gradient',
                    'coefficient': self.args.gradient_slice[0],
                    'exponent': self.args.gradient_slice[1]}
        else:
            return None

    def main(self):
        """
        Prehandles command line args.

        Handles the args ``-qq``, ``-crd``, ``-srd``, ``-grd``, ``--tree``, and ``-fp``.
        Then handles the path before starting the processing routine
        :meth:`~uv_pro.scripts.cli.CLI.proc()`.

        Returns
        -------
        None.
        """
        if self.args.test_mode is True:
            self.handle_test_mode()  # [-qq]
            return

        if self.args.set_root_dir is not None:
            self.modify_root_dir(self.args.set_root_dir)  # [-srd]

        if self.args.clear_root_dir is True:
            self.reset_root_dir()  # [-crd]

        root_dir = self.get_root_dir()

        if self.args.get_root_dir is True:
            print(f'root directory: {root_dir}')  # [-gdr]

        self.handle_file_picker(root_dir)  # [-fp] [--tree]

        if self.args.path is not None:
            self.handle_path(root_dir)
            self.proc()

    def proc(self):
        """
        Process data.

        Initializes a :class:`~uv_pro.process.Dataset` with the
        given ``args``, plots the result, and prompts the user
        for exporting.

        Returns
        -------
        None.
        """
        if self.args.view is True:
            data = Dataset(self.args.path, view_only=True)
            print('\nPlotting data...')
            uvplt.plot_spectra(data, data.all_spectra)
        else:
            data = Dataset(self.args.path, trim=self.args.trim,
                           slicing=self.handle_slicing(),
                           fitting=self.args.fitting,
                           outlier_threshold=self.args.outlier_threshold,
                           baseline_lambda=self.args.baseline_lambda,
                           baseline_tolerance=self.args.baseline_tolerance,
                           low_signal_window=self.args.low_signal_window,
                           time_trace_window=self.args.time_trace_window,
                           time_trace_interval=self.args.time_trace_interval,
                           wavelengths=self.args.time_traces)

            print('\nPlotting data...')
            self._show_plots(data)

            if self.args.no_export is False:
                files_exported = self._prompt_for_export(data)
                if files_exported:
                    print(f'\nExport location: {os.path.dirname(self.args.path)}')
                    print('Files exported:')
                    [print(f'\t{file}') for file in files_exported]

    def _prompt_for_export(self, dataset: Dataset) -> list:
        files_exported = []
        options = ['Cleaned spectra']
        if dataset.specific_time_traces is not None:
            options.extend(['Time traces', 'Both'])

        prompt = f'\nExport data?\n{'=' * 12}\n'
        prompt += '\n'.join([f'({i}) {option}' for i, option in enumerate(options, start=1)])
        prompt += '\n(q) Quit\n\nChoice: '

        valid_choices = [str(i) for i in range(1, len(options) + 1)] + ['q']
        user_input = input(prompt).strip().lower()

        while user_input not in valid_choices:
            print('\nUnrecognized input.')
            user_input = input(prompt).strip().lower()

        if user_input in ['1', '3']:
            filename = export_csv(dataset, dataset.sliced_spectra)
            files_exported.append(filename)
        if user_input in ['2', '3']:
            filename = export_time_trace(dataset)
            files_exported.append(filename)

        return files_exported

    def _show_plots(self, dataset: Dataset) -> None:
        if len(dataset.all_spectra.columns) > 2:
            uvplt.plot_2x2(dataset)
        else:
            uvplt.plot_spectra(dataset, dataset.all_spectra)


def main() -> None:
    """Run the CLI."""
    CLI()

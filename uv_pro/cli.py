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

batch
-----
Usage: ``uvp batch <wavelengths> <options>``

Batch export time traces from .KD files in the current working directory.

wavelengths : arbitrary number of ints, required
    A list of time trace wavelengths (in nm) to export.
-f, --search_filters : arbitrary number of strings, optional
    A sequence of search filter strings. For example, passing ``-f copper A``
    will select .KD files which contain 'copper' OR 'A' in their filename.
    Passing no filters selects all .KD files in the current working directory.

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

config (cfg)
------------
Usage: ``uvp config <option>`` or ``uvp cfg <option>``

List, edit, reset, or delete the script configuration settings.

-edit : flag, optional
    Edit configuration settings. Will prompt the user for a selection of
    configuration settings to edit.
-delete : flag, optional
    Delete the config file and directory. The config directory will only be deleted
    if it is empty.
-list : flag, optional
    Print the current configuration settings to the console.
-reset : flag, optional
    Reset configuration settings back to their default value. Will prompt the user
    for a selection of configuration settings to reset.

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
    uvp cfg -edit

    # Select the root directory config setting and enter a file path
    C:/Desktop
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
import uv_pro._args as subcommands
from uv_pro.multiview import multiview, filter_files
from uv_pro.plots import plot_spectra, plot_2x2
from uv_pro.process import Dataset
from uv_pro.quickfig import QuickFig
from uv_pro.io.export import prompt_for_export, export_csv
from uv_pro.utils.config import Config
from uv_pro.utils.filepicker import FilePicker
from uv_pro.utils.printing import prompt_user_choice, prompt_for_value


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

        subcommands.batch(subparsers, self.batch)
        subcommands.browse(subparsers, self.browse)
        subcommands.config(subparsers, self.config)
        subcommands.multiview(subparsers, self.multiview)
        subcommands.process(subparsers, self.process)
        subcommands.tree(subparsers, self.tree)
        subcommands.test(subparsers, self.test)

        return main_parser.parse_args()

    def batch(self) -> None:
        if files := filter_files(self.args.search_filters):
            files_exported = []

            for file in files:
                dataset = Dataset(
                    path=file,
                    view_only=True
                )

                files_exported.append(
                    export_csv(
                        dataset=dataset,
                        data=dataset.get_chosen_traces(self.args.wavelengths),
                        suffix='Traces'
                    )
                )

            if files_exported:
                print('Files exported:')
                [print(f'\t{file}') for file in files_exported]

    def browse(self) -> None:
        if root_dir := self._get_root_dir():
            if file := FilePicker(root_dir, '.KD').pick_file():
                self.args.path = file[0]
                self.args.view = True
                self.process()

    def config(self) -> None:
        if self.args.edit or self.args.reset:
            if self.args.edit:
                header = 'Edit config settings'
                func = self._edit_config
            if self.args.reset:
                header = 'Reset config settings'
                func = self._reset_config

            self._config_prompt(header, func)

        elif self.args.list:
            self._print_config()

        elif self.args.delete:
            self._delete_config()

    def _config_prompt(self, header: str, func: callable) -> None:
        options = []
        settings_keys = {}
        for key, (setting, value) in enumerate(self.cfg.items('Settings'), start=1):
            options.append({'key': str(key), 'name': f'{setting}: {value}'})
            settings_keys[str(key)] = setting

        if user_choices := prompt_user_choice(header=header, options=options):
            for choice in user_choices:
                func(settings_keys[choice])

    def _delete_config(self) -> None:
        if input('Delete config file? (Y/N): ').lower() == 'y':
            delete = self.cfg.delete()
            if isinstance(delete, BaseException):
                print('Error deleting config.')
                print(delete)

            else:
                print('Config deleted.')

    def _edit_config(self, setting: str) -> None:
        if value := prompt_for_value(title=setting, prompt='Enter a new value: '):
            if self.cfg.modify(section='Settings', key=setting, value=value):
                return

            else:
                self._edit_config(setting)

    def _reset_config(self, setting: str) -> None:
        self.cfg.modify(
            'Settings',
            setting,
            self.cfg.defaults['Settings'][setting]
        )

    def _print_config(self) -> None:
        print('\nConfig settings')
        print('===============')
        for setting, value in self.cfg.items('Settings'):
            print(f'{setting}: {value}')
        print('')

    def multiview(self) -> None:
        multiview(
            search_filters=self.args.search_filters,
            filter_mode=self.args.filter_mode
        )

    def process(self) -> None:
        """
        Process data.

        Initializes a :class:`~uv_pro.process.Dataset` with the
        given ``args``, plots the result, and prompts the user
        for exporting.
        """
        self._handle_path(self._get_root_dir())

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
                plot_2x2(dataset, figsize=self._get_plot_size())

            if self.args.no_export is False:
                files_exported.extend(prompt_for_export(dataset))

            if files_exported:
                print(f'\nExport location: {os.path.dirname(self.args.path)}')
                print('Files exported:')
                [print(f'\t{file}') for file in files_exported]

        else:
            plot_spectra(dataset, dataset.raw_spectra)

    def _get_plot_size(self) -> tuple[int, int]:
        return tuple(map(int, self.cfg.get('Settings', 'plot_size').split()))

    def _get_root_dir(self) -> str:
        root_dir = self.cfg.get('Settings', 'root_directory')
        return root_dir if root_dir else None

    def tree(self) -> None:
        if root_dir := self._get_root_dir():
            FilePicker(root_dir, '.KD').tree()

    def test(self) -> None:
        r"""Test mode `-qq` only works from inside the repo \...\uv_pro\uv_pro."""
        test_data = os.path.normpath(
            os.path.join(os.path.abspath(os.pardir), 'test data\\test_data1.KD')
        )
        self.args.path = test_data
        self.process()


def main() -> None:
    CLI()

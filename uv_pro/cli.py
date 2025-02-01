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

path : str, required (unless using --list-colormaps).
    The path to a .KD file. Paths containing spaces should be wrapped in double
    quotes "". The script will first look for the file inside the current
    working directory, then look at the absolute path, and lastly
    inside the root directory (if a root directory has been set).
    If using ``--list-colormaps``, the path can be omitted.
-bs, --baseline-smoothness : float, optional
    Set the smoothness of the baseline (for outlier detection). Higher values
    give smoother baselines. Try values between 0.001 and 10000. The
    default is 10. See :func:`pybaselines.whittaker.asls()` for more information.
-bt, --baseline-tolerance : float, optional
    Set the exit criteria for the baseline algorithm. Try values between
    0.001 and 10000. The default is 0.1. See :func:`pybaselines.whittaker.asls()`
    for more information.
-c, --colormap : str, optional
    Set the colormap for the processed spectra plot. Accepts any built-in
    Matplotlib colormap name. For a full description of colormaps see:
    https://matplotlib.org/stable/tutorials/colors/colormaps.html.
    Default is 'default'.
-fx, --fit-exponential : flag, optional
    Perform exponential fitting on time traces given by ``-tt``.
-ir, --initial-rates : flag or float, optional
    Perform initial rates linear regression fitting on the time traces
    given by ``-tt``. An optional float value can be provided to specify
    the cutoff for the % change in absorbance. The default is 0.05 (5% change
    in absorbance).
--list_colormaps : flag, optional
    List available colormaps and exit (path not required).
-lw, --low-signal-window : ``narrow``, ``wide``, or ``none`` optional
    Set the width of the low signal outlier detection window (see
    :func:`~uv_pro.outliers.find_outliers()`). Set to ``wide`` if low
    signals are interfering with the baseline. Default is ``none``.
-ne, --no-export : flag, optional
    Use this argument to bypass the export data prompt at the end of the script.
-ot, --outlier-threshold : float, optional
    The threshold by which spectra are considered outliers. Values closer to 0
    produce more outliers. Values closer to 1 produce fewer outliers. A value
    >> 1 will produce no outliers. The default value is 0.1.
-qf, --quick-fig : flag, optional
    Use the quick figure generator to create and export plot figures.
-sl, --slice : int, optional
    Defines the number of equally-spaced slices to plot or export.
    For example, if :attr:`~uv_pro.dataset.Dataset.processed_spectra`
    contains 100 spectra and ``slice`` is set to 10, every tenth spectrum
    will be kept. This option allows you to reduce the number of spectra
    by selecting evenly spaced slices from the dataset.
    Default value: None (all spectra are plotted or exported)
-ssl, --specific-slice : arbitrary number of floats, optional
    Select specific slices at given times. The values should be provided
    as an arbitrary number of floats representing the time of each slice.
    This option allows you to select slices from specific positions in the dataset.
    Default value: None (all spectra are plotted or exported).
-tr, --trim : int int, optional
    Trim data outside a specified time range. The values should be provided
    as two integers representing the time range: [START, END]. This option
    allows you to exclude spectra outside the defined time window.
    Default value: None (no trimming).
-tt, --time-traces : arbitrary number of ints, optional
    A list of specific wavelengths (in nm) to create time traces for.
    These time traces are independent from the time traces created by
    :meth:`~uv_pro.dataset.Dataset.get_time_traces()`.
-ti, --time-trace-interval : int, optional
    Specifies the interval (in nm) between time traces.
    For example, setting an interval of 10 will generate time traces
    every 10 nm within the specified wavelength window (from the minimum
    to maximum wavelength). Smaller intervals can result in longer loading
    times due to the increased number of time traces. This option is used
    in the :meth:`~uv_pro.dataset.Dataset.get_time_traces()` function.
    Default value: 10 nm.
-tw, --time-trace-window : int int, optional
    Specifies the wavelength range (in nanometers) for which time traces
    will be generated. The value should be provided as a pair of integers
    representing the minimum and maximum wavelengths, e.g., '300 1060'.
    This option defines the range of wavelengths over which the time traces
    are computed by the :meth:`~uv_pro.dataset.Dataset.get_time_traces()`
    function. Default value: 300 1060 nm.
-v : flag, optional
    Enable view-only mode. No data processing is performed and a plot of
    the data set is shown. Default is False.
-vsl, --variable-slice : float float, optional
    Slice the data into non-equally spaced slices. You need to provide two
    values: a coefficient and an exponent. The data slicing will be determined
    by the equation: ``y = coefficient * x^exponent + 1``, where ``y`` is the
    step size between slices and ``x`` is the index of the slice. This option
    allows you to create slices with progressively changing intervals,
    based on the power function defined by the coefficient and exponent.
    Default value: None (all spectra are plotted or exported).

peaks
-----
Usage: ``uvp peaks <path> <options>``

Find peaks in UV-vis spectra.

path : str, required
    A path to a UV-vis data file (.KD format).
-conc, --concentration : float, optional
    The molar concentration of the species in the spectrum. Used for calculating
    molar absorptivity (ε). Default is None.
-dist, --distance : int, optional
    Set the minimum distance between peaks (in nm). Default is 10. Only used with
    ``localmax`` method.
--max_iter : int, optional
    The max number of peak finding iterations. The default is 1000. Only used with
    ``localmax`` method.
--method : str, optional
    The peak detection method: either ``localmax`` or deriv. Default is ``localmax``.
-num, --num_peaks : int, optional
    The number of peaks that should be found. Default is 0 (find all peaks).
    Only used with ``localmax`` method.
-prom, --prominance : float, optional
    Set the minimum peak prominance. Default is 0. Only used with ``localmax`` method.
-pwin, --peak_window : int int, optional
    Set the (min, max) peak detection window (in nm). Search for peaks within
    the given wavelength range. Default is None (search whole spectrum).
-swin, --smooth_window : int, optional
    Set the Savitzky-Golay smoothing window. Default is 15.
    See :func:`scipy.signal.savgol_filter`.

binmix
------
Usage: ``uvp binmix <path> <component_a> <component_b> <options>``

Estimate the relative concentrations of two species in a binary mixture.

path : str, required
    Path to a UV-vis data file (.csv format) of one or more binary mixture spectra.
component_a : str, required
    Path to a UV-vis spectrum (.csv format) of pure component "A".
component_b : str, required
    Path to a UV-vis spectrum (.csv format) of pure component "B".
-a, --molarity_a : float, optional
    Specify the concentration (in M) of pure component "A".
-b, --molarity_b : float, optional
    Specify the concentration (in M) of pure component "B".
-cols, --columns : arbitrary number of str, optional
    The columns of the binary mixture .csv file to perform fitting on.
    Provide the LABEL for each column. Default is None (fit all columns).
-icols, --index_columns : arbitrary number of ints, optional
    Specify the columns of the binary mixture .csv file to perform fitting on.
    Provide the IDX for each column. Default is None (fit all columns).
-win, --window : int int, optional
    Set the range of wavelengths (in nm) to use from the given spectra
    for fitting. Default is 300 1100.
-i, --interactive : flag, optional
    Enable interactive mode. Show an interactive matplotlib figure
    of the binary mixture fitting.

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
    .KD files which contain both 'copper' AND 'A' in their filename. Default is OR filter mode.

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
    uvp p myfile.KD -tr 50 250 -ot 0.2 -sl 10 -tt 780 1020 -fx

@author: David Hebert
"""

import sys
from random import choice
from rich import print
from uv_pro import __version__, __author__
from uv_pro.commands import get_args
from uv_pro.utils.config import Config


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
        self.args = get_args()
        self.args.config = Config()
        self.apply_config()

        try:
            self.args.func(args=self.args)

        except AttributeError:
            print(self)

    def __str__(self) -> str:
        print(*self._splash(), sep='\n')
        return ''

    def apply_config(self):
        for arg_name, value in self.args.config.broadcast():
            setattr(self.args, arg_name, value)

    def _splash(self) -> list[str]:
        colors = ['red', 'blue', 'green', 'yellow', 'cyan', 'magenta']
        random_color = choice(colors)

        splash = [
            '                                                      ',
            ' ███  ███ ███   ███         ███████   ██████  ██████  ',
            ' ███  ███ ███   ███         ███  ███ ███     ███  ███ ',
            ' ███  ███  ███ ███          ███  ███ ███     ███  ███ ',
            '  ███████   █████   ███████ ███████  ███      ██████  ',
            '                            ███                       ',
            '                            ███                       ',
        ]

        splash = [f'[{random_color}]{line}[/{random_color}]' for line in splash]
        splash.append(f'Version: {__version__}\nAuthor: {__author__}')
        splash.append('\nFor help with commands, type: uvp -h')

        return splash


def main() -> None:
    CLI()

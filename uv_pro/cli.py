"""
Run ``uv_pro`` from the command line. With the ``uv_pro`` package installed,
this script can be called directly from the command line with::

    uvp -p myfile.KD

Command Line Arguments
----------------------
-p, --path : string, required
    The path to the UV-Vis data, either a .KD file or a folder (.csv format).
    Paths containing spaces may need to be wrapped in double quotes "". The
    program will first look for the given path inside the current working
    directory, if not found it will then look at the absolute path and inside
    the root directory (if a root directory has been set).
-rd, --root_dir : string, optional
    Set a root directory for where data files are located so you don't have to
    type a full file path every time. For example, if all your UV-Vis data is
    stored inside some main directory ``C:/mydata/UV-Vis Data/``, you can
    set this as the root directory so that the path given with ``-p`` is
    assumed to be located inside the root directory.
-grd, --get_root_dir : flag, optional
    Print the current root directory to the console.
-crd, --clear_root_dir : flag, optional
    Clear the current root directory.
-v : flag, optional
    Enable view only mode. No data processing is performed and a plot of
    the data set is shown. Default is False.
-t, --trim : int int, optional
    Use ``trim`` to select a specific portion of a dataset of spectra
    ``first last``. The first value ``trim[0]`` is the index or time
    (in seconds) of the first spectrum to select. The second value
    ``trim[1]`` is the index or time (in seconds) of the last spectrum
    to import. Default is None (no trimming). Trimming uses spectrum #'s (indices).
    To trim using time (seconds), the -sec must also be given.
-ct, --cycle_time : int, optional
    Set the cycle time in seconds from the experiment. Only required if using
    time (seconds) to trim datasets imported from .csv files. The cycle time
    is automatically detected when creating a dataset from a .KD file.
    Note: only experiments with a constant cycle time are currently supported.
    The default is 1 (same as using indexes).
-ot, --outlier_threshold : float, optional
    The threshold by which spectra are considered outliers.
    Values closer to 0 result in higher sensitivity (more outliers).
    Values closer to 1 result in lower sensitivity (fewer outliers).
    The default value is 0.1.
-sl, --slice_spectra : int, optional
    The number of slices to plot or export. The default is 0, where all spectra
    are plotted or exported. Example: if :attr:`uv_pro.process.Dataset.trimmed_spectra`
    contains 100 spectra and ``slice_spectra`` is 10, then every tenth spectrum
    will be plotted.
-lam, --baseline_lambda : float, optional
    Set the smoothness of the baseline when cleaning data. Higher values
    give smoother baselines. Try values between 0.001 and 10000. The
    default is 10. See :func:`pybaselines.whittaker.asls()` for more information.
-tol, --baseline_tolerance : float, optional
    Set the exit criteria for the baseline algorithm. Try values between
    0.001 and 10000. The default is 0.1. See :func:`pybaselines.whittaker.asls()`
    for more information.
-lsw, --low_signal_window : ``"narrow"`` or ``"wide"``, optional
    Set the width of the low signal outlier detection window (see
    :meth:`uv_pro.process.Dataset.find_outliers()`). Set to ``"wide"`` to label
    points directly neighboring low signal outliers as low signal outliers also.
    Default is ``"narrow"``, meaning only low signal outliers themselves are
    labelled. Set to ``"wide"`` if low signals are interfering with the baseline.
-tr, --tree : flag, optional
    Print the ``root_directory`` file tree to the console.
-fp, --file_picker : flag, optional
    Interactively pick a .KD file from the console. The file is opened in view
    only mode.
-sec, --use_seconds : flag, optional
    Use time (seconds) when trimming data instead of spectrum # (indices).

Examples
--------
::

    # Open myfile.KD in view-only mode.
    uvp -p C:/Desktop/myfile.KD -v

    # Set a root directory.
    uvp -rd C:/Desktop
    # Now C:/Desktop can be omitted from the given path.

    # Open C:/Desktop/myfile.KD, show 10 spectra from 50 to 250 seconds
    # with outlier threshold of 0.2.
    uvp -p myfile.KD -t 50 250 -sec -ot 0.2 -sl 10

    # Open .csv files in C:/Desktop/mydatafolder, set the cycle time to 5
    # seconds and show 10 spectra from 50 to 250 seconds with outlier threshold
    # of 0.2
    uvp -p mydatafolder -t 50 250 -ct 5 -sec -ot 0.2 -sl 10

@author: David Hebert
"""

import argparse
import os
import pickle
from uv_pro.process import Dataset
import uv_pro.plots as uvplt
from uv_pro.file_io import export_csv
from simplefilepicker.filepicker import FilePicker


def handle_test_mode(args):
    r"""
    Handle the test mode functionality.

    `-qq`

    Test mode only works from inside the repo \...\uv_pro\uv_pro.

    Parameters
    ----------
    args : :class:`argparse.Namespace`
        Parsed command-line arguments.

    Returns
    -------
    None.

    """
    test_data = os.path.normpath(
        os.path.join(os.path.abspath(os.pardir), 'test data\\test_data3.KD'))
    args.path = test_data
    proc(args)


def get_root_pickle():
    """
    Return the path to the root directory pickle file.

    Returns
    -------
    str
        The path to the root directory pickle file.

    """
    parent_directory = os.path.abspath(os.path.join(__file__, os.pardir))
    root_pickle = os.path.normpath(os.path.join(parent_directory, 'root_directory.pickle'))

    return root_pickle


def save_root_directory(args, root_pickle):
    """
    Save a new root directory.

    `-rd`

    Parameters
    ----------
    args : :class:`argparse.Namespace`
        Parsed command-line arguments.
    root_pickle : str
        The path to the root directory pickle file.

    Returns
    -------
    None.

    """
    if os.path.exists(os.path.normpath(args.root_dir)):
        with open(root_pickle, 'wb') as f:
            pickle.dump(args.root_dir, f)
        print(f'New root directory: {args.root_dir}')
    else:
        print('Error: Directory does not exist.')


def handle_root_directory(args, root_pickle):
    """
    Load or clear the root directory from the root directory pickle file.

    `-grd`, `-crd`

    Parameters
    ----------
    args : :class:`argparse.Namespace`
        Parsed command-line arguments.
    root_pickle : str
        The path to the root directory pickle file.

    Returns
    -------
    str or None
        The root directory or None if the pickle file doesn't exist.

    """
    if os.path.exists(root_pickle):
        if args.clear_root_dir is True:  # [-crd]
            os.remove(root_pickle)
            root_dir = None
            print('Cleared root directory.')
        else:
            with open(root_pickle, 'rb') as f:
                root_dir = pickle.load(f)
    else:
        root_dir = None

    return root_dir


def handle_file_picker(args, root_dir):
    """
    Handle the file picker functionality.

    `-fp`

    Parameters
    ----------
    args : :class:`argparse.Namespace`
        Parsed command-line arguments.
    root_dir : str or None
        The root directory.

    Returns
    -------
    None.

    """
    if args.file_picker is True and root_dir is not None:
        args.path = FilePicker(root_dir, '.KD').pick_file()
        args.view = True

    if args.tree is True:  # [-tr]
        FilePicker(root_dir, '.KD').tree()


def handle_path(args, root_dir):
    """
    Path handling and runs the proc script.

    Parameters
    ----------
    args : :class:`argparse.Namespace`
        Parsed command-line arguments.
    root_dir : str or None
        The root directory.

    Raises
    ------
    FileNotFoundError
        Raised if the given file path cannot be found.

    Returns
    -------
    None.

    """
    if args.path is not None:
        current_dir = os.getcwd()
        path_exists = os.path.exists(os.path.join(current_dir, args.path))

        if path_exists:
            args.path = os.path.join(current_dir, args.path)
            proc(args)
        elif root_dir is not None and os.path.exists(os.path.join(root_dir, args.path)):
            args.path = os.path.join(root_dir, args.path)
            proc(args)
        else:
            raise FileNotFoundError(f'No such file or directory could be found: "{args.path}"')


def main():
    """
    Prehandles command line args.

    Handles the args ``-qq``, ``-crd``, ``-rd``, ``-grd``, ``-tr``, and ``-fp``
    before starting the processing routine :func:`~uv_pro.cli.proc()`.

    Raises
    ------
    FileNotFoundError
        Raised if the given file path cannot be found.

    Returns
    -------
    None.

    """
    args = get_args()

    # Test mode [-qq]
    if args.test_mode is True:
        handle_test_mode(args)
        return

    root_pickle = get_root_pickle()

    if args.root_dir is not None:
        # Root dir [-rd]
        save_root_directory(args, root_pickle)

    # Load or clear [-crd] root dir
    root_dir = handle_root_directory(args, root_pickle)

    # Print root directory [-gdr]
    if args.get_root_dir is True:
        print(f'root directory: {root_dir}')

    # File picker [-fp] and tree [-tr]
    handle_file_picker(args, root_dir)

    handle_path(args, root_dir)


def proc(args):
    """
    Process data.

    Initializes a :class:`~uv_pro.process.Dataset` with the
    given ``args``, plots the result, and prompts the user
    for exporting.

    Parameters
    ----------
    args : :class:`argparse.Namespace`
        Holds the arguments given at the command line.

    Returns
    -------
    None.

    """
    if args.view is True:
        data = Dataset(args.path, view_only=True)

        print('\nPlotting data...')

        uvplt.plot_spectra(data, data.all_spectra)

    else:
        data = Dataset(args.path,
                       trim=args.trim,
                       cycle_time=args.cycle_time,
                       outlier_threshold=args.outlier_threshold,
                       baseline_lambda=args.baseline_lambda,
                       baseline_tolerance=args.baseline_tolerance,
                       low_signal_window=args.low_signal_window,
                       use_seconds=args.use_seconds
                       )

        print('\nPlotting data...')

        # Show 2x2 plot if data has been cleaned
        if len(data.all_spectra) > 2:
            uvplt.plot_2x2(data, args.slice_spectra)
        else:
            uvplt.plot_spectra(data, data.all_spectra)

        def prompt_for_export():
            """
            Ask the user if they wish to export the processed data.

            Accepts a Y or N response.

            Returns
            -------
            None. Calls :func:`~uv_pro.file_io.export_csv`.

            """
            # Ask user if data should be exported
            user_input = input('\nExport cleaned spectra? (Y/N): ')

            # Check user input is Y or N.
            while user_input.lower() not in ['y', 'n']:
                user_input = input('\nY/N: ')
            if user_input.lower() == 'y':
                export_csv(data, data.trimmed_spectra, args.slice_spectra)
            elif user_input.lower() == 'n':
                pass

        prompt_for_export()


def get_args():
    """
    Create an ``ArgumentParser`` and parse command line arguments.

    Returns
    -------
    parser : :class:`argparse.ArgumentParser`

    """
    parser = argparse.ArgumentParser(description='Process UV-Vis Data Files')
    help_msg = {
        'path': '''Process UV-Vis data at the given path.
                    Either a .KD file or a folder (.csv format).''',
        'root_dir': '''Set a root directory where data files are located so you
                       don't have to type a full path every time.''',
        'get_root_dir': '''Print the root directory to the console.''',
        'clear_root_dir': '''Clear the current root directory.''',
        'view': '''Enable view only mode (no data processing).''',
        'trim': '''2 args: trim data from __ to __.
                    By default, trimming uses spectrum #'s (indices). You can trim using time (seconds)
                    by adding the -sec argument. Datasets from .csv files can only be trimmed
                    using time if a cycle time has also been provided.''',
        'cycle_time': '''Set the cycle time (in seconds) for the experiment.
                          Cycle time is automatically detected when using a .KD file.''',
        'outlier_threshold': '''Set the threshold (0-1) for outlier detection. Default: 0.1.
                                 Values closer to 0 result in higher sensitivity (more outliers).
                                 Values closer to 1 result in lower sensitivity (fewer outliers).''',
        'slice_spectra': 'Set the number of slices to plot. Default: 0 (show all).',
        'baseline_lambda': 'Set the smoothness of the baseline. Default: 10.',
        'baseline_tolerance': 'Set the threshold (0-1) for outlier detection. Default: 0.1.',
        'low_signal_window': '''"narrow" or "wide". Set the width of the low signal outlier detection window.
                                Default: "narrow"''',
        'tree': 'Show the root directory file tree.',
        'file_picker': 'Choose a .KD file interactively from the command line instead of using -p.',
        'use_seconds': "Use seconds instead of spectrum #'s when trimming data.",
        'test_mode': 'For testing purposes.'}

    parser.add_argument('-p',
                        '--path',
                        action='store',
                        default=None,
                        metavar='',
                        help=help_msg['path'])

    parser.add_argument('-rd',
                        '--root_dir',
                        action='store',
                        default=None,
                        metavar='',
                        help=help_msg['root_dir'])

    parser.add_argument('-grd',
                        '--get_root_dir',
                        action='store_true',
                        default=False,
                        help=help_msg['get_root_dir'])

    parser.add_argument('-crd',
                        '--clear_root_dir',
                        action='store_true',
                        default=False,
                        help=help_msg['clear_root_dir'])

    parser.add_argument('-v',
                        '--view',
                        action='store_true',
                        default=False,
                        help=help_msg['view'])

    parser.add_argument('-t',
                        '--trim',
                        action='store',
                        type=int,
                        nargs=2,
                        default=None,
                        metavar='',
                        help=help_msg['trim'])

    parser.add_argument('-ct',
                        '--cycle_time',
                        action='store',
                        type=int,
                        default=None,
                        metavar='',
                        help=help_msg['cycle_time'])

    parser.add_argument('-ot',
                        '--outlier_threshold',
                        action='store',
                        type=float,
                        default=0.1,
                        metavar='',
                        help=help_msg['outlier_threshold'])

    parser.add_argument('-sl',
                        '--slice_spectra',
                        action='store',
                        type=int,
                        default=0,
                        metavar='',
                        help=help_msg['slice_spectra'])

    parser.add_argument('-lam',
                        '--baseline_lambda',
                        action='store',
                        type=float,
                        default=10,
                        metavar='',
                        help=help_msg['baseline_lambda'])

    parser.add_argument('-tol',
                        '--baseline_tolerance',
                        action='store',
                        type=float,
                        default=0.1,
                        metavar='',
                        help=help_msg['baseline_tolerance'])

    parser.add_argument('-lsw',
                        '--low_signal_window',
                        action='store',
                        default='narrow',
                        metavar='',
                        help=help_msg['low_signal_window'])

    parser.add_argument('-tr',
                        '--tree',
                        action='store_true',
                        default=False,
                        help=help_msg['tree'])

    parser.add_argument('-fp',
                        '--file_picker',
                        action='store_true',
                        default=False,
                        help=help_msg['file_picker'])

    parser.add_argument('-sec',
                        '--use_seconds',
                        action='store_true',
                        default=False,
                        help=help_msg['use_seconds'])

    parser.add_argument('-qq',
                        '--test_mode',
                        action='store_true',
                        default=False,
                        help=help_msg['test_mode'])

    return parser.parse_args()

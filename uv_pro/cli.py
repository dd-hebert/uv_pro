'''
Command Line Interface
======================
A script for running ``uv_pro`` from the command line. Serves as a command
line entry point. With the ``uv_pro`` package installed, this script can be
called directly from the command line with uvp::

    uvp -p "myfile.KD"

Command Line Arguments
----------------------
-p, --path : string, required
    The path to the UV-Vis data, either a .KD file or a folder (.csv format).
    Should be wrapped in double quotes "".
-v : flag, optional
    Enable view only mode. No data processing is performed and a plot of
    the data set is shown. Default is False.
-t, --trim : int int, optional
    Use ``trim`` to select a specific portion of a dataset of spectra
    ``first last``. The first value ``trim[0]`` is the index or time
    (in seconds) of the first spectrum to select. The second value
    ``trim[1]`` is the index or time (in seconds) of the last spectrum
    to import. Default is None (no trimming).
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

Examples
--------
::

    # Open myfile.KD in view-only mode.
    uvp -p "C:\\Desktop\\myfile.KD" -v

    # Open myfile.KD, show 10 spectra from 50 to 250 seconds with outlier
    # threshold of 0.2.
    uvp -p "C:\\Desktop\\myfile.KD" -t 50 250 -ot 0.2 -sl 10

    # Open .csv files in mydatafolder, set the cycle time to 5 seconds and
    # show 10 spectra from 50 to 250 seconds with outlier threshold of 0.2
    uvp -p "C:\\Desktop\\mydatafolder" -t 50 250 -ct 5 -ot 0.2 -sl 10

'''

import argparse
import os
import pickle
from uv_pro.process import Dataset
import uv_pro.plots as uvplt
from uv_pro.file_io import export_csv


def main():
    '''
    Handles the args ``-qq``, ``-r``, and ``-grd`` before starting the
    processing routine :func:`~uv_pro.cli.proc()`.

    '''

    __args = get_args()

    # Testing mode [-qq]
    if __args.test_mode is True:
        test_data = r'C:\Users\David\Python\uv_pro\test data\test_data.KD'
        __args.path = test_data
        proc(__args)
    else:
        # Save new root directory [-r]
        if __args.root_dir is not None:
            if os.path.exists(os.path.normpath(__args.root_dir)):
                with open('pickled_root', 'wb') as f:
                    pickle.dump(__args.root_dir, f)
                print(f'New root directory: {__args.root_dir}')
            else:
                print('Error: Directory does not exist.')

        # Load root directory
        if os.path.exists('pickled_root'):
            with open('pickled_root', 'rb') as f:
                __root = pickle.load(f)
        else:
            __root = None

        # Print root directory [-gdr]
        if __args.get_root_dir is True:
            print(f'root directory: {__root}')

        # Run proc script
        if __args.path is not None:
            if __root is not None:
                __args.path = os.path.join(__root, __args.path)
                proc(__args)
            else:
                proc(__args)


def proc(__args):
    '''
    Process data. Initializes a :class:`~uv_pro.process.Dataset` with the
    given ``__args``, plots the result, and prompts the user
    for exporting.

    Parameters
    ----------
    __args : :class:`argparse.Namespace`
        Holds the arguments given at the command line.

    Returns
    -------
    None.

    '''

    if __args.view is True:
        data = Dataset(__args.path, view_only=True)

        print('\nPlotting data...')

        uvplt.plot_spectra(data, data.all_spectra)

    else:
        data = Dataset(__args.path,
                       trim=__args.trim,
                       cycle_time=__args.cycle_time,
                       outlier_threshold=__args.outlier_threshold,
                       baseline_lambda=__args.baseline_lambda,
                       baseline_tolerance=__args.baseline_tolerance,
                       low_signal_window=__args.low_signal_window
                       )

        print('\nPlotting data...')

        # Show 2x2 plot if data has been cleaned
        if len(data.all_spectra) > 2:
            uvplt.plot_2x2(data, __args.slice_spectra)
        else:
            uvplt.plot_spectra(data, data.all_spectra)

        def prompt_for_export():
            '''
            Ask the user if they wish to export the processed data. Accepts
            a Y or N response.

            Returns
            -------
            None. Calls :func:`~uv_pro.file_io.export_csv`.

            '''

            # Ask user if data should be exported
            user_input = input('\nExport cleaned spectra? (Y/N): ')

            # Check user input is Y or N.
            while user_input.lower() not in ['y', 'n']:
                user_input = input('\nY/N: ')
            if user_input.lower() == 'y':
                export_csv(data, data.cleaned_spectra, __args.slice_spectra)
            elif user_input.lower() == 'n':
                pass

        prompt_for_export()


def get_args():
    '''
    Setup ``ArgumentParser`` and parse command line arguments.

    Returns
    -------
    parser : :class:`argparse.ArgumentParser`

    '''

    parser = argparse.ArgumentParser(description='Process UV-Vis Data Files')
    help_msg = {
        'path': '''Process UV-Vis data at the given path.
                    Either a .KD file or a folder (.csv format).''',
        'root_dir': '''Set the root directory to scan for .KD files.''',
        'get_root_dir': '''Print the root directory to the console.''',
        'view': '''View only mode (no data processing).''',
        'trim': '''2 args: trim data from __ to __.
                    Uses indices if no cycle time provided (.csv).
                    Uses time (seconds) is a cycle time is provided.''',
        'cycle_time': '''Set the cycle time (in seconds) for the experiment.
                          Cycle time is automatically detected when using a .KD file.''',
        'outlier_threshold':  '''Set the threshold (0-1) for outlier detection. Default: 0.1.
                                 Values closer to 0 result in higher sensitivity (more outliers).
                                 Values closer to 1 result in lower sensitivity (fewer outliers).''',
        'slice_spectra': 'Set the number of spectra to show. Default: 0 (show all).',
        'baseline_lambda': 'Set the smoothness of the baseline. Default: 10.',
        'baseline_tolerance': 'Set the threshold (0-1) for outlier detection. Default: 0.1.',
        'low_signal_window': 'Set the width of the low signal outlier detection window.',
        'test_mode': 'For testing purposes.'
                }

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

    parser.add_argument('-qq',
                        '--test_mode',
                        action='store_true',
                        default=False,
                        help=help_msg['test_mode'])

    return parser.parse_args()

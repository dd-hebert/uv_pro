"""
View multiple .KD files from the command line.

Navigate to a directory containing .KD files and run the command::

    uvp mv -f some search filters

The script will open .KD files which contain any of the supplied search filters
in ``view_only`` mode.

The default search behavior is an `OR` search. You can supply the ``-a`` or
``--and-filter`` argument to perform an `AND` search::

    uvp mv -f some search filters -a

Now only .KD files with contain all of the search filters in their name will be
opened.

The ``-f`` filtering argument can be omitted to open all .KD files in the current working
directory.

@author: David
"""

import argparse
import glob
import subprocess
from concurrent.futures import ThreadPoolExecutor

from uv_pro.commands import argument, command

HELP = {
    'filters': 'An arbitrary number of search filters.',
    'and-filter': '``and`` filter mode.',
    'or-filter': '``or`` filter mode.',
}
ARGS = [
    argument(
        '-f',
        '--filters',
        action='store',
        nargs='*',
        default='*',
        metavar='',
        help=HELP['filters'],
    ),
    argument(
        '-a',
        '--and-filter',
        dest='filter_mode',
        action='store_const',
        default='or',
        const='and',
        help=HELP['and-filter'],
    ),
]


@command(args=ARGS, aliases=['mv'])
def multiview(args: argparse.Namespace) -> None:
    """
    Open multilple .KD files in parallel (view-only mode).

    Parameters
    ----------
    search_filters : list[str]
        A list of search filter strings.
    mode : str, optional
        The filter mode, can be 'and' or 'or'. The default is 'or'.

    Parser Info
    -----------
    *aliases : mv
    *desc : Search for multiple UV-vis data files in the current working directory \
        and open them view-only mode.
    *help : Open multiple UV-vis data files in view-only mode.
    """
    _run_uvp_parallel(filter_files(args.search_filters, mode=args.filter_mode))


def filter_files(search_filters: list[str], mode: str = 'or') -> set[str]:
    """
    Filter a list of files into a set.

    Parameters
    ----------
    search_filters : list[str]
        A list of search filter strings. Default is '*'.
    mode : str, optional
        The filter mode, can be 'and' or 'or'. The default is 'or'.

    Returns
    -------
    files : set[str]
        The filtered files.
    """
    search_patterns = [f'*{pattern}*.KD' for pattern in search_filters]

    if mode == 'and':
        files = set(glob.glob(search_patterns[0]))
        for pattern in search_patterns[1:]:
            files &= set(glob.glob(pattern))
    else:
        files = set(
            [matches for pattern in search_patterns for matches in glob.glob(pattern)]
        )

    if len(files) == 0:
        print('Error: No .KD files found with the specified filter(s).')
        return

    return files


def _run_uvp_subprocess(file: str) -> None:
    """
    Run the uvp script in parallel.

    Parameters
    ----------
    file : str
        A file name.
    """
    try:
        subprocess.run(
            ['uvp', 'process', file, '-v'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
        )

    except Exception as e:
        print(f'An error occurred while processing the file: {str(e)}')


def _run_uvp_parallel(files: set[str]) -> None:
    """
    Run the ``uvp`` script on a list of files in parallel using ThreadPoolExecutor.

    Parameters
    ----------
    files : set[str]
        A set of file names.
    """
    try:
        with ThreadPoolExecutor(max_workers=50) as executor:
            executor.map(_run_uvp_subprocess, files)

    except TypeError:
        pass

    except Exception as e:
        print(f'An error occurred while processing the files: {str(e)}')

"""
View multiple .KD files from the command line.

Navigate to a directory containing .KD files and run the command::

    uvp mv -f some search filters

The script will open .KD files which contain any of the supplied search filters
in ``view_only`` mode.

The default search behavior is an `OR` search. You can use supply the ``-a`` or
``--and_filter`` argument to perform an `AND` search::

    uvp mv -f some search filters -a

Now only .KD files with contain all of the search filters in their name will be
opened.

If no search filters are provided, then all .KD files in the current working
directory will be opened.

@author: David
"""

import os
import glob
import subprocess
from concurrent.futures import ThreadPoolExecutor


def multiview(search_filters: list[str], filter_mode: str = 'or') -> None:
    """
    Get command line args and run :func:`~uv_pro.scripts.multiview.multiview()`.

    Parameters
    ----------
    search_filters : list[str]
        A list of search filter strings.
    mode : str, optional
        The filter mode, can be 'and' or 'or'. The default is 'or'.
    """
    _run_uvp_parallel(filter_files(search_filters, mode=filter_mode))


def filter_files(search_filters: list[str], mode: str = 'or') -> set[str]:
    """
    Filter a list of files into a set.

    Parameters
    ----------
    search_filters : list[str]
        A list of search filter strings.
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
        files = set([matches for pattern in search_patterns for matches in glob.glob(pattern)])

    if len(files) == 0:
        print("Error: No files found with the specified filter(s).")
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
            stderr=subprocess.STDOUT
        )

    except Exception as e:
        print(f"An error occurred while processing the file: {str(e)}")


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
        print(f"An error occurred while processing the files: {str(e)}")

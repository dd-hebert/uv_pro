# -*- coding: utf-8 -*-
"""
Import data from .csv.

Contains methods to import UV-Vis data from .csv files.

@author: David Hebert
"""
import os
import pandas as pd


def import_csv(path):
    """
    Read .csv files at ``path``.

    Read .csv files and import spectra found in ``path`` into a list of
    :class:`pandas.DataFrame` objects.

    Parameters
    ----------
    path : string
        The path to a folder containing UV-Vis data in .csv format.

    Raises
    ------
    Exception
        Raised if ``path`` is empty.

    Returns
    -------
    spectra : list of :class:`pandas.DataFrame` objects.
        Returns a list of :class:`pandas.DataFrame` objects containing all the
        spectra found in ``path``.

    """
    spectra = []
    file_list = []
    directory = os.listdir(os.path.normpath(path))

    for entry in directory:
        if os.path.isfile(os.path.join(os.path.normpath(path), entry)) and entry.endswith('.csv'):
            file_list.append(entry)

    if len(file_list) == 0:
        raise Exception('Empty file path, no files found.')

    start_file = file_list.index(file_list[0])
    end_file = file_list.index(file_list[-1])

    print('Importing .csv files...')

    # First try UTF-16 encoding, which is how .csv exported from the Chemstation
    # software are encoded.
    try:
        # Import files within specified time range.
        for n in range(start_file, end_file + 1):
            spectra.append(pd.read_csv(path + '\\' + file_list[n],
                                       encoding='utf-16',
                                       na_filter=False))
    except UnicodeError:
        # Then try UTF-8 encoding, which is how .csv created by this script
        # are encoded.
        try:
            for n in range(start_file, end_file + 1):
                spectra.append(pd.read_csv(path + '\\' + file_list[n],
                                           encoding='utf-8',
                                           na_filter=False))
        except UnicodeError:
            print('Error importing .csv files.',
                  'Only UTF-16 and UTF-8 encodings are supported.')

    return spectra

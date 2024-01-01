# -*- coding: utf-8 -*-
"""
Export data.

Contains functions for exporting UV-Vis data to .csv format.

@author: David Hebert
"""
import os


def _make_output_dir(dataset):
    # If path is a file, create output folder in {dataset.path} named
    # {dataset.name} without file extension.
    if os.path.isfile(dataset.path) is True:
        output_dir = os.path.splitext(dataset.path)[0]
        n = 1
        # If a folder named {dataset.name} exists, add a number after.
        while os.path.exists(output_dir) is True:
            output_dir = os.path.splitext(dataset.path)[0] + f' ({n})'
            n += 1

    # Otherwise create folder in {dataset.path} named {dataset.name}.
    else:
        output_dir = os.path.join(dataset.path, f'{dataset.name}')
        n = 1
        # If a folder named {dataset.name} already exists, add a number after.
        while os.path.exists(output_dir) is True:
            output_dir = os.path.join(dataset.path, f'{dataset.name}') + f' ({n})'
            n += 1

    os.mkdir(output_dir)
    return output_dir


def _get_unique_filename(output_dir, base_filename):
    """If a file named base_filename exists, add a number after."""
    n = 1
    unique_filename = base_filename
    while os.path.exists(f'{os.path.join(output_dir, unique_filename)}.csv'):
        unique_filename = base_filename + f' ({n})'
        n += 1
    return unique_filename


def export_csv(dataset, spectra):
    """
    Export spectra to .csv.

    Spectra are exported to the same directory as the parent
    .KD file.

    Parameters
    ----------
    dataset : :class:`~uv_pro.process.Dataset`
        The :class:`~uv_pro.process.Dataset` to be exported.
    spectra : :class:`pandas.DataFrame`
        The spectra to be exported. A :class:`pandas.DataFrame`
        such as ``dataset.all_spectra`` or ``dataset.trimmed_spectra``.

    Returns
    -------
    str
        The file name of the exported .csv file.

    """
    output_dir = os.path.dirname(dataset.path)
    base_filename = os.path.splitext(dataset.name)[0]
    filename = _get_unique_filename(output_dir, base_filename)
    spectra.to_csv(os.path.join(output_dir, f'{filename}.csv'), index=True)
    return f'{filename}.csv'


def export_time_trace(dataset):
    """
    Export time traces to .csv.

    Time traces are exported to the same directory as the parent
    .KD file.

    Parameters
    ----------
    dataset : :class:`~uv_pro.process.Dataset`
        The :class:`~uv_pro.process.Dataset` with time traces to be exported.

    Returns
    -------
    str
        The file name of the exported .csv file.

    """
    output_dir = os.path.dirname(dataset.path)
    base_filename = f'{os.path.splitext(dataset.name)[0]} Traces'
    filename = _get_unique_filename(output_dir, base_filename)
    time_traces = dataset.specific_time_traces
    time_traces.to_csv(os.path.join(output_dir, f'{filename}.csv'),
                       index=True)
    return f'{filename}.csv'

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


def export_csv(dataset, spectra, num_spectra=0):
    """
    Export ``spectra`` as .csv format.

    ``spectra`` are exported to a folder named ``dataset.name`` inside
    ``dataset.path``.

    Parameters
    ----------
    dataset : :class:`~uv_pro.process.Dataset`
        The :class:`~uv_pro.process.Dataset` to be exported.
    spectra : list of :class:`pandas.DataFrame` objects
        The spectra to be exported. A list of :class:`pandas.DataFrame`
        objects, such as ``dataset.all_spectra`` or ``dataset.trimmed_spectra``.
    num_spectra : int, optional
        The number of slices to export. The default is 0, where all spectra
        are exported. Example: if ``spectra`` contains 200 spectra and
        ``num_spectra`` is 10, then every 20th spectrum will be exported.

    Returns
    -------
    None.

    """
    output_dir = _make_output_dir(dataset)

    # Get number of digits to use for leading zeros.
    digits = len(str(len(spectra)))

    # Export all spectra, name files by index in given list of spectra
    if num_spectra == 0:
        for i, spectrum in enumerate(spectra):
            spectrum.to_csv(os.path.join(output_dir, f'{str(i+1).zfill(digits)}.csv'), index=False)

    # Export chosen spectra, name files by index in given list of spectra
    else:
        if int(num_spectra) > len(spectra):
            num_spectra = len(spectra)

        for i in range(0, len(spectra), len(spectra) // int(num_spectra)):
            spectra[i].to_csv(os.path.join(output_dir, f'{str(i+1).zfill(digits)}.csv'), index=False)

    print(f'Finished export: {output_dir}', end='\n')


def export_time_trace(dataset):
    """
    Export time traces to .csv format.

    Time traces are exported to a folder named ``dataset.name`` inside
    ``dataset.path``.

    Parameters
    ----------
    dataset : :class:`~uv_pro.process.Dataset`
        The :class:`~uv_pro.process.Dataset` with time traces to be exported.

    Returns
    -------
    None.

    """
    output_dir = _make_output_dir(dataset)
    time_traces = dataset.specific_time_traces

    for wavelength in time_traces.columns:
        time_traces[wavelength].to_csv(os.path.join(output_dir, f'{wavelength}.csv'),
                                       index=True,
                                       index_label='time (s)')

    print(f'Finished export: {output_dir}', end='\n')

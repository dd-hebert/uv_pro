'''
Contains methods importing and exporting UV-Vis data files. Supports .csv files
and Agilent 845x UV-Vis Chemstation binary files (.KD).

'''

import os
import struct
import pandas as pd


def from_csv(path):
    '''
    Reads .csv files and imports spectra found in ``path``.

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

    '''

    spectra = []
    file_list = []
    directory = os.listdir(os.path.normpath(path))

    # Ignore files that aren't .csv extension.
    for entry in directory:
        if os.path.isfile(os.path.join(os.path.normpath(path), entry)) and entry.endswith('.csv'):
            file_list.append(entry)

    if len(file_list) == 0:
        raise Exception('Empty file path, no files found.')

    # Get index of first and last spectrum from list of files in path.
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


def from_kd(path):
    '''
    Reads a .KD file and extracts the spectra into a list of :class:`pandas.DataFrame`
    objects. Also reads the cycle time from the .KD file.

    Important
    ---------
        Only experiments with a constant cycle time are currently supported.

    Parameters
    ----------
    path : string
        The file path to a .KD file.

    Returns
    -------
    spectra, cycle_time : list of :class:`pandas.DataFrame` objects, int
        Returns a list of :class:`pandas.DataFrame` objects containing all the
        spectra in the .KD file and the cycle time (in seconds) for the experiment.

    '''

    spectrum_locations = [0]
    spectra = []
    wavelength = list(range(190, 1101))  # Spectrometer records from 190-1100 nm

    # Data is 8 hex characters per wavelength long.
    absorbance_table_length = (wavelength[-1] - wavelength[0]) * 8 + 8

    absorbance_data_string = b'\x28\x00\x41\x00\x55\x00\x29\x00'
    cycle_time_string = (
        b'\x43\x00\x79\x00\x63\x00\x6C\x00'
        b'\x65\x00\x54\x00\x69\x00\x6D\x00'
        b'\x65\x00\x77\x00\x00\x00\x00\x00'
        )

    print('Reading .KD file...')

    with open(path, 'rb') as kd_file:
        file_bytes = kd_file.read()  # Bytes from .KD binary file

    # Find the string of bytes that precedes absorbance data in the binary file.
    finder = file_bytes.find(absorbance_data_string, spectrum_locations[-1])

    # Extract absorbance data.
    while spectrum_locations[-1] != -1:
        spectrum_locations.append(finder)
        absorbance = []
        # Data starts 17 hex characters after the {absorbance_data_string}.
        data_start = spectrum_locations[-1] + 17
        data_end = data_start + absorbance_table_length

        for i in range(data_start, data_end, 8):
            # Little endian mode
            absorbance.append(struct.unpack('<d', (file_bytes[i:i + 8]))[0])

        spectra.append(pd.DataFrame({'Wavelength (nm)': wavelength,
                                     'Absorbance (AU)': absorbance}))

        # Find next spectrum, start looking from the end of the current spectrum.
        finder = file_bytes.find(absorbance_data_string, data_end)

    spectra.pop(-1)  # Remove weird last spectrum

    # Find the string of bytes that precedes the cycle time in the binary file.
    # Cycle time is 24 bytes after the {cycle_time_string}.
    finder = file_bytes.find(cycle_time_string) + 24
    cycle_time = int(struct.unpack('<d', (file_bytes[finder:finder + 8]))[0])
    print(f'Setting cycle time set to: {cycle_time} seconds...')

    return spectra, cycle_time


def export_csv(dataset, spectra, num_spectra=0):
    '''
    Exports ``spectra`` as .csv to a folder named ``dataset.name`` inside
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

    '''

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

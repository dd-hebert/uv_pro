# -*- coding: utf-8 -*-
"""
Import .KD files.

A script for parsing .KD files and extracting UV-Vis data
and experimental parameters.

@author: David Hebert
"""
import struct
import os
import pandas as pd


class KDFile:
    """
    A KDFile object. Contains methods to parse .KD files.

    Attributes
    ----------
    absorbance_data_header : dict
        The hex string header and spacing that precedes the absorbance data in
        the .KD file.
    spectrum_time_header : dict
        The hex string header and spacing that precedes the spectrum times in
        the .KD file.
    cycle_time_header : dict
        The hex string header and spacing that precedes the cycle time in
        the .KD file.
    absorbance_table_length : int
        The length (in bytes) of the absorbance data table based on the range
        of wavelengths captured by the detector.
    file_bytes : bytes
        The bytes read from the .KD file.
    spectra : :class:`pandas.DataFrame`
        All of the raw spectra in the :class:`Dataset`.
    spectra_times : class:`pandas.Series`
        The time values that each spectrum was captured.
    cycle_time : int
        The cycle time value (in seconds) for the experiment.
    """

    absorbance_data_header = {
        'header': b'\x28\x00\x41\x00\x55\x00\x29\x00',
        'spacing': 17}
    spectrum_time_header = {
        'header': b'\x52\x00\x65\x00\x6C\x00\x54'
        b'\x00\x69\x00\x6D\x00\x65\x00',
        'spacing': 20}
    cycle_time_header = {
        'header': b'\x43\x00\x79\x00\x63\x00\x6C\x00'
        b'\x65\x00\x54\x00\x69\x00\x6D\x00'
        b'\x65\x00\x77\x00\x00\x00\x00\x00',
        'spacing': 24}

    def __init__(self, path, spectrometer_range=(190, 1100)):
        """
        Create a KDFile object and parse a .KD file at ``path``.

        Read a .KD file and extract the spectra into a :class:`pandas.DataFrame`.
        Also reads the spectrum times and cycle time from the .KD file.

        Important
        ---------
            Only experiments with a constant cycle time are currently supported.

        Parameters
        ----------
        path : string
            The file path to a .KD file.
        spectrometer_range : tuple-like
            The minimum and maximum wavelengths captured by the spectrometer.
        """
        self.path = path
        self.wavelength_range = list(range(spectrometer_range[0], spectrometer_range[1]))
        self.absorbance_table_length = self._get_absorbance_table_length()
        self.file_bytes = self._read_binary()
        self.spectra, self.spectra_times, self.cycle_time = self.parse_kd()

    def _get_absorbance_table_length(self):
        """8 hex chars per wavelength."""
        absorbance_table_length = (self.wavelength_range[-1] - self.wavelength_range[0]) * 8 + 8
        return absorbance_table_length

    def _read_binary(self):
        print(f'Reading .KD file {os.path.basename(self.path)}...')
        with open(self.path, 'rb') as kd_file:
            file_bytes = kd_file.read()
        return file_bytes

    def _extract_data(self, header, parse_func):
        data_list = []
        position = 0
        data_header = header['header']
        spacing = header['spacing']

        while True:
            header_location = self.file_bytes.find(data_header, position)
            if header_location == -1:
                break

            data_start = header_location + spacing
            data = parse_func(data_start)
            data_list.append(data)
            position = data_start + self.absorbance_table_length

        if data_list == []:
            return None

        return data_list

    def _parse_spectra(self, data_start):
        data_end = data_start + self.absorbance_table_length
        absorbance_data = self.file_bytes[data_start:data_end]
        absorbance_values = [value for value, in struct.iter_unpack('<d', absorbance_data)]
        return pd.Series(absorbance_values, index=self.wavelength_range, name='Absorbance (AU)')

    def _parse_spectratimes(self, data_start):
        time_value = float(struct.unpack_from('<d', self.file_bytes, data_start)[0])
        return time_value

    def _parse_cycletime(self, data_start):
        cycle_time = int(struct.unpack_from('<d', self.file_bytes, data_start)[0])
        return cycle_time

    def _spectra_dataframe(self, list_of_spectra):
        df = pd.concat(list_of_spectra, axis=1)
        idx = pd.Index(self.wavelength_range, name='Wavelength (nm)')
        df.index = idx
        return df

    def parse_kd(self):
        """
        Parse a .KD file and extract data.

        Raises
        ------
        Exception
            Raises an exception if no spectra can be found.

        Returns
        -------
        spectra : :class:`pandas.DataFrame`
            The raw spectra contained in the .KD file.
        spectra_times : :class:`pandas.Series`
            The time values that each spectrum was captured.
        cycle_time : int
            The cycle time (in seconds) for the UV-Vis experiment.

        """
        spectra = self._handle_spectra()
        spectra_times = self._handle_spectratimes()
        cycle_time = self._handle_cycletime()
        print(f'Spectra found: {len(spectra.columns)}', end='\n')
        print(f'Cycle time (s): {cycle_time}', end='\n')
        return spectra, spectra_times, cycle_time

    def _handle_spectra(self):
        list_of_spectra = self._extract_data(KDFile.absorbance_data_header, self._parse_spectra)
        if list_of_spectra is None:
            raise Exception('Error parsing file. No spectra found.')
        return self._spectra_dataframe(list_of_spectra)

    def _handle_spectratimes(self):
        return pd.Series(
            self._extract_data(KDFile.spectrum_time_header, self._parse_spectratimes),
            name='Time (s)')

    def _handle_cycletime(self):
        cycle_time = int(self._extract_data(KDFile.cycle_time_header, self._parse_cycletime)[0])
        if cycle_time is None:
            cycle_time = 1
        return cycle_time
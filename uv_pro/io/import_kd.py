"""
Import .KD files.

A script for parsing .KD files and extracting UV-vis data
and experimental parameters.

@author: David Hebert
"""
import struct
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
        All of the raw spectra found in the .KD file.
    spectra_times : :class:`pandas.Series`
        The time values that each spectrum was captured.
    cycle_time : int
        The cycle time value (in seconds) for the experiment.
    """

    absorbance_data_header = {
        'header': b'\x28\x00\x41\x00\x55\x00\x29\x00',
        'spacing': 17
    }
    spectrum_time_header = {
        'header': b'\x52\x00\x65\x00\x6C\x00\x54'
        b'\x00\x69\x00\x6D\x00\x65\x00',
        'spacing': 20
    }
    cycle_time_header = {
        'header': b'\x43\x00\x79\x00\x63\x00\x6C\x00'
        b'\x65\x00\x54\x00\x69\x00\x6D\x00'
        b'\x65\x00\x77\x00\x00\x00\x00\x00',
        'spacing': 24
    }

    def __init__(self, path: str, spectrometer_range: tuple[int, int] = (190, 1100)) -> None:
        """
        Initialize a KDFile object and parse a .KD file at ``path``.

        Read a .KD file and extract the spectra into a :class:`pandas.DataFrame`.
        Also reads the spectrum times and cycle time from the .KD file.

        Important
        ---------
        Only experiments with a constant cycle time are currently supported.

        Parameters
        ----------
        path : str
            The file path to a .KD file.
        spectrometer_range : tuple[int, int]
            The minimum and maximum wavelengths captured by the spectrometer.
        """
        self.path = path
        self.wavelength_range = list(range(spectrometer_range[0], spectrometer_range[1]))
        self.absorbance_table_length = self._get_absorbance_table_length()
        self.file_bytes = self._read_binary()
        self.spectra, self.spectra_times, self.cycle_time = self.parse_kd()

    def _get_absorbance_table_length(self) -> int:
        """8 hex chars per wavelength."""
        absorbance_table_length = (self.wavelength_range[-1] - self.wavelength_range[0]) * 8 + 8
        return absorbance_table_length

    def _read_binary(self) -> bytes:
        with open(self.path, 'rb') as kd_file:
            file_bytes = kd_file.read()
        return file_bytes

    def parse_kd(self) -> tuple[pd.DataFrame, pd.Series, int]:
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
            The cycle time (in seconds) for the UV-vis experiment.
        """
        cycle_time = self._handle_cycletime()
        spectra_times = self._handle_spectratimes()
        spectra = self._handle_spectra(spectra_times)
        return spectra, spectra_times, cycle_time

    def _handle_spectra(self, spectra_times: pd.Series) -> pd.DataFrame:
        list_of_spectra = self._extract_data(KDFile.absorbance_data_header, self._parse_spectra)
        if list_of_spectra is None:
            raise Exception('Error parsing file. No spectra found.')
        return self._spectra_dataframe(list_of_spectra, spectra_times)

    def _handle_spectratimes(self) -> pd.Series:
        spectra_times = self._extract_data(KDFile.spectrum_time_header, self._parse_spectratimes)
        if spectra_times is None:
            raise Exception('Error parsing file. No spectra times found.')
        return pd.Series(spectra_times, name='Time (s)')

    def _handle_cycletime(self) -> int:
        try:
            return int(self._extract_data(KDFile.cycle_time_header, self._parse_cycletime)[0])
        except TypeError:
            return None

    def _extract_data(self, header: dict, parse_func: callable) -> list:
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

        return data_list if data_list else None

    def _parse_spectra(self, data_start: int) -> pd.Series:
        data_end = data_start + self.absorbance_table_length
        absorbance_data = self.file_bytes[data_start:data_end]
        absorbance_values = [value for value, in struct.iter_unpack('<d', absorbance_data)]
        return pd.Series(absorbance_values, index=self.wavelength_range)

    def _parse_spectratimes(self, data_start: int) -> float:
        return float(struct.unpack_from('<d', self.file_bytes, data_start)[0])

    def _parse_cycletime(self, data_start: int) -> int:
        return int(struct.unpack_from('<d', self.file_bytes, data_start)[0])

    def _spectra_dataframe(self, spectra: list, spectra_times: pd.Series) -> pd.DataFrame:
        df = pd.concat(spectra, axis=1)
        df.index = pd.Index(self.wavelength_range, name='Wavelength (nm)')
        df.columns = spectra_times
        return df

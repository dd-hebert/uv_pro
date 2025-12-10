"""
Import .KD files.

A script for parsing .KD files and extracting UV-vis data
and experimental parameters.

@author: David Hebert
"""

import struct
import warnings
from pathlib import Path

import pandas as pd


class KDFile:
    """
    A KDFile object. Contains methods to parse .KD files.

    Attributes
    ----------
    spectra : :class:`pandas.DataFrame`
        A MultiIndex DataFrame with UV-vis spectra from all cells/cuvettes.
        Column levels are `'Cell'` and `'Time (s)'`; indexed by Wavelength (nm).
    spectra_times : :class:`pandas.Series`
        A MultiIndex Series with spectra capture times (s) for all cells/cuvettes.
        Index levels `'Cell'` and `'idx'`.
    cells : list[str]
        A sorted list of all cell/cuvette identifiers (e.g., 'SAMPLES_CELL_1') found in the file.
    is_multicell : bool
        True if the file contains data for more than one cuvette.
    spectra_cell_labels : :class:`pandas.Series`
        The cell/cuvette identifier for each spectrum.
    spectrum_bytes_length : int
        The length (in bytes) of each spectrum based on the range
        of wavelengths captured by the detector.
    file_bytes : bytes
        The bytes read from the .KD file.
    absorbance_data_header : dict
        The hex string header and spacing that precedes the absorbance data in
        the .KD file.
    spectrum_time_header : dict
        The hex string header and spacing that precedes the spectrum times in
        the .KD file.
    cycle_time_header : dict
        The hex string header and spacing that precedes the cycle time in
        the .KD file.
    samples_cell_header : dict
        The hex string header and spacing that precedes the cell/cuvette identifiers in
        the .KD file.
    """

    absorbance_data_header = {
        'header': b'\x28\x00\x41\x00\x55\x00\x29\x00',
        'spacing': 17,
    }
    spectrum_time_header = {
        'header': b'\x52\x00\x65\x00\x6c\x00\x54\x00\x69\x00\x6d\x00\x65\x00',
        'spacing': 20,
    }
    cycle_time_header = {
        'header': b'\x43\x00\x79\x00\x63\x00\x6c\x00'
        b'\x65\x00\x54\x00\x69\x00\x6d\x00'
        b'\x65\x00\x77\x00\x00\x00\x00\x00',
        'spacing': 24,
    }
    samples_cell_header = {
        'header': b'\x52\x00\x65\x00\x67\x00\x4e\x00\x61\x00\x6d\x00\x65\x00\x00\x00\x0f\x00',
        'spacing': 16,
    }

    def __init__(
        self, path: Path, spectrometer_range: tuple[int, int] = (190, 1100)
    ) -> None:
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
        self.wavelength_range = list(
            range(spectrometer_range[0], spectrometer_range[1] + 1)
        )

        self.spectrum_bytes_length = self._get_spectrum_bytes_length()
        self.file_bytes = self._read_binary()

        self._parse_kd()

    @property
    def spectra(self) -> pd.DataFrame:
        """
        Return a MultiIndex DataFrame containing all spectra for all cells.

        Returns
        -------
        :class:`pandas.DataFrame`
            MultiIndex DataFrame with column levels 'Cell' and 'Time (s)'. Index is Wavelength (nm).
        """
        return self._spectra

    @property
    def spectra_times(self) -> pd.Series:
        """
        Return a MultiIndex Series containing all capture times for all cells.

        Returns
        -------
        :class:`pandas.Series`
            MultiIndex Series with index levels 'Cell' and 'idx'.
        """
        return self._spectra_times

    def _get_spectrum_bytes_length(self) -> int:
        """8 hex chars per wavelength."""
        spectrum_bytes_length = (
            self.wavelength_range[-1] - self.wavelength_range[0]
        ) * 8 + 8
        return spectrum_bytes_length

    def _read_binary(self) -> bytes:
        with open(self.path, 'rb') as kd_file:
            file_bytes = kd_file.read()

        return file_bytes

    def _parse_kd(self) -> None:
        """
        Parse a .KD file and extract data.
        """
        cycle_time = self._handle_cycle_time()
        spectra_times = self._handle_spectra_times()
        spectra = self._handle_spectra(spectra_times)
        spectra_cell_labels = self._handle_spectra_cell_labels()

        self.cycle_time = cycle_time
        self.spectra_cell_labels = spectra_cell_labels

        self._spectra = spectra.copy()
        self._spectra.columns = pd.MultiIndex.from_arrays(
            [spectra_cell_labels, spectra_times], names=['Cell', 'Time (s)']
        )
        self._spectra_times = pd.Series(
            spectra_times.to_numpy(),
            index=pd.MultiIndex.from_arrays(
                [spectra_cell_labels.to_numpy(), range(len(spectra_times))],
                names=['Cell', 'idx'],
            ),
            name='Time (s)',
        )

        self.cells = sorted(spectra_cell_labels.unique().tolist())
        self.is_multicell = len(self.cells) > 1

        self._check_monotonic()

    def _handle_spectra(self, spectra_times: pd.Series) -> pd.DataFrame:
        def _spectra_dataframe(spectra: list, spectra_times: pd.Series) -> pd.DataFrame:
            df = pd.concat(spectra, axis=1)
            df.index = pd.Index(self.wavelength_range, name='Wavelength (nm)')
            df.columns = spectra_times
            return df

        if list_of_spectra := self._extract_data(
            KDFile.absorbance_data_header, self._parse_spectra
        ):
            return _spectra_dataframe(list_of_spectra, spectra_times)

        raise Exception('Error parsing file. No spectra found.')

    def _handle_spectra_times(self) -> pd.Series:
        if spectra_times := self._extract_data(
            KDFile.spectrum_time_header, self._parse_spectra_times
        ):
            return pd.Series(spectra_times, name='Time (s)')

        raise Exception('Error parsing file. No spectra times found.')

    def _handle_cycle_time(self) -> int | None:
        try:
            return int(
                self._extract_data(KDFile.cycle_time_header, self._parse_cycle_time)[0]
            )
        except TypeError:
            return None

    def _handle_spectra_cell_labels(self) -> pd.Series:
        if spectra_cell_labels := self._extract_data(
            KDFile.samples_cell_header, self._parse_spectra_cell_labels
        ):
            return spectra_cell_labels[0]  # Only one array per .KD file

        raise Exception('Error parsing file. Samples cell(s) not found.')

    def _extract_data(
        self, header: dict, parse_func: callable, chunk_size: int | None = None
    ) -> list:
        data_list = []
        position = 0
        data_header = header['header']
        spacing = header['spacing']
        chunk_size = (
            chunk_size if chunk_size is not None else self.spectrum_bytes_length
        )

        while True:
            header_idx = self.file_bytes.find(data_header, position)
            if header_idx == -1:
                break

            data_idx = header_idx + spacing
            data_list.append(parse_func(data_idx))
            position = data_idx + chunk_size

        return data_list if data_list else None

    def _parse_spectra(self, data_start: int) -> pd.Series:
        data_end = data_start + self.spectrum_bytes_length
        absorbance_data = self.file_bytes[data_start:data_end]
        absorbance_values = [
            value for (value,) in struct.iter_unpack('<d', absorbance_data)
        ]
        return pd.Series(absorbance_values, index=self.wavelength_range)

    def _parse_spectra_times(self, data_start: int) -> float:
        return float(struct.unpack_from('<d', self.file_bytes, data_start)[0])

    def _parse_cycle_time(self, data_start: int) -> int:
        return int(struct.unpack_from('<d', self.file_bytes, data_start)[0])

    def _parse_spectra_cell_labels(self, data_start: int) -> pd.Series:
        data_end = self.file_bytes.find(b'\x07', data_start)
        spectra_cell_labels_raw = self.file_bytes[data_start:data_end].split(b'\x0f')
        spectra_cell_labels_cleaned = [
            label.replace(b'\x00', b'').decode('utf8')
            for label in spectra_cell_labels_raw[1:]
        ]
        return pd.Series(spectra_cell_labels_cleaned, name='Cell')

    def _check_monotonic(self):
        cells = []
        for cell in self.cells:
            if not self._spectra_times[cell].is_monotonic_increasing:
                cells.append(cell)

        if cells:
            warnings.warn(
                f'Spectra capture times are not monotonic for {", ".join(cells)}. File may be corrupted.',
                stacklevel=3,
            )

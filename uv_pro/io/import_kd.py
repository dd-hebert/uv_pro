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
    absorbance_data_header : dict
        The hex string header and spacing that precedes the absorbance data in
        the .KD file.
    spectrum_time_header : dict
        The hex string header and spacing that precedes the spectrum times in
        the .KD file.
    cycle_time_header : dict
        The hex string header and spacing that precedes the cycle time in
        the .KD file.
    spectrum_bytes_length : int
        The length (in bytes) of each spectrum based on the range
        of wavelengths captured by the detector.
    file_bytes : bytes
        The bytes read from the .KD file.
    spectra : :class:`pandas.DataFrame`
        All of the raw spectra found in the .KD file.
    spectra_times : :class:`pandas.Series`
        The time values that each spectrum was captured.
    cycle_time : int or None
        The cycle time value (in seconds) for the experiment.
    samples_cell : :class:`pandas.Series` or None
        The cell/cuvette identifier for each spectrum.
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
        'header': b'\x52\x00\x65\x00\x67\x00\x4e\x00\x61\x00\x6d\x00\x65\x00',
        'spacing': 18,
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
            range(spectrometer_range[0], spectrometer_range[1])
        )
        self.spectrum_bytes_length = self._get_spectrum_bytes_length()
        self.file_bytes = self._read_binary()
        self.spectra, self.spectra_times, self.cycle_time, self.samples_cell = self.parse_kd()

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

    def parse_kd(self) -> tuple[pd.DataFrame, pd.Series, int, pd.Series | None]:
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
        samples_cell : :class:`pandas.Series` or None
            The cell/cuvette identifier for each spectrum (for multi-cuvette files).
        """
        cycle_time = self._handle_cycletime()
        spectra_times = self._handle_spectratimes()
        spectra = self._handle_spectra(spectra_times)
        samples_cell = self._handle_samples_cell()

        # Validate and fix corrupt timepoints
        spectra, spectra_times, samples_cell = self._validate_and_fix_data(
            spectra, spectra_times, samples_cell
        )

        return spectra, spectra_times, cycle_time, samples_cell

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

    def _handle_spectratimes(self) -> pd.Series:
        if spectra_times := self._extract_data(
            KDFile.spectrum_time_header, self._parse_spectratimes
        ):
            return pd.Series(spectra_times, name='Time (s)')

        raise Exception('Error parsing file. No spectra times found.')

    def _validate_and_fix_data(
        self,
        spectra: pd.DataFrame,
        spectra_times: pd.Series,
        samples_cell: pd.Series | None,
    ) -> tuple[pd.DataFrame, pd.Series, pd.Series | None]:
        """
        Validate that time values are monotonically increasing within each cuvette.

        If non-increasing time values are found (indicating file corruption),
        issue a warning and remove the corrupt timepoints and their spectra.

        Parameters
        ----------
        spectra : pd.DataFrame
            The spectra data with time as columns.
        spectra_times : pd.Series
            The time values for each spectrum.
        samples_cell : pd.Series or None
            The cell/cuvette identifier for each spectrum.

        Returns
        -------
        tuple[pd.DataFrame, pd.Series, pd.Series | None]
            The validated/fixed spectra, times, and samples_cell data.
        """
        # Build a working dataframe by transposing spectra (rows become spectra, columns become wavelengths)
        work_df = spectra.T.reset_index()
        work_df.rename(columns={'Time (s)': 'Time_s'}, inplace=True)
        cell_values = samples_cell if samples_cell is not None else pd.Series(['SAMPLES_CELL_1'] * len(work_df))
        work_df.insert(0, 'sample', cell_values.values)

        def find_valid_rows(group: pd.DataFrame) -> pd.DataFrame:
            """Find rows where times are monotonically increasing."""
            times = group['Time_s'].values
            valid_mask = [True] * len(times)

            # Find reset points where time decreases
            for i in range(1, len(times)):
                if times[i] < times[i - 1]:
                    # Mark all previous times >= current time as invalid
                    for j in range(i):
                        if times[j] >= times[i]:
                            valid_mask[j] = False

            return group[valid_mask]

        # Apply validation per cell group - get valid indices
        valid_indices = work_df.groupby('sample', group_keys=False).apply(
            find_valid_rows, include_groups=False
        ).index

        # Check if any data was removed
        removed_count = len(work_df) - len(valid_indices)
        if removed_count > 0:
            removed_indices = set(work_df.index) - set(valid_indices)
            removed_times = work_df.loc[list(removed_indices), 'Time_s'].tolist()

            warnings.warn(
                f"Potentially corrupted .KD file detected: {self.path}. "
                f"Time values are not monotonically increasing.",
                UserWarning
            )
            warnings.warn(
                f"Removed {removed_count} corrupt timepoint(s) "
                f"at indices {sorted(removed_indices)} with time values {removed_times}. "
                f"These timepoints and their corresponding spectra have been excluded.",
                UserWarning
            )

            # Filter work_df using valid indices
            clean_df = work_df.loc[valid_indices]

            # Rebuild the clean data
            clean_spectra_times = pd.Series(clean_df['Time_s'].values, name='Time (s)')
            clean_samples_cell = pd.Series(clean_df['sample'].values, name='Cell') if samples_cell is not None else None

            # Rebuild spectra dataframe (transpose back)
            wavelength_cols = [col for col in clean_df.columns if col not in ['sample', 'Time_s']]
            clean_spectra = clean_df[wavelength_cols].T
            clean_spectra.index = pd.Index(self.wavelength_range, name='Wavelength (nm)')
            clean_spectra.columns = clean_spectra_times

            return clean_spectra, clean_spectra_times, clean_samples_cell

        return spectra, spectra_times, samples_cell

    def _handle_cycletime(self) -> int | None:
        try:
            return int(
                self._extract_data(KDFile.cycle_time_header, self._parse_cycletime)[0]
            )
        except TypeError:
            return None

    def _handle_samples_cell(self) -> pd.Series | None:
        data_header = KDFile.samples_cell_header['header']
        spacing = KDFile.samples_cell_header['spacing']

        header_idx = self.file_bytes.find(data_header)
        if header_idx == -1:
            return None

        samples_cell = []
        position = header_idx + spacing

        while True:
            cell_name = self._parse_samples_cell(position)
            if cell_name is None or not cell_name.startswith('SAMPLES_CELL'):
                break
            samples_cell.append(cell_name)
            position += 30  # 2-byte prefix + 28-byte cell name (14 chars * 2)

        if samples_cell:
            return pd.Series(samples_cell, name='Cell')

        return None

    def _extract_data(self, header: dict, parse_func: callable) -> list:
        data_list = []
        position = 0
        data_header = header['header']
        spacing = header['spacing']
        chunk = self.spectrum_bytes_length

        while True:
            header_idx = self.file_bytes.find(data_header, position)
            if header_idx == -1:
                break

            data_idx = header_idx + spacing
            data_list.append(parse_func(data_idx))
            position = data_idx + chunk

        return data_list if data_list else None

    def _parse_spectra(self, data_start: int) -> pd.Series:
        data_end = data_start + self.spectrum_bytes_length
        absorbance_data = self.file_bytes[data_start:data_end]
        absorbance_values = [
            value for (value,) in struct.iter_unpack('<d', absorbance_data)
        ]
        return pd.Series(absorbance_values, index=self.wavelength_range)

    def _parse_spectratimes(self, data_start: int) -> float:
        return float(struct.unpack_from('<d', self.file_bytes, data_start)[0])

    def _parse_cycletime(self, data_start: int) -> int:
        return int(struct.unpack_from('<d', self.file_bytes, data_start)[0])

    def _parse_samples_cell(self, data_start: int) -> str | None:
        try:
            data_end = data_start + 28  # 14 chars * 2 bytes per char
            cell_name_bytes = self.file_bytes[data_start:data_end]
            return cell_name_bytes.decode('utf-16-le').rstrip('\x00')
        except (IndexError, UnicodeDecodeError):
            return None

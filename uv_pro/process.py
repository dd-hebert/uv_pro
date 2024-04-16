"""
Process UV-vis Data.

Tools for processing UV-vis data files (.KD format) from the Agilent 845x
UV-vis Chemstation software.

@author: David Hebert
"""

import os
import pandas as pd
from uv_pro.io.import_kd import KDFile
from uv_pro.outliers import find_outliers
from uv_pro.fitting import fit_exponential
from uv_pro.slicing import slice_spectra
from uv_pro.utils.printing import print_dataset


class Dataset:
    """
    A Dataset object. Contains methods to process UV-vis data.

    Attributes
    ----------
    name : str
        The name of the .KD file that the :class:`Dataset` was created from.
    cycle_time : int
        The cycle time in seconds from the experiment.
    raw_spectra : :class:`pandas.DataFrame`
        The raw spectra found in the .KD file that the :class:`Dataset`
        was created from.
    time_traces : :class:`pandas.DataFrame`
        The time traces for the :class:`Dataset`. The number of time traces and
        their wavelengths are dictated by ``time_trace_window`` and
        ``time_trace_interval``.
    chosen_traces : :class:`pandas.DataFrame`
        Time traces for user-specified wavelengths.
    outliers : list
        The times of outlier spectra.
        See :func:`~uv_pro.outliers.find_outliers()` for more information.
    baseline : :class:`pandas.Series`
       The baseline of the summed :attr:`time_traces`.
       See :func:`~uv_pro.outliers.find_outliers()` for more information.
    processed_spectra : :class:`pandas.DataFrame`
        The processed spectra with :attr:`outliers` removed and with trimming
        and slicing applied.
    processed_traces : :class:`pandas.DataFrame`
        The processed chosen traces with :attr:`outliers` and trimming applied.
    is_processed : bool
        Indicates if the data has been processed. Data is processed only if the
        :class:`Dataset` was initialized with ``view_only=False``
        and it contains more than 2 spectra.
    """

    def __init__(self, path: str, trim: list[int, int] | None = None,
                 slicing: dict | None = None, fitting: bool = False,
                 outlier_threshold: float = 0.1, baseline_lambda: float = 10,
                 baseline_tolerance: float = 0.1, low_signal_window: str = 'narrow',
                 time_trace_window: tuple[int, int] = (300, 1060),
                 time_trace_interval: int = 10, wavelengths: list | None = None,
                 view_only: bool = False) -> None:
        """
        Initialize a :class:`Dataset`.

        Parses the .KD file at ``path`` and processes the found spectra to
        remove "bad" spectra (e.g. spectra collected when mixing the solution).

        Parameters
        ----------
        path : str
            A file path to a .KD file.
        trim : list[int, int] or None, optional
            Trim data outside a given time range: ``[trim_before, trim_after]``.
            Default value is None (no trimming).
        slicing : dict or None, optional
            Reduce the data down to a selection of slices. Slices can be taken in
            equally- or unequally-spaced (gradient) intervals. For equal
            slicing: ``{'mode': 'equal', 'slices': int}``. For gradient slicing:
            ``{'mode': 'gradient', 'coeff': float, 'expo': float}``.
        fitting : bool, optional
            Perform exponential fitting on the time traces specified with ``wavelengths``
        outlier_threshold : float, optional
            A value between 0 and 1 indicating the threshold by which spectra
            are considered outliers. Values closer to 0 produce more outliers,
            while values closer to 1 produce fewer outliers. Use a value >>1 to guarantee
            no data are considered outliers. The default value is 0.1.
        baseline_lambda : float, optional
            Set the smoothness of the baseline (for outlier detection). Higher values
            give smoother baselines. Try values between 0.001 and 10000. The default is 10.
        baseline_tolerance : float, optional
            Set the exit criteria for the baseline algorithm. Try values between
            0.001 and 10000. The default is 0.1. See :func:`pybaselines.whittaker.asls()`
            for more information.
        low_signal_window : str, "narrow" or "wide", optional
            Set the width of the low signal detection window (see
            :func:`~uv_pro.outliers.find_outliers()`). Set to wide if low signal
            outliers are affecting the baseline.
        time_trace_window : tuple[int, int] or None, optional
            The range (min, max) of wavelengths (in nm) to get time traces for.
            Used in :meth:`~uv_pro.process.Dataset.get_time_traces()`.
            The default is (300, 1060).
        time_trace_interval : int, optional
            The wavelength interval (in nm) between time traces. A smaller interval
            produces more time traces. Used in :meth:`~uv_pro.process.Dataset.get_time_traces()`
            For example, an interval of 20 would generate time traces like this:
            [window min, window min + 20, window min + 40, ..., window max - 20, window max].
            The default value is 10.
        wavelengths : list[int, ...] or None, optional
            A list of specific wavelengths to get time traces for. These time traces are
            independent of those created by :meth:`~uv_pro.process.Dataset.get_time_traces()`.
            The default is None.
        view_only : bool, optional
            Indicate if data processing (cleaning and trimming) should be
            performed. Default is False (processing is performed).
        """
        self.path = path
        self.name = os.path.basename(self.path)
        self.trim = trim
        self.slicing = slicing
        self.fitting = fitting
        self.time_trace_window = time_trace_window
        self.time_trace_interval = time_trace_interval
        self.wavelengths = wavelengths
        self.outlier_threshold = outlier_threshold
        self.low_signal_window = low_signal_window
        self.baseline_lambda = baseline_lambda
        self.baseline_tolerance = baseline_tolerance
        self.is_processed = False

        self._import_data()

        if not view_only:
            self.process_data()

    def __str__(self) -> str:
        return print_dataset(self)

    def _import_data(self) -> None:
        kd_file = KDFile(self.path)
        self.raw_spectra = kd_file.spectra
        self.spectra_times = kd_file.spectra_times
        self.cycle_time = kd_file.cycle_time

    def process_data(self) -> None:
        """
        Process the UV-vis dataset.

        Gets time traces, finds outliers, processes the spectra
        and traces, and performs data fitting according to the
        attributes of the :class:`~uv_pro.process.Dataset`.
        """
        if len(self.raw_spectra.columns) <= 2:
            pass
        else:
            self.time_traces = self.get_time_traces(
                window=self.time_trace_window,
                interval=self.time_trace_interval
            )

            self.outliers, self.baseline = find_outliers(
                time_traces=self.time_traces,
                threshold=self.outlier_threshold,
                lsw=self.low_signal_window,
                lam=self.baseline_lambda,
                tol=self.baseline_tolerance
            )

            self._check_trim_values()
            self.processed_spectra = self._process_spectra()
            self.chosen_traces, self.processed_traces = self._process_chosen_traces(self.wavelengths)

            if self.fitting is True:
                self.fit = fit_exponential(self.processed_traces)
            else:
                self.fit = None

            self.is_processed = True

    def _process_spectra(self):
        processed_spectra = self.clean_data(self.raw_spectra, axis='columns')

        if self.trim is not None:
            processed_spectra = self.trim_data(processed_spectra, axis='columns')

        if self.slicing is not None:
            processed_spectra = slice_spectra(processed_spectra, self.slicing)

        return processed_spectra

    def _process_chosen_traces(self, wavelengths):
        if wavelengths is not None:
            chosen_traces = self.get_chosen_traces(wavelengths)

            if chosen_traces is not None:
                processed_traces = self.clean_data(chosen_traces, axis='index')

                if self.trim is not None:
                    processed_traces = self.trim_data(processed_traces, axis='index')

            return chosen_traces, processed_traces

        return None, None

    def get_time_traces(self, window=(300, 1060), interval=10):
        """
        Iterate through different wavelengths and get time traces.

        Note
        ----
        Time traces that have a median absorbance above 1.75 AU
        are excluded due to saturation of the detector. These high
        intensity traces can negatively impact outlier detection.

        Parameters
        ----------
        window : tuple, optional
            The range of wavelengths (in nm) to get time traces for (min, max).
            The default value is (300, 1060).
        interval : int, optional
            The wavelength interval (in nm) between time traces. A ``window`` of
            (300, 1000) with an ``interval`` of 10 will get time traces
            from [300, 310, 320, ... , 970, 980, 990] nm. The
            default value is 10.

        Returns
        -------
        :class:`pandas.DataFrame`
            The raw time traces, where each column is a different wavelength.
        """
        all_time_traces = {}
        for wavelength in range(window[0], window[1] + 1, interval):
            time_trace = self.raw_spectra.loc[wavelength]
            time_trace.index = pd.Index(self.spectra_times, name='Time (s)')
            if time_trace.median() < 1.75:  # Exclude saturated wavelengths.
                key = f'{wavelength} (nm)'
                all_time_traces[key] = time_trace
        return pd.DataFrame.from_dict(all_time_traces)

    def get_chosen_traces(self, wavelengths, window=(190, 1100)):
        """
        Get time traces of specific wavelengths.

        Parameters
        ----------
        wavelengths: list
            A list of wavelengths to get time traces for.
        window : tuple, optional
            The range of wavelengths captured by the spectrometer.
            The default value is (190, 1100).

        Returns
        -------
        :class:`pandas.DataFrame` or None
            The raw time traces, where each column is a different
            wavelength. Otherwise, returns None if no wavelengths
            are given or no time traces could be made.
        """
        time_traces = {}
        for wavelength in wavelengths:
            if int(wavelength) not in range(window[0], window[1] + 1):
                continue

            trace = self.raw_spectra.loc[int(wavelength)]
            key = f'{int(wavelength)} (nm)'
            time_traces[key] = trace

        if time_traces:
            chosen_traces = pd.DataFrame.from_dict(time_traces)
            time_values = pd.Index(self.spectra_times, name='Time (s)')
            chosen_traces.set_index(time_values, inplace=True)
            return chosen_traces
        else:
            return None

    def clean_data(self, data: pd.DataFrame, axis: str) -> pd.DataFrame:
        """
        Remove outliers from ``data`` along ``axis``.

        Parameters
        ----------
        data : :class:`pandas.DataFrame`
            The data to be cleaned.
        axis : str
            'index' or 'columns'.

        Returns
        -------
        :class:`pandas.DataFrame`
            The data with :attr:`outliers` removed.
        """
        return data.drop(self.outliers, axis=axis)

    def trim_data(self, data: pd.DataFrame, axis: str) -> pd.DataFrame:
        """
        Truncate ``data`` along ``axis`` to the time range given by :attr:`trim`.

        Parameters
        ----------
        data : :class:`pandas.DataFrame`
            The data to be trimmed.
        axis : str
            'index' or 'columns'.

        Returns
        -------
        :class:`pandas.DataFrame`
            The trimmed data.
        """
        return data.truncate(before=self.trim[0], after=self.trim[1], axis=axis)

    def _check_trim_values(self) -> None:
        try:
            start = min(self.trim)
            end = max(self.trim)
            self.trim = (start, end)
        except TypeError:
            pass

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
from uv_pro.fitting import fit_exponential, initial_rates
from uv_pro.slicing import slice_spectra


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
        The time traces for the :class:`Dataset`. The number of time traces and \
        their wavelengths are dictated by ``time_trace_window`` and \
        ``time_trace_interval``.
    chosen_traces : :class:`pandas.DataFrame`
        Time traces of user-specified wavelengths.
    outliers : list
        The times of outlier spectra.
        See :func:`~uv_pro.outliers.find_outliers()` for more information.
    baseline : :class:`pandas.Series`
       The baseline of the summed :attr:`time_traces`.
       See :func:`~uv_pro.outliers.find_outliers()` for more information.
    processed_spectra : :class:`pandas.DataFrame`
        The processed spectra with :attr:`outliers` removed and with
        trimming and slicing applied.
    processed_traces : :class:`pandas.DataFrame`
        The processed chosen traces with :attr:`outliers` removed and
        trimming applied.
    fit : dict
        The fitting curves and parameters.
    is_processed : bool
        Indicates if the data has been processed. Data is processed only if the \
        :class:`Dataset` was initialized with ``view_only=False`` \
        and it contains more than 2 spectra.
    """

    def __init__(self, path: str, *, trim: tuple[int, int] | None = None,
                 slicing: dict | None = None, fit_exp: bool = False,
                 fit_init_rate: float | None = None, outlier_threshold: float = 0.1,
                 baseline_smoothness: float = 10.0, baseline_tolerance: float = 0.1,
                 low_signal_window: str = 'none', time_trace_window: tuple[int, int] = (300, 1060),
                 time_trace_interval: int = 10, wavelengths: list | None = None,
                 view_only: bool = False) -> None:
        """
        Initialize a :class:`Dataset`.

        Parses a .KD file at ``path`` and processes the found spectra. Processing \
        includes removing "bad" spectra (e.g. stray light or spectra collected \
        during mixing), trimming (see :meth:`trim_data`), slicing \
        (see :func:`~uv_pro.slicing.slice_spectra`), and kinetics analysis of \
        time traces.

        Parameters
        ----------
        path : str
            A file path to a .KD file.
        trim : tuple[int, int] or None, optional
            Trim data outside a given time range: ``(trim_before, trim_after)``.
            Default value is None (no trimming).
        slicing : dict or None, optional
            Reduce the data down to a selection of slices. Slices can be taken in \
            equally- or unequally-spaced (gradient) intervals, or at specific times.
            For equal slicing: ``{'mode': 'equal', 'slices': int}``.
            For gradient slicing: ``{'mode': 'gradient', 'coeff': float, 'expo': float}``.
            For specific slicing: ``{'mode': 'specific', 'times': list[float]}``.
        fit_exp : bool, optional
            Perform exponential fitting on the time traces specified with ``wavelengths``.
        fit_init_rate : float or None, optional
            Perform initial rates linear regression fitting on the time traces specified \
            with ``wavelengths``.
        outlier_threshold : float, optional
            A value between 0 and 1 indicating the threshold by which spectra
            are considered outliers. Values closer to 0 produce more outliers,
            while values closer to 1 produce fewer outliers. Use a value >>1 to guarantee
            no data are considered outliers. The default value is 0.1.
        baseline_smoothness : float, optional
            Set the smoothness of the baseline (for outlier detection). Higher values \
            give smoother baselines. Try values between 0.001 and 10000.
            See :func:`~uv_pro.outliers.find_outliers`. The default is 10.
        baseline_tolerance : float, optional
            Set the exit criteria for the baseline algorithm. Try values between \
            0.001 and 10000. The default is 0.1. See :func:`pybaselines.whittaker.asls()`
            for more information.
        low_signal_window : str, "narrow", "wide", or "none", optional
            Set the width of the low signal detection window (see \
            :func:`~uv_pro.outliers.find_outliers()`). Set to wide if low signal
            outliers are affecting the baseline. The default is "none".
        time_trace_window : tuple[int, int] or None, optional
            The range (min, max) of wavelengths (in nm) to get time traces for.
            Used in :meth:`~uv_pro.dataset.Dataset.get_time_traces()`.
            The default is (300, 1060).
        time_trace_interval : int, optional
            The wavelength interval (in nm) between time traces. A smaller interval \
            produces more time traces. Used in :meth:`~uv_pro.dataset.Dataset.get_time_traces()`.
            An interval of 20 would generate time traces like this:
            [window min, window min + 20, window min + 40, ..., window max - 20, window max].
            The default value is 10.
        wavelengths : list[int] or None, optional
            A list of specific wavelengths to get time traces for. These time traces are \
            independent of those created by :meth:`~uv_pro.dataset.Dataset.get_time_traces()`.
            The default is None.
        view_only : bool, optional
            Indicate if data processing (cleaning and trimming) should be performed.
            Default is False (processing is performed).
        """
        self.path = path
        self.name = os.path.basename(self.path)
        self.trim = trim
        self.slicing = slicing
        self.fit_exp = fit_exp
        self.fit_init_rate = fit_init_rate
        self.time_trace_window = time_trace_window
        self.time_trace_interval = time_trace_interval
        self.wavelengths = wavelengths
        self.outlier_threshold = outlier_threshold
        self.low_signal_window = low_signal_window
        self.baseline_smoothness = baseline_smoothness
        self.baseline_tolerance = baseline_tolerance
        self.fit = None
        self.init_rate = None
        self.is_processed = False

        self._import_data()

        if not view_only:
            self.process_data()

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
        attributes of the :class:`~uv_pro.dataset.Dataset`.
        """
        if len(self.raw_spectra.columns) > 2:
            self.time_traces = self.get_time_traces(
                window=self.time_trace_window,
                interval=self.time_trace_interval
            )

            self.outliers, self.baseline = find_outliers(
                time_traces=self.time_traces,
                threshold=self.outlier_threshold,
                lsw=self.low_signal_window,
                lam=self.baseline_smoothness,
                tol=self.baseline_tolerance
            )

            self._check_trim_values()
            self.processed_spectra = self._process_spectra()
            self.chosen_traces, self.processed_traces = self._process_chosen_traces(self.wavelengths)

            if self.processed_traces is not None:
                if self.fit_exp is True:
                    self.fit = fit_exponential(self.processed_traces)

                if self.fit_init_rate is not None:
                    self.init_rate = initial_rates(self.processed_traces, cutoff=self.fit_init_rate)

            self.is_processed = True

    def _process_spectra(self) -> pd.DataFrame:
        processed_spectra = self.clean_data(self.raw_spectra, axis='columns')

        if self.trim is not None:
            processed_spectra = self.trim_data(processed_spectra, axis='columns')

        if self.slicing is not None:
            processed_spectra = slice_spectra(processed_spectra, self.slicing)

        return processed_spectra

    def _process_chosen_traces(self, wavelengths: list[int]) -> tuple[pd.DataFrame, pd.DataFrame] | tuple[None, None]:
        if wavelengths is None:
            return None, None

        chosen_traces = self.get_chosen_traces(wavelengths)

        if chosen_traces is None:
            return None, None

        processed_traces = self.clean_data(chosen_traces, axis='index')

        if self.trim:
            processed_traces = self.trim_data(processed_traces, axis='index')

        return chosen_traces, processed_traces

    def get_time_traces(self, window=(300, 1060), interval=10) -> pd.DataFrame:
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
        time_traces = self.raw_spectra.loc[window[0]:window[1]:interval]
        return time_traces[time_traces.median(axis='columns') < 1.75].transpose()

    def get_chosen_traces(self, wavelengths: list[int]) -> pd.DataFrame | None:
        """
        Get time traces of specific wavelengths.

        Parameters
        ----------
        wavelengths: list[int]
            A list of wavelengths to get time traces for.

        Returns
        -------
        :class:`pandas.DataFrame` or None
            The chosen time traces, where each column is a different
            wavelength. Returns None if no wavelengths are given or if
            the given wavelengths are not found in :attr:`raw_spectra`.
        """
        wavelengths = [
            wavelength for wavelength in set(wavelengths) if wavelength in self.raw_spectra.index
        ]

        return self.raw_spectra.loc[wavelengths].transpose() if wavelengths else None

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
            start, end = self.trim
            start = max(start, self.spectra_times.iloc[0])

            if end >= self.spectra_times.iloc[-1] or end == -1:
                end = self.spectra_times.iloc[-1]

            self.trim = (start, end)

        except TypeError:
            pass

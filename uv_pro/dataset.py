"""
Process UV-vis Data.

Tools for processing UV-vis data files (.KD format) from the Agilent 845x
UV-vis Chemstation software.

@author: David Hebert
"""

import os
import pandas as pd
from rich import print
from rich.table import Table, Column
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

    def __init__(self, path: str, *, trim: list[int, int] | None = None,
                 slicing: dict | None = None, fit_exp: bool = False,
                 fit_init_rate: float | None = None, outlier_threshold: float = 0.1,
                 baseline_lambda: float = 10.0, baseline_tolerance: float = 0.1,
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
        trim : list[int, int] or None, optional
            Trim data outside a given time range: ``[trim_before, trim_after]``.
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
        baseline_lambda : float, optional
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
        self.baseline_lambda = baseline_lambda
        self.baseline_tolerance = baseline_tolerance
        self.fit = None
        self.init_rate = None
        self.is_processed = False

        self._import_data()

        if not view_only:
            self.process_data()

    def __str__(self) -> str:
        print(*self._to_string(), sep='\n')
        return ''

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
        start, end = self.trim

        if end >= self.spectra_times.iloc[-1] or end == -1:
            end = self.spectra_times.iloc[-1]

        self.trim = (start, end)

    def _to_string(self) -> str:
        def rich_text(dataset: Dataset) -> list:
            out = []
            out.append(f'Filename: {dataset.name}')
            out.append(f'Spectra found: {len(dataset.raw_spectra.columns)}')

            if dataset.cycle_time:
                out.append(f'Cycle time (s): {dataset.cycle_time}')

            if dataset.is_processed is True:
                out.append(f'Outliers found: {len(dataset.outliers)}')

                if dataset.trim:
                    start, end = dataset.trim
                    start = 'start' if start == 0 else f'{start} seconds'
                    end = 'end' if end >= dataset.spectra_times.iloc[-1] else f'{end} seconds'

                    out.append(f'Keeping data from {start} to {end}.')

                if dataset.slicing is None:
                    out.append(f'Spectra remaining: {len(dataset.processed_spectra.columns)}')

                else:
                    out.append(f'Slicing mode: {dataset.slicing["mode"]}')
                    if dataset.slicing['mode'] == 'gradient':
                        out.append(f'Coefficient: {dataset.slicing["coeff"]}')
                        out.append(f'Exponent: {dataset.slicing["expo"]}')

                    out.append(f'Slices: {len(dataset.processed_spectra.columns)}')

                if dataset.fit is not None:
                    out.extend(['', fit(dataset.fit)])
                    if unable_to_fit := set(dataset.chosen_traces.columns).difference(set(dataset.fit['curves'].columns)):
                        out.append(f'\033[31mUnable to fit: {", ".join(map(str, unable_to_fit))} nm.\033[0m')

                if dataset.init_rate is not None:
                    out.extend(['', init_rate(dataset.init_rate)])

            return out

        def fit(fit: dict) -> str:
            equation = 'f(t) = abs_f + (abs_0 - abs_f) * exp(-kobs * t)'
            table = Table(
                Column('λ', justify='center'),
                Column('kobs', justify='center'),
                Column('abs_0', justify='center'),
                Column('abs_f', justify='center'),
                Column('r2', justify='center'),
                title='Exponential Fit Results',
                caption=f'Fit function: {equation}',
                width=65
            )


            for wavelength in fit['params'].columns:
                params = fit['params'][wavelength]
                table.add_row(
                    str(wavelength),
                    '{:.2e} ± {:.2e}'.format(params['kobs'], params['kobs err']),
                    '{: .2e}'.format(params['abs_0']),
                    '{: .2e}'.format(params['abs_f']),
                    '{:.4f}'.format(params['r2'])
                )

            return table

        def init_rate(init_rate: dict) -> str:
            table = Table(
                Column('λ', justify='center'),
                Column('rate', justify='center'),
                Column('Δabs', justify='center'),
                Column('Δt', justify='center'),
                Column('r2', justify='center'),
                title='Initial Rates Results',
                width=65
            )

            for wavelength in init_rate['params'].columns:
                params = init_rate['params'][wavelength]
                table.add_row(
                    str(wavelength),
                    '{: .2e} ± {:.2e}'.format(params['slope'], params['slope err']),
                    '{:.2%}'.format(abs(params['delta_abs_%'])),
                    '{:.1f}'.format(params['delta_t']),
                    '{:.4f}'.format(params['r2'])
                )

            return table

        return rich_text(self)

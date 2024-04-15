"""
Process UV-Vis Data.

Tools for processing UV-Vis data files (.KD format) from the Agilent 845x
UV-Vis Chemstation software.

@author: David Hebert
"""

import os
import pandas as pd
from uv_pro.io.import_kd import KDFile
from uv_pro.outliers import find_outliers
from uv_pro.fitting import fit_exponential
from uv_pro.utils.printing import print_dataset


class Dataset:
    """
    A Dataset object. Contains methods to process UV-Vis data.

    Attributes
    ----------
    name : str
        The name of the .KD file that the :class:`Dataset` was created from.
    cycle_time : int
        The cycle time in seconds from the experiment.
    all_spectra : :class:`pandas.DataFrame`
        All the raw spectra in the :class:`Dataset`.
    time_traces : :class:`pandas.DataFrame`
        The time traces for the :class:`Dataset`. The number of time traces and
        their wavelengths are dictated by `time_trace_window` and
        `time_trace_interval`.
    specific_time_traces : :class:`pandas.DataFrame`
        Time traces for user-specified wavelengths.
    outliers : list
        The times of outlier spectra.
        See :func:`~uv_pro.outliers.find_outliers()` for more information.
    baseline : :class:`pandas.Series`
       The baseline of the summed :attr:`time_traces`.
       See :func:`~uv_pro.outliers.find_outliers()` for more information.
    cleaned_spectra : :class:`pandas.DataFrame`
        The spectra with :attr:`outliers` removed.
    trimmed_spectra : :class:`pandas.DataFrame`
        The spectra that fall within the given time range.
    sliced_spectra : :class:`pandas.DataFrame`
        The selected spectra slices.
    is_processed : bool
        Indicates if the data has been processed. Data is processed only if the
        :class:`~uv_pro.process.Dataset` was initialized with ``view_only=False``
        and it contains more than 2 spectra.
    """

    def __init__(self, path: str,
                 trim: list[int, int] | None = None,
                 slicing: dict | None = None,
                 fitting: bool = False,
                 outlier_threshold: float = 0.1,
                 baseline_lambda: float = 10,
                 baseline_tolerance: float = 0.1,
                 low_signal_window: str = 'narrow',
                 time_trace_window: tuple[int, int] = (300, 1060),
                 time_trace_interval: int = 10,
                 wavelengths: list | None = None,
                 view_only: bool = False
                 ) -> None:
        """
        Initialize a :class:`~uv_pro.process.Dataset`.

        Parses the .KD file at ``path`` and processes it to remove "bad"
        spectra (e.g. spectra collected when mixing the solution).

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
            ``{'mode': 'gradient', 'coefficient': float, 'exponent': float}``.
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
        self._import_data()
        self.is_processed = False

        if not view_only and len(self.all_spectra.columns) > 2:
            self.process_data()
            self.is_processed = True

    def __str__(self) -> str:
        return print_dataset(self)

    def _import_data(self) -> None:
        kd_file = KDFile(self.path)
        self.all_spectra = kd_file.spectra
        self.spectra_times = kd_file.spectra_times
        self.cycle_time = kd_file.cycle_time

    def process_data(self) -> None:
        self.time_traces = self.get_time_traces(window=self.time_trace_window,
                                                interval=self.time_trace_interval)

        self.specific_time_traces = self.get_specific_time_traces(self.wavelengths)

        self.outliers, self.baseline = find_outliers(time_traces=self.time_traces,
                                                     threshold=self.outlier_threshold,
                                                     lsw=self.low_signal_window,
                                                     lam=self.baseline_lambda,
                                                     tol=self.baseline_tolerance)

        self.cleaned_spectra, self.cleaned_traces = self.clean_data()

        if self.trim is None:
            self.trimmed_spectra = self.cleaned_spectra
            self.trimmed_traces = self.specific_time_traces
        else:
            self.trimmed_spectra, self.trimmed_traces = self.trim_data()

        if self.slicing is None:
            self.sliced_spectra = self.trimmed_spectra
        else:
            self.sliced_spectra = self.slice_data()

        if self.fitting is True and self.trimmed_traces is not None:
            self.fit = fit_exponential(self.trimmed_traces)
        else:
            self.fit = None

    def get_time_traces(self, window=(300, 1060), interval=10):
        """
        Iterate through different wavelengths and get time traces.

        Time traces which saturate the detector due to high intensity are
        removed by checking if they have a median absorbance above 1.75 AU.
        The raw (un-normalized) time traces are returned.

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
            time_trace = self.all_spectra.loc[wavelength]
            time_trace.index = pd.Index(self.spectra_times, name='Time (s)')
            if time_trace.median() < 1.75:  # Exclude saturated wavelengths.
                key = f'{wavelength} (nm)'
                all_time_traces[key] = time_trace
        return pd.DataFrame.from_dict(all_time_traces)

    def get_specific_time_traces(self, wavelengths, window=(190, 1100)):
        """
        Get time traces of specific wavelengths.

        Parameters
        ----------
        wavelengths: list or None
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
        if wavelengths is None:
            return None
        else:
            all_time_traces = {}
            for wavelength in wavelengths:
                if int(wavelength) not in range(window[0], window[1] + 1):
                    continue

                time_trace = self.all_spectra.loc[int(wavelength)]
                key = f'{int(wavelength)} (nm)'
                all_time_traces[key] = time_trace

            if all_time_traces:
                specific_time_traces = pd.DataFrame.from_dict(all_time_traces)
                time_values = pd.Index(self.spectra_times, name='Time (s)')
                specific_time_traces.set_index(time_values, inplace=True)
                return specific_time_traces
            else:
                return None

    def clean_data(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Remove outliers from :attr:`all_spectra` and :attr:`specific_time_traces`.

        Returns
        -------
        cleaned_spectra : :class:`pandas.DataFrame`
            The spectra with outlier spectra removed.
        cleaned_traces : :class:`pandas.DataFrame`
            The time traces with outlier points removed.
        """
        cleaned_spectra = self.all_spectra.drop(self.outliers, axis='columns')
        if self.specific_time_traces is not None:
            cleaned_traces = self.specific_time_traces.drop(self.outliers)
        else:
            cleaned_traces = None
        return cleaned_spectra, cleaned_traces

    def trim_data(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Truncate the data to the time range given by :attr:`Dataset.trim`."""
        self._check_trim_values()
        trimmed_spectra = self.cleaned_spectra.truncate(before=self.trim[0], after=self.trim[1], axis='columns')
        if self.cleaned_traces is not None:
            trimmed_traces = self.cleaned_traces.truncate(before=self.trim[0], after=self.trim[1])
        else:
            trimmed_traces = None
        return trimmed_spectra, trimmed_traces

    def _check_trim_values(self) -> None:
        start = min(self.trim)
        end = max(self.trim)
        self.trim = (start, end)

    def slice_data(self) -> pd.DataFrame:
        """
        Reduce the data down to a selection of slices.

        Slices can be taken at equally-spaced or unequally-spaced
        (gradient) intervals. Equal slicing requires a single integer
        (e.g., a value of 10 will produce 10 equally-spaced slices).
        Gradient slicing requires two floats, a coefficient and an exponent.
        For gradient slicing, the step size between slices is calculated
        by the equation step_size = [coefficient*x^exponent + 1].

        Slicing behavior is determined by :attr:`uv_pro.process.Dataset.slicing`.
        For equal slicing: ``{'mode': 'equal', 'slices': int}``.
        For gradient (unequally-spaced) slicing: ``{'mode': 'gradient',
        'coefficient': float, 'exponent': float}``.

        Returns
        -------
        sliced_spectra : :class:`pandas.DataFrame`
            The spectra slices given by :attr:`uv_pro.process.Dataset.slicing`.
        """
        if self.slicing['mode'] == 'gradient':
            sliced_spectra = self._gradient_slicing()
        else:
            sliced_spectra = self._equal_slicing()
        return sliced_spectra

    def _gradient_slicing(self) -> pd.DataFrame:
        coefficient = self._check_gradient_slice_coeff()
        exponent = self.slicing['exponent']
        slices = []
        i = 1
        while sum(slices) < len(self.trimmed_spectra.columns):
            slices.append(round(coefficient * i**exponent + 1))
            i += 1
        while sum(slices) >= len(self.trimmed_spectra.columns):
            slices.pop()

        columns_to_keep = [0]
        for index, value in enumerate(slices):
            columns_to_keep.append(columns_to_keep[index] + value)
        return self.trimmed_spectra.iloc[:, columns_to_keep]

    def _check_gradient_slice_coeff(self) -> float:
        coefficient = self.slicing['coefficient']
        if coefficient > 0:
            return coefficient
        else:
            raise ValueError('Invalid gradient slicing coefficient. Value must be >0.')

    def _equal_slicing(self) -> pd.DataFrame:
        step = round(len(self.trimmed_spectra.columns) / int(self.slicing['slices']))
        if step == 0:
            step = 1
        columns_to_keep = list(range(0, len(self.trimmed_spectra.columns), step))
        return self.trimmed_spectra.iloc[:, columns_to_keep]

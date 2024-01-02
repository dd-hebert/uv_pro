"""
Process UV-Vis Data.

Tools for processing UV-Vis data files (.KD format) from the Agilent 845x
UV-Vis Chemstation software.

@author: David Hebert
"""

import os
import pandas as pd
from pybaselines import whittaker
from uv_pro.io.import_kd import KDFile


class Dataset:
    """
    A Dataset object. Contains methods to process UV-Vis data.

    Attributes
    ----------
    name : string
        The name of the .KD file that the :class:`Dataset` was created from.
    cycle_time : int
        The cycle time in seconds from the experiment.
    all_spectra : :class:`pandas.DataFrame`
        All of the raw spectra in the :class:`Dataset`.
    time_traces : :class:`pandas.DataFrame`
        The time traces for the :class:`Dataset`. The number of time traces and
        their wavelengths are dictated by `time_trace_window` and
        `time_trace_interval`.
    specific_time_traces : :class:`pandas.DataFrame`
        Time traces for user-specified wavelengths.
    outliers : list
        The time indices of outlier spectra. See :meth:`find_outliers()`
        for more information.
    baseline : :class:`pandas.Series`
       The baseline of the summed :attr:`time_traces`. See :meth:`find_outliers()`
       for more information.
    cleaned_spectra : :class:`pandas.DataFrame`
        The spectra with :attr:`outliers` removed.
    trimmed_spectra : :class:`pandas.DataFrame`
        The spectra that fall within the given time range.
    sliced_spectra : :class:`pandas.DataFrame`
        The selected spectra slices.

    """

    def __init__(self, path, trim=None, slicing=None, outlier_threshold=0.1,
                 baseline_lambda=10, baseline_tolerance=0.1,
                 low_signal_window='narrow', time_trace_window=(300, 1060),
                 time_trace_interval=10, wavelengths=None, view_only=False):
        """
        Initialize a :class:`~uv_pro.process.Dataset`.

        Parses the .KD file at ``path`` and processes it to remove "bad"
        spectra (e.g. spectra collected when mixing the solution).

        Parameters
        ----------
        path : string
            A file path to a .KD file.
        trim : tuple-like or None, optional
            Select spectra within a given time range. The first value
            ``trim[0]`` is the time (in seconds) of the beginning of the time
            range, and the second value ``trim[1]`` is the end of the time range.
            Default value is None (no trimming).
        slicing : dict or None, optional
            Reduce the data down to a selection of slices. Data can be sliced linearly
            (equally-spaced slices) or exponentially (unequally-spaced). For linear
            (equally-spaced) slicing: ``{'mode': 'linear', 'slices': int}``.
            For exponential (unequally-spaced) slicing: ``{'mode': 'exponential',
            'coefficient': float, 'exponent': float}``.
        outlier_threshold : float, optional
            A value between 0 and 1 indicating the threshold by which spectra
            are considered outliers. Values closer to 0 produce more outliers,
            while values closer to 1 produce fewer outliers. The default value is 0.1.
        baseline_lambda : float, optional
            Set the smoothness of the baseline (for outlier detection). Higher values
            give smoother baselines. Try values between 0.001 and 10000. The
            default is 10.
        baseline_tolerance : float, optional
            Set the exit criteria for the baseline algorithm. Try values between
            0.001 and 10000. The default is 0.1. See :func:`pybaselines.whittaker.asls()`
            for more information.
        low_signal_window : "narrow" or "wide", optional
            Set the width of the low signal detection window (see
            :meth:`find_outliers()`). Set to wide if low signal outliers are
            affecting the baseline.
        time_trace_window : tuple-like or None, optional
            The range (min, max) of wavelengths (in nm) to get time traces for.
            The default is (300, 1060).
        time_trace_interval : int, optional
            The wavelength interval (in nm) between time traces.
            A smaller interval produces more time traces.
            For example, an interval of 20 would generate time traces like this:
            [window min, window min + 20, window min + 40, ..., window max - 20, window max].
            The default value is 10.
        wavelengths : list-like or None, optional
            A list of specific wavelengths to get time traces for. The default is None.
        view_only : True or False, optional
            Indicate whether data processing (cleaning and trimming) should be
            skipped. Default is False (cleaning and trimming are performed).

        Returns
        -------
        None.

        """
        self.path = path
        self.name = os.path.basename(self.path)
        self.trim = trim
        self.slicing = slicing
        self.low_signal_window = low_signal_window
        self.outlier_threshold = outlier_threshold
        self.baseline_lambda = baseline_lambda
        self.baseline_tolerance = baseline_tolerance
        self.time_trace_window = time_trace_window
        self.time_trace_interval = time_trace_interval
        self.wavelengths = wavelengths

        self._import_data()

        if not view_only:
            self._process_data()

    def _import_data(self):
        kd_file = KDFile(self.path)
        self.all_spectra = kd_file.spectra
        self.spectra_times = kd_file.spectra_times
        self.cycle_time = kd_file.cycle_time

    def _process_data(self):
        if len(self.all_spectra.columns) > 2:
            self.time_traces = self.get_time_traces(window=self.time_trace_window, interval=self.time_trace_interval)
            self.specific_time_traces = self.get_specific_time_traces(self.wavelengths)
            print('Finding outliers...')
            self.outliers = self.find_outliers()
            print(f'{len(self.outliers)} outliers detected.')

            print('Cleaning data...')
            self.cleaned_spectra = self.clean_data()

            if self.trim is None:
                self.trimmed_spectra = self.cleaned_spectra
            else:
                print('Trimming data...')
                self.trimmed_spectra = self.trim_data()

            if self.slicing is None:
                self.sliced_spectra = self.trimmed_spectra
            else:
                print('Slicing data...')
                self.sliced_spectra = self.slice_data()
            print('Success.')

    def get_time_traces(self, window=(300, 1060), interval=10):
        """
        Iterate through different wavelengths and get time traces.

        Time traces which saturate the detector due to high intensity are
        removed by checking if they have a median absorbance below 1.75 AU.
        The raw (un-normalized) time traces are returned.

        Parameters
        ----------
        window : tuple-like, optional
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
            A :class:`pandas.DataFrame` containing the raw time traces,
            where each column is a different wavelength.

        """
        all_time_traces = {}

        for wavelength in range(window[0], window[1] + 1, interval):
            time_trace = self.all_spectra.loc[wavelength]
            time_trace.index = pd.Index(self.spectra_times, name='Time (s)')

            # Check if the median absorbance of the time trace is below 1.75 AU.
            # This excludes saturated wavelengths.
            if time_trace.median() < 1.75:
                key = f'{wavelength} (nm)'
                all_time_traces[key] = time_trace

        return pd.DataFrame.from_dict(all_time_traces)

    def get_specific_time_traces(self, wavelengths, window=(190, 1100)):
        """
        Get time traces of specific wavelengths.

        Parameters
        ----------
        wavelengths: list-like or None
            A list of wavelengths to get time traces for.
        window : tuple-like, optional
            The range of wavelengths captured by the spectrometer.
            The default value is (190, 1100).

        Returns
        -------
        :class:`pandas.DataFrame` or None
            A :class:`pandas.DataFrame` containing the raw time traces,
            where each column is a different wavelength. Otherwise,
            returns None if no wavelengths are given or no time traces
            could be made.

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
                time_values = pd.Index(self.spectra_times, name='Time (s)')
                specific_time_traces = pd.DataFrame.from_dict(all_time_traces)
                specific_time_traces.set_index(time_values, inplace=True)
                return specific_time_traces
            else:
                return None

    def find_outliers(self):
        """
        Find outlier spectra.

        Detects outlier spectra using :attr:`time_traces`. Outliers typically
        occur when mixing or injecting solutions and result in big spikes or
        dips in the absorbance.

        Returns
        -------
        outliers : list
            A list containing the time indices of outlier spectra.

        """
        outliers = []
        low_signal_outliers = set()

        low_signal_outliers = self._find_low_signal_outliers()
        time_traces = self.time_traces.drop(low_signal_outliers)
        outliers.extend(low_signal_outliers)

        self._compute_baseline(time_traces)
        baselined_time_traces = time_traces.sum(1) - self.baseline

        baseline_outliers = self._find_baseline_outliers(baselined_time_traces)
        outliers.extend(baseline_outliers)

        return outliers

    def _find_low_signal_outliers(self):
        """
        Find outlier points with very low absorbance signal.

        Low signal outliers usually occur when the cuvette is removed from the
        instrument during the experiment.

        Returns
        -------
        low_signal_outliers : set
            A set of time indices where low signal outliers are found.

        """
        low_signal_outliers = set()
        low_signal_cutoff = len(self.time_traces.columns) * 0.1
        sorted_time_traces = self.time_traces.sum(1).sort_values()

        i = 0
        if self.low_signal_window.lower() == 'wide':
            while sorted_time_traces.iloc[i] < low_signal_cutoff:
                outlier_index = self.time_traces.index.get_loc(sorted_time_traces.index[i])
                low_signal_outliers.add(self.time_traces.index[outlier_index])
                low_signal_outliers.add(self.time_traces.index[outlier_index + 1])
                low_signal_outliers.add(self.time_traces.index[outlier_index - 1])
                i += 1
        else:
            while sorted_time_traces.iloc[i] < low_signal_cutoff:
                outlier_index = self.time_traces.index.get_loc(sorted_time_traces.index[i])
                low_signal_outliers.add(self.time_traces.index[outlier_index])
                i += 1

        return low_signal_outliers

    def _compute_baseline(self, time_traces):
        # Smoothed baseline of the summed time traces (lam=smoothing factor, tol=exit criteria)
        self.baseline = pd.Series(whittaker.asls(
            time_traces.sum(1),
            lam=self.baseline_lambda,
            tol=self.baseline_tolerance)[0],
            time_traces.sum(1).index)

    def _find_baseline_outliers(self, baselined_time_traces):
        """
        Faster method to find outliers using sort_values().

        Parameters
        ----------
        baselined_time_traces : :class:`pandas.core.series.Series`
            The summed time traces after subtracting the
            :attr:`~uv_pro.process.Dataset.baseline`

        Returns
        -------
        baseline_outliers : set
            A set of time indices where baseline outliers are located.

        """
        baseline_outliers = set()

        i = 0
        sorted_baselined_time_traces = abs(baselined_time_traces).sort_values(ascending=False)
        while sorted_baselined_time_traces.iloc[i] / baselined_time_traces.max() > self.outlier_threshold:
            baseline_outliers.add(sorted_baselined_time_traces.index[i])
            i += 1

        return baseline_outliers

    def clean_data(self):
        """
        Remove outliers from :attr:`all_spectra`.

        Returns
        -------
        cleaned_spectra : :class:`pandas.DataFrame`
            A :class:`pandas.DataFrame` containing the spectra
            with outlier spectra removed.

        """
        column_numbers = [x for x in range(self.all_spectra.shape[1])]
        outlier_indices = [self.time_traces.index.get_loc(outlier) for outlier in self.outliers]
        [column_numbers.remove(outlier) for outlier in outlier_indices]
        cleaned_spectra = self.all_spectra.iloc[:, column_numbers]

        return cleaned_spectra

    def trim_data(self):
        """
        Trim the data to keep a portion within a given time range.

        Returns
        -------
        trimmed_spectra : :class:`pandas.DataFrame`
            A :class:`pandas.DataFrame` containing the spectra within
            the time range given by :attr:`uv_pro.process.Dataset.trim`.

        """
        trimmed_spectra = []
        start, end = self._check_trim_values()
        trimmed_spectra = self.cleaned_spectra.iloc[:, start // self.cycle_time:end // self.cycle_time + 1]

        print(f'Selecting {len(trimmed_spectra.columns)} spectra from {start}',
              f'seconds to {end} seconds...')

        return trimmed_spectra

    def _check_trim_values(self):
        start = self.trim[0]
        end = self.trim[1]

        if start >= end:
            start = self.trim[1]
            end = self.trim[0]
        if start < self.cycle_time:
            start = 0
        if end > len(self.all_spectra.columns) * self.cycle_time:
            end = len(self.all_spectra.columns) * self.cycle_time

        return start, end

    def slice_data(self):
        """
        Reduce the data down to a selection of slices.

        Slicing can be performed linearly (equally-spaced) or exponentially
        (unequally-spaced). Linear slicing requires a single integer
        (e.g., a value of 10 will produce 10 equally-spaced slices).
        Exponential slicing requies two floats, a coefficient and an exponent.
        Exponential slicing uses the equation y = coefficient*x^exponent + 1
        to find the indexes of slices to keep.

        Slicing behavior is determined by :attr:`uv_pro.process.Dataset.slicing`.
        For linear (equally-spaced) slicing: ``{'mode': 'linear', 'slices': int}``.
        For exponential (unequally-spaced) slicing: ``{'mode': 'exponential',
        'coefficient': float, 'exponent': float}``.

        Returns
        -------
        sliced_spectra : :class:`pandas.DataFrame`
            A :class:`pandas.DataFrame` containing the spectra slices
            given by :attr:`uv_pro.process.Dataset.slicing`.
        """
        sliced_spectra = []
        if self.slicing['mode'] == 'exponential':
            slices = []
            coefficient = self.slicing['coefficient']
            exponent = self.slicing['exponent']
            i = 1

            while sum(slices) < len(self.trimmed_spectra.columns):
                slices.append(round(coefficient * i**exponent + 1))
                i += 1
            while sum(slices) >= len(self.trimmed_spectra.columns):
                slices.pop()

            columns_to_keep = [0]
            for index, value in enumerate(slices):
                columns_to_keep.append(columns_to_keep[index] + value)
            sliced_spectra = self.trimmed_spectra.iloc[:, columns_to_keep]

        else:
            step = len(self.trimmed_spectra.columns) // int(self.slicing['slices'])
            columns_to_keep = list(range(0, len(self.trimmed_spectra.columns), step))
            sliced_spectra = self.trimmed_spectra.iloc[:, columns_to_keep]

        return sliced_spectra

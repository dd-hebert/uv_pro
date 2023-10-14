"""
Process UV-Vis Data.

Tools for processing UV-Vis data files (.KD or .csv formats) exported from
the Agilent 845x UV-Vis Chemstation software.

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
        The name of the .KD file or Folder (when using .csv format) that the
        :class:`Dataset` was created from.
    cycle_time : int
        The cycle time in seconds from the experiment.
    all_spectra : :class:`pandas.DataFrame`
        All of the raw spectra in the :class:`Dataset`.
    time_traces : :class:`pandas.DataFrame`
        The time traces for the :class:`Dataset`.
    specific_time_traces : :class:`pandas.DataFrame`
        Time traces for user-specified wavelengths.
    outliers : list
        The time values of outlier spectra. See :meth:`find_outliers()`
        for more information.
    baseline : :class:`pandas.Series`
       The baseline of the summed :attr:`time_traces`. See :meth:`find_outliers()`
       for more information.
    cleaned_spectra : :class:`pandas.DataFrame`
        The :class:`Dataset`'s spectra with :attr:`outliers` removed.
    trimmed_spectra : :class:`pandas.DataFrame`
        The trimmed portion of the :class:`Dataset`'s :attr:`cleaned_spectra`.

    """

    def __init__(self, path, trim=None, outlier_threshold=0.1,
                 baseline_lambda=10, baseline_tolerance=0.1,
                 low_signal_window='narrow', time_trace_window=(300, 1060),
                 time_trace_interval=10, wavelengths=None, view_only=False):
        """
        Initialize a :class:`~uv_pro.process.Dataset`.

        Imports the specified data at ``path`` and processes it to remove bad
        spectra (e.g. spectra collected when mixing the solution).

        Parameters
        ----------
        path : string
            A file path to a .KD file or a folder containing .csv data files
            containing the data to be processed.
        trim : list-like or None, optional
            Select spectra within a given time range. The first value
            ``trim[0]`` is the time (in seconds) of the first spectrum
            to select. The second value ``trim[1]`` is the time (in
            seconds) of the last spectrum to select. Default value is None (no
            trimming).
        outlier_threshold : float, optional
            A value between 0 and 1 indicating the threshold by which spectra
            are considered outliers. Values closer to 0 result in higher
            sensitivity (more outliers). Values closer to 1 result in lower
            sensitivity (fewer outliers). The default value is 0.1.
        baseline_lambda : float, optional
            Set the smoothness of the baseline when cleaning data. Higher values
            give smoother baselines. Try values between 0.001 and 10000. The
            default is 10.
        baseline_tolerance : float, optional
            Set the exit criteria for the baseline algorithm. Try values between
            0.001 and 10000. The default is 0.1. See :func:`pybaselines.whittaker.asls()`
            for more information.
        low_signal_window : "narrow" or "wide", optional
            Set the width of the low signal detection window (see
            :meth:`find_outliers()`). When set to ``"wide"``, the data points
            before and after the low signal outlier(s) are also considered
            outliers. The default is ``"narrow"``, meaning only the low signal
            outlier(s) are considered outliers.
        time_trace_window : list-like or None, optional
            The wavelength range (min, max) in nm for time traces used in outlier
            detection. The default is (300, 1060).
        time_trace_interval : int, optional
            The wavelength interval (in nm) at which time traces are created.
            A smaller interval means more frequent data points.
            For example, an interval of 20 would generate time traces like this:
            [window min, window min + 20, window min + 40, ..., window max - 20, window max].
            The default value is 10.
        wavelengths : list-like or None, optional
            A list of specific wavelengths to create time traces for. The default is None.
        view_only : True or False, optional
            Indicate whether data processing (cleaning and trimming) should be
            performed. Default is False (cleaning and trimming are performed).

        Returns
        -------
        None.

        """
        self.path = path
        self.name = os.path.basename(self.path)
        self.trim = trim
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
            print('Success.')

            if self.trim is None:
                self.trimmed_spectra = self.cleaned_spectra
            else:
                print('Trimming data...')
                self.trimmed_spectra = self.trim_data()

    def get_time_traces(self, window=(300, 1060), interval=10):
        """
        Iterate through different wavelengths and builds time traces.

        Time traces which have poor signal-to-noise and/or saturate the detector
        due to high intensity are removed by checking if the mean of their normalized
        absorbance is above 0.5. The raw (un-normalized) time traces are returned.

        Parameters
        ----------
        window : list-like, optional
            Describes the window of wavelengths to construct time traces of.
            The first value ``window[0]`` gives the minimum wavelength, and
            the second value ``window[1]`` gives the maximum wavelength. The
            default value is (300, 1060).
        interval : int, optional
            Describes the interval in nm to construct time traces. A ``window``
            of (300, 1000) with an ``interval`` of 10 will build time traces
            from [300, 310, 320, 330, 340,... ..., 970, 980, 990] nm. The
            default value is 10 (nm).

        Returns
        -------
        :class:`pandas.DataFrame`
            Returns a :class:`pandas.DataFrame` object containing the raw
            time traces, where each column is a different wavelength.

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
            A list of wavelengths to create time traces for.
        window : list-like, optional
            Describes the window of wavelengths to construct time traces of.
            The first value ``window[0]`` gives the minimum wavelength, and
            the second value ``window[1]`` gives the maximum wavelength. The
            default value is (190, 1100).

        Returns
        -------
        :class:`pandas.DataFrame` or None
            Returns a :class:`pandas.DataFrame` object containing the raw
            time traces, where each column is a different wavelength. Returns
            None if no wavelengths are given or no time traces could be made.

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
            A list containing the time values of outlier spectra.

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

        Returns
        -------
        low_signal_outliers : set
            A set of time values where low signal outliers are found.

        """
        low_signal_outliers = set()
        low_signal_cutoff = len(self.time_traces.columns) * 0.1
        sorted_time_traces = self.time_traces.sum(1).sort_values()

        i = 0
        if self.low_signal_window.lower() == 'wide':
            while sorted_time_traces[sorted_time_traces.index[i]] < low_signal_cutoff:
                low_signal_outliers.add(sorted_time_traces.index[i] - 1)
                low_signal_outliers.add(sorted_time_traces.index[i])
                low_signal_outliers.add(sorted_time_traces.index[i] + 1)
                i += 1
        else:
            while sorted_time_traces[sorted_time_traces.index[i]] < low_signal_cutoff:
                low_signal_outliers.add(sorted_time_traces.index[i])
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
            A set of time values where baseline outliers are located.

        """
        baseline_outliers = set()

        i = 0
        sorted_baselined_time_traces = abs(baselined_time_traces).sort_values(ascending=False)
        while sorted_baselined_time_traces[sorted_baselined_time_traces.index[i]] / baselined_time_traces.max() > self.outlier_threshold:
            baseline_outliers.add(sorted_baselined_time_traces.index[i])
            i += 1

        return baseline_outliers

    def clean_data(self):
        """
        Remove outliers from :attr:`all_spectra`.

        Returns
        -------
        cleaned_spectra : :class:`pandas.DataFrame`
            Returns a :class:`pandas.DataFrame` object containing the
            cleaned spectra (with outlier spectra removed).

        """
        column_numbers = [x for x in range(self.all_spectra.shape[1])]
        outlier_indices = [self.time_traces.index.get_loc(outlier) for outlier in self.outliers]
        [column_numbers.remove(outlier) for outlier in outlier_indices]

        cleaned_spectra = self.all_spectra.iloc[:, column_numbers]

        return cleaned_spectra

    def trim_data(self):
        """
        Trim the data to keep only a specific portion.

        Returns
        -------
        trimmed_spectra : :class:`pandas.DataFrame`
            A :class:`pandas.DataFrame` object containing the
            spectra specified by :attr:`uv_pro.process.Dataset.trim`.

        """
        trimmed_spectra = []

        start, end = self._check_trim_values()

        # Choose spectra from {start} time to {end_time} time.
        trimmed_spectra = self.cleaned_spectra.iloc[:, start // self.cycle_time:end // self.cycle_time + 1]

        print(f'Selecting {len(trimmed_spectra.columns)} spectra from {start}',
              f'seconds to {end} seconds...')

        return trimmed_spectra

    def _check_trim_values(self):
        start = self.trim[0]
        end = self.trim[1]

        if start >= end:
            raise Exception('Data trim start should be before the end.')

        if start < self.cycle_time:
            start = 0

        if end > len(self.all_spectra.columns) * self.cycle_time:
            end = len(self.all_spectra.columns) * self.cycle_time

        return start, end

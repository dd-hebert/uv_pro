"""
Tools for processing UV-Vis data files (.KD or .csv formats) exported from
the Agilent 845x UV-Vis Chemstation software.

"""

import os
import pandas as pd
import numpy as np
from pybaselines import whittaker
from uv_pro.file_io import from_kd
from uv_pro.file_io import from_csv


class Dataset:
    """
    A Dataset object. Contains methods to process UV-Vis data.

    Attributes
    ----------
    name : string
        The name of the .KD file or Folder (when using .csv format) that the
        :class:`Dataset` was created from.
    units : string
        Either ``"seconds"`` or ``"index"``. Denotes how ``trim`` will be
        interpretted during data trimming. Default is "index". A :class:`Dataset`
        created from .csv files will require the ``cycle_time`` to be provided
        in order to use ``"seconds"`` to trim data.
    all_spectra : list of :class:`pandas.DataFrame` objects
        All of the raw spectra in the :class:`Dataset`.
    time_traces : :class:`pandas.DataFrame`
        The time traces for the :class:`Dataset`.
    outliers : list
        The indices of outlier spectra. See :meth:`find_outliers()`
        for more information.
    baseline : :class:`pandas.Series`
       The baseline of the summed :attr:`time_traces`. See :meth:`find_outliers()`
       for more information.
    cleaned_spectra : list of :class:`pandas.DataFrame` objects
        The :class:`Dataset`'s spectra with :attr:`outliers` removed.
    trimmed_spectra : list of :class:`pandas.DataFrame` objects
        The trimmed portion of the :class:`Dataset`'s :attr:`cleaned_spectra`.

    """

    def __init__(self, path, cycle_time=None, trim=None, use_seconds=False,
                 outlier_threshold=0.1, baseline_lambda=10, baseline_tolerance=0.1,
                 low_signal_window='narrow', view_only=False):
        """
        Initialize a :class:`~uv_pro.process.Dataset`.

        Imports the specified data at ``path`` and processes it to remove bad
        spectra (e.g. spectra collected when mixing the solution).

        Parameters
        ----------
        path : string
            A file path to a .KD file or a folder containing .csv data files
            containing the data to be processed.
        cycle_time : int or None, optional
            The cycle time in seconds from the experiment. Only required if
            using time (seconds) to trim datasets imported from .csv files. The
            cycle time is automatically detected when creating a dataset from a
            .KD file. Defaults to 1 (same as using indexes).

            Important
            ---------
                Only experiments with a constant cycle time are currently
                supported.

        trim : list-like or None, optional
            Select a specific portion of a dataset of spectra. The first value
            ``trim[0]`` is the index or time (in seconds) of the first spectrum
            to select. The second value ``trim[1]`` is the index or time (in
            seconds) of the last spectrum to import. Default value is None (no
            trimming).
        use_seconds : True or False, optional
            Use time (seconds) instead of spectrum #'s when trimming data.
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
        view_only : True or False, optional
            Indicate whether data processing (cleaning and trimming) should be
            performed. Default is False (cleaning and trimming are performed).

        Returns
        -------
        None.

        """
        self.path = path  # string
        self.name = os.path.basename(self.path)  # string
        self.cycle_time = cycle_time  # int
        self.trim = trim  # list-like
        self.low_signal_window = low_signal_window  # string
        self.outlier_threshold = outlier_threshold  # float
        self.baseline_lambda = baseline_lambda  # float
        self.baseline_tolerance = baseline_tolerance  # float

        if use_seconds is True:
            self.units = 'seconds'
        else:
            self.units = 'index'

        # Get data and cycle time
        if self.name.endswith('.KD'):
            self.all_spectra, self.cycle_time = from_kd(self.path)  # List of pd DataFrames
        else:
            if self.cycle_time is None:
                self.cycle_time = 1
                self.units = 'index'
            self.all_spectra = from_csv(self.path)  # List of pd DataFrames

        print(f'{len(self.all_spectra)} spectra successfully imported from: {self.name}.', end='\n')

        # Clean and trim spectra
        if view_only is False:
            if len(self.all_spectra) > 2:
                self.time_traces = self.get_time_traces()  # pd DataFrame

                print('Finding outliers...')
                self.outliers = self.find_outliers()  # List
                print(f'{len(self.outliers)} outliers detected.')

                print('Cleaning data...')
                self.cleaned_spectra = self.clean_data()  # List of pd DataFrames
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
            Returns a :class:`pandas.DataFrame` objects. containing the raw
            time traces, where each column is a different wavelength.

        """
        all_time_traces = {}
        min_wavelength = window[0]  # Minimum time trace wavelength (in nm)
        max_wavelength = window[1]  # Maximum time trace wavelength (in nm)

        for wavelength in range(min_wavelength, max_wavelength, interval):
            time_trace = []

            # Append the absorbance at specific {wavelength} to list.
            # {wavelength}-190 because the instrument measures from 190 nm.
            for _, spectrum in enumerate(self.all_spectra):
                time_trace.append(spectrum['Absorbance (AU)'][wavelength-190])

            # Check if the median absorbance of the time trace is below 1.75 AU.
            # This excludes saturated wavelengths.
            if pd.Series(time_trace).median() < 1.75:
                key = f'{wavelength} (nm)'
                all_time_traces[key] = time_trace

        return pd.DataFrame.from_dict(all_time_traces)

    def find_outliers(self):
        """
        Find outlier spectra.

        Detects outlier spectra using :attr:`time_traces`. Outliers typically
        occur when mixing or injecting solutions and result in big spikes or
        dips in the absorbance.

        How It Works
        ------------
        First, the time traces in :attr:`time_traces` are summed to give a
        **summed time trace** with improved signal to noise, and **low signal
        outliers** are removed (spectra taken when the cuvette has been removed
        from the spectrometer). From the remaining spectra, a smoothed
        baseline is found (see :func:`pybaselines.whittaker.asls()`). The baseline
        is subtracted from the **summed time trace** to create a **baselined time
        trace**. The **baselined time trace** is normalized and spectra with absorbance
        above the ``outlier_threshold`` are recorded as :attr:`outliers`.

        Returns
        -------
        outliers : list
            A list containing the indices of outlier spectra.

        """
        outliers = []
        low_signal_outliers = set()
        baseline_outliers = set()
        low_signal_cutoff = len(self.time_traces.columns) * 0.1
        sorted_time_traces = self.time_traces.sum(1).sort_values()

        def find_low_signal_outliers():
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

        low_signal_outliers = find_low_signal_outliers()
        time_traces = self.time_traces.drop(low_signal_outliers)
        outliers.extend(low_signal_outliers)

        # Smoothed baseline of the summed time traces (lam=smoothing factor, tol=exit criteria)
        self.baseline = pd.Series(whittaker.asls(
                time_traces.sum(1),
                lam=self.baseline_lambda,
                tol=self.baseline_tolerance)[0],
            time_traces.sum(1).index)

        # Subtract baseline from summed time traces to get baselined time trace
        baselined_time_traces = time_traces.sum(1) - self.baseline

        # def find_baseline_outliers_envelope():
        #     # New method to filter outliers using an envelope
        #     upper_outlier_bound = self.baseline + self.outlier_threshold
        #     lower_outlier_bound = self.baseline - self.outlier_threshold
        #     for i, _ in time_traces.sum(1).items():
        #         if time_traces.sum(1)[i] > upper_outlier_bound[i] or time_traces.sum(1)[i] < lower_outlier_bound[i]:
        #             baseline_outliers.add(i)

        #     return baseline_outliers

        # def find_baseline_outliers_classic():
        #     # Classic method to filter outliers using the normalized baselined time traces.
        #     # Slow for large Datasets, but works.
        #     for i, _ in baselined_time_traces.items():
        #         if abs(baselined_time_traces[i] / baselined_time_traces.max()) > self.outlier_threshold:
        #             baseline_outliers.add(i)

        #     return baseline_outliers

        def find_baseline_outliers():
            # New faster method to check for outliers using sort_values()
            i = 0
            sorted_baselined_time_traces = abs(baselined_time_traces).sort_values(ascending=False)
            while sorted_baselined_time_traces[sorted_baselined_time_traces.index[i]] / baselined_time_traces.max() > self.outlier_threshold:
                baseline_outliers.add(sorted_baselined_time_traces.index[i])
                i += 1

            return baseline_outliers

        baseline_outliers = find_baseline_outliers()
        outliers.extend(baseline_outliers)

        return np.flip(np.sort(outliers))

    def clean_data_simple(self, wavelength, tolerance):
        """
        Clean data by removing outliers.

        A simple method to clean :attr:`all_spectra` using the rolling median of a time
        trace at ``wavelength``. If a point of the time trace is greater than its rolling
        median + ``tolerance``, that point (spectrum) is rejected.

        Tip
        ---
            ``tolerance`` may require some trial and error to get a good result.

        Parameters
        ----------
        wavelength : int
            Integer wavelength of a time trace found in :attr:`time_traces`.
        tolerance : float
            Changes the sensitivity of the rejection algorithm. A larger tolerance
            will reject fewer points, while a smaller tolernace will reject more.

        Returns
        -------
        cleaned_spectra : list of :class:`pandas.DataFrame` objects.
            Returns a list of :class:`pandas.DataFrame` objects containing the
            spectra which fell within the given ``tolerance``. Ideally, most
            outlier spectra will be removed.

        """
        cleaned_spectra = []
        time_trace = self.time_traces[f'{wavelength} (nm)']
        rolling_median = pd.Series(self.time_traces[f'{wavelength} (nm)']).rolling(3).median()

        for i, spectrum in enumerate(self.all_spectra):
            if abs(time_trace[i] - rolling_median[i]) < tolerance:
                cleaned_spectra.append(spectrum)
            else:
                pass

        return cleaned_spectra

    def clean_data(self):
        """
        Generate a list of cleaned spectra by popping outliers from :attr:`all_spectra`.

        Returns
        -------
        cleaned_spectra : list of :class:`pandas.DataFrame` objects.
            Returns a list of :class:`pandas.DataFrame` objects containing the
            cleaned spectra (with outlier spectra removed).

        """
        cleaned_spectra = []

        for i, _ in enumerate(self.all_spectra):
            cleaned_spectra.append(self.all_spectra[i])

        for outlier in self.outliers:
            cleaned_spectra.pop(outlier)

        return cleaned_spectra

    def trim_data(self, **kwargs):
        """
        Trim the data to select a specific portion.

        Trims the data by removing spectra before ``trim[0]`` and after
        ``trim[1]``.

        Keyword Arguments
        -----------------
        mode : string
            Specify whether time (seconds) or indexes are used when trimming data.
            By default, indexes are used. For trimming a :class:`Dataset` from .csv
            files, seconds can only be used if a :attr:`cycle_time` has been provided
            (see :meth:`__init__()`).

        Returns
        -------
        trimmed_spectra : list of :class:`pandas.DataFrame` objects.
            Returns a list of :class:`pandas.DataFrame` objects containing the
            chosen spectra between ``trim[0]`` and ``trim[1]``.

        """
        trimmed_spectra = []
        start = self.trim[0]
        end = self.trim[1]

        # Check if {start} is before {end}.
        if start >= end:
            raise Exception('Data trim start should be before the end.')

        mode = kwargs.get('mode', self.units)

        if mode == 'seconds':
            # Change {start} time if less than cycle time.
            if start < self.cycle_time:
                start = self.cycle_time

            # Fix {end} time if it is after the last spectrum.
            if end > len(self.all_spectra) * self.cycle_time:
                end = len(self.all_spectra) * self.cycle_time

            # Choose spectra from {start} time to {end_time} time.
            trimmed_spectra = self.cleaned_spectra[start // self.cycle_time:end // self.cycle_time + 1]

            print(f'Selecting {len(trimmed_spectra)} spectra from {start}',
                  f'seconds to {end} seconds...')

        elif mode == 'index':
            # Fix {end} if it is after the last spectrum.
            if end > len(self.all_spectra):
                end = len(self.all_spectra)

            # Choose spectra from {start} to {end}.
            trimmed_spectra = self.cleaned_spectra[start:end + 1]

            print(f'Selecting {len(trimmed_spectra)} spectra from spectrum {start}',
                  f'to spectrum {end}...')

        return trimmed_spectra

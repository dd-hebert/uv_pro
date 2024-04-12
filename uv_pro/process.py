"""
Process UV-Vis Data.

Tools for processing UV-Vis data files (.KD format) from the Agilent 845x
UV-Vis Chemstation software.

@author: David Hebert
"""

import os
import pandas as pd
from uv_pro.io.import_kd import KDFile
from uv_pro.outliers import OutlierFinder
from uv_pro.fitting import fit_exponential


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
    outlier_finder : :class:`uv_pro.outliers.OutlierFinder`
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

    def __init__(self, path, trim=None, slicing=None, fitting=False,
                 outlier_threshold=0.1, baseline_lambda=10, baseline_tolerance=0.1,
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
            Reduce the data down to a selection of slices. Slices can be taken in
            equally-spaced or unequally-spaced (gradient) intervals. For equal
            slicing: ``{'mode': 'equal', 'slices': int}``. For gradient slicing:
            ``{'mode': 'gradient', 'coefficient': float, 'exponent': float}``.
        outlier_threshold : float, optional
            A value between 0 and 1 indicating the threshold by which spectra
            are considered outliers. Values closer to 0 produce more outliers,
            while values closer to 1 produce fewer outliers. Values >>1 produce no outliers.
            The default value is 0.1.
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
        self.fitting = fitting
        self.outlier_finder = OutlierFinder(
            outlier_threshold=outlier_threshold,
            low_signal_window=low_signal_window,
            baseline_lambda=baseline_lambda,
            baseline_tolerance=baseline_tolerance)
        self.time_trace_window = time_trace_window
        self.time_trace_interval = time_trace_interval
        self.wavelengths = wavelengths

        self._import_data()

        if not view_only:
            self._process_data()

    def _import_data(self):
        print(f'\033[1m* Reading .KD file {os.path.basename(self.path)}...\033[22m')
        kd_file = KDFile(self.path)
        self.all_spectra = kd_file.spectra
        self.spectra_times = kd_file.spectra_times
        self.cycle_time = kd_file.cycle_time
        print(f'Spectra found: {len(self.all_spectra.columns)}')
        print(f'Cycle time (s): {self.cycle_time}')

    def _process_data(self):
        if len(self.all_spectra.columns) > 2:
            self.time_traces = self.get_time_traces(
                window=self.time_trace_window, interval=self.time_trace_interval)
            self.specific_time_traces = self.get_specific_time_traces(self.wavelengths)

            print('\033[1m* Finding outliers...\033[22m')
            self.outliers, self.baseline = self.outlier_finder.find_outliers(self.time_traces)
            print(f'Outliers found: {len(self.outliers)}')

            print('\033[1m* Cleaning data...\033[22m')
            self.cleaned_spectra = self.clean_data()

            if self.trim is None:
                self.trimmed_spectra = self.cleaned_spectra
                self.trimmed_traces = self.specific_time_traces
            else:
                print('\033[1m* Trimming data...\033[22m')
                self.trimmed_spectra = self.trim_data()
                self.trimmed_traces = self.trim_traces()

            if self.slicing is None:
                self.sliced_spectra = self.trimmed_spectra
            else:
                print('\033[1m* Slicing data...\033[22m')
                self.sliced_spectra = self.slice_data()

            if self.fitting is True and self.trimmed_traces is not None:
                print('\033[1m* Fitting exponential...\033[22m')
                self.fit = fit_exponential(self.trimmed_traces)
                if self.fit is not None:
                    self._print_fit()
            else:
                self.fit = None

            print('\033[32mSuccess.\033[37m')

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
            A :class:`pandas.DataFrame` containing the raw time traces,
            where each column is a different wavelength.
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
        print(f'Keeping {len(trimmed_spectra.columns)} spectra from {start}',
              f'to {end} seconds...')
        return trimmed_spectra

    def trim_traces(self):
        """
        Trim the specified time traces to keep a portion within a given time range.

        Returns
        -------
        :class:`pandas.DataFrame` or None
            A :class:`pandas.DataFrame` containing the trimmed time traces,
            where each column is a different wavelength.
        """
        if self.specific_time_traces is not None:
            trim_start = self.trim[0] // self.cycle_time
            trim_end = self.trim[1] // self.cycle_time + 1
            return self.specific_time_traces.drop(self.outliers).iloc[trim_start:trim_end]
        return None

    def _check_trim_values(self) -> tuple:
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

    def _print_fit(self) -> None:
        # TODO use string formatting to make table prettier
        equation = 'f(t) = abs_f + (abs_0 - abs_f) * exp(-kobs * t)'
        print('\033[3m{}\033[23m'.format(equation))
        print('\n' + '┌' + '─' * 94 + '┐')
        table_headings = '│ \033[1m{}\t{:^18}\t{:^18}\t{:^18}\t{:^6}\033[22m │'
        print(table_headings.format('Wavelength', 'abs_0', 'abs_f', 'kobs', 'r2'))
        print('├' + '─' * 94 + '┤')
        for wavelength, fit in self.fit.items():
            abs_0 = '{:+.5f} ± {:.5f}'.format(fit['popt'][0], fit['perr'][0])
            abs_f = '{:+.5f} ± {:.5f}'.format(fit['popt'][1], fit['perr'][1])
            kobs = '\033[36m{:.2e} ± {:.2e}\033[0m'.format(fit['popt'][2], fit['perr'][2])
            r2 = '\033[36m{:.4f}\033[0m'.format(fit['r2'])
            print('│ {:>10}\t{}\t{}\t{}\t{} │'.format(wavelength, abs_0, abs_f, kobs, r2))
        print('└' + '─' * 94 + '┘')
        print('')

    def slice_data(self):
        """
        Reduce the data down to a selection of slices.

        Slices can be taken at equally-spaced or unequally-spaced
        (gradient) intervals. Equal slicing requires a single integer
        (e.g., a value of 10 will produce 10 equally-spaced slices).
        Gradient slicing requies two floats, a coefficient and an exponent.
        For gradient slicing, the step size between slices is calculated
        by the equation step_size = [coefficient*x^exponent + 1].

        Slicing behavior is determined by :attr:`uv_pro.process.Dataset.slicing`.
        For equal slicing: ``{'mode': 'equal', 'slices': int}``.
        For gradient (unequally-spaced) slicing: ``{'mode': 'gradient',
        'coefficient': float, 'exponent': float}``.

        Returns
        -------
        sliced_spectra : :class:`pandas.DataFrame`
            A :class:`pandas.DataFrame` containing the spectra slices
            given by :attr:`uv_pro.process.Dataset.slicing`.
        """
        sliced_spectra = []
        if self.slicing['mode'] == 'gradient':
            sliced_spectra = self._gradient_slicing()
            slicing_args = '\n'.join([f'Coefficient: {self.slicing['coefficient']}',
                                      f'Exponent: {self.slicing['exponent']}'])
        else:
            sliced_spectra = self._equal_slicing()
            slicing_args = f'Slices: {len(sliced_spectra.columns)}'
        print(f'Mode: {self.slicing['mode']}')
        print(slicing_args)
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
        step = len(self.trimmed_spectra.columns) // int(self.slicing['slices'])
        if step == 0:
            step = 1
        columns_to_keep = list(range(0, len(self.trimmed_spectra.columns), step))
        return self.trimmed_spectra.iloc[:, columns_to_keep]

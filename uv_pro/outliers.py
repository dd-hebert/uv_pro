import pandas as pd
from pybaselines import whittaker


# TODO: make baseline and outliers attribute of this class
class OutlierFinder:
    """
    An OutlierFinder object. Contains methods for outlier detection.
    """

    def __init__(self, outlier_threshold: float, low_signal_window: str,
                 baseline_lambda: float, baseline_tolerance: float):
        """
        Initialize an :class:`~uv_pro.outliers.OutlierFinder` object.

        Parameters
        ----------
        outlier_threshold : float
            The outlier threshold, values closer to 0 produce more outliers
            while values closer to 1 produce fewer outliers. A value >>1 will
            produce no outliers.
        low_signal_window : str
            The width of the low signal outlier window. Either 'wide' or 'narrow'.
        baseline_lambda : float
            The smoothness of the baseline. Larger numbers result in a smoother
            baseline. Try values between 0.001 and 10000.
        baseline_tolerance : float
            Set the exit criteria for the baseline algorithm. Try values between
            0.001 and 10000. See :func:`pybaselines.whittaker.asls()` for more
            information.
        """
        self.outlier_threshold = outlier_threshold
        self.low_signal_window = low_signal_window
        self.baseline_lambda = baseline_lambda
        self.baseline_tolerance = baseline_tolerance

    def find_outliers(self, time_traces: pd.DataFrame):
        """
        Find outlier spectra.

        Detects outlier spectra from the given time traces. Outliers typically
        occur when mixing or injecting solutions and result in big spikes or
        dips in the absorbance.

        Parameters
        ----------
        time_traces : pd.DataFrame
            Time traces to find outliers with.

        Returns
        -------
        outliers : list
            A list containing the time indices of outlier spectra.
        """
        outliers = []
        low_signal_outliers = self.find_low_signal_outliers(time_traces)
        time_traces = time_traces.drop(low_signal_outliers)

        baseline = self.compute_baseline(time_traces)
        baselined_time_traces = time_traces.sum(1) - baseline
        baseline_outliers = self.find_baseline_outliers(baselined_time_traces)

        outliers.extend(low_signal_outliers)
        outliers.extend(baseline_outliers)
        return outliers, baseline

    def find_low_signal_outliers(self, time_traces: pd.DataFrame) -> set[int]:
        """
        Detect points in time traces with very low total absorbance.

        Low signal outliers usually occur when the cuvette is removed
        from the instrument during data collection, resulting in an
        abrupt 'valley' in the time trace. It is important to remove
        these outliers as the baseline fitting algorithm is greatly
        affected by their presence.

        Parameters
        ----------
        time_traces : pd.DataFrame
            The time traces to be checked for low signal outliers.

        Returns
        -------
        low_signal_outliers : set
            A set of outlier indexes.
        """
        low_signal_outliers = set()
        low_signal_cutoff = len(time_traces.columns) * 0.1
        sorted_time_traces = time_traces.sum(1).sort_values()

        i = 0
        while sorted_time_traces.iloc[i] < low_signal_cutoff:
            outlier_index = time_traces.index.get_loc(sorted_time_traces.index[i])
            low_signal_outliers.add(time_traces.index[outlier_index])
            i += 1
        if self.low_signal_window.lower() == 'wide':
            neighboring_outliers = (
                [time_traces.index[time_traces.index.get_loc(outlier) - 1]
                 for outlier in low_signal_outliers]
                + [time_traces.index[time_traces.index.get_loc(outlier) + 1]
                   for outlier in low_signal_outliers])
            low_signal_outliers.update(neighboring_outliers)
        return low_signal_outliers

    def compute_baseline(self, time_traces: pd.DataFrame) -> pd.Series:
        # lam=smoothing factor, tol=exit criteria
        return pd.Series(
            whittaker.asls(
                time_traces.sum(1),
                lam=self.baseline_lambda,
                tol=self.baseline_tolerance)[0],
            time_traces.sum(1).index)

    def find_baseline_outliers(self, baselined_time_traces: pd.DataFrame) -> set:
        max_value = baselined_time_traces.abs().max()
        outliers = baselined_time_traces.abs() / max_value > self.outlier_threshold
        return set(outliers[outliers].index)

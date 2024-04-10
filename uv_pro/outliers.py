import pandas as pd
from pybaselines import whittaker


def find_outliers(time_traces, outlier_threshold,
                  low_signal_window, baseline_lambda, baseline_tolerance):
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

    low_signal_outliers = find_low_signal_outliers(time_traces, low_signal_window)
    time_traces = time_traces.drop(low_signal_outliers)
    outliers.extend(low_signal_outliers)

    baseline = compute_baseline(time_traces, baseline_lambda, baseline_tolerance)
    baselined_time_traces = time_traces.sum(1) - baseline

    baseline_outliers = find_baseline_outliers(baselined_time_traces, outlier_threshold)
    outliers.extend(baseline_outliers)

    return outliers, baseline


def find_low_signal_outliers(time_traces, low_signal_window):
    low_signal_outliers = set()
    low_signal_cutoff = len(time_traces.columns) * 0.1
    sorted_time_traces = time_traces.sum(1).sort_values()

    i = 0
    if low_signal_window.lower() == 'wide':
        while sorted_time_traces.iloc[i] < low_signal_cutoff:
            outlier_index = time_traces.index.get_loc(sorted_time_traces.index[i])
            low_signal_outliers.add(time_traces.index[outlier_index])
            low_signal_outliers.add(time_traces.index[outlier_index + 1])
            low_signal_outliers.add(time_traces.index[outlier_index - 1])
            i += 1
    else:
        while sorted_time_traces.iloc[i] < low_signal_cutoff:
            outlier_index = time_traces.index.get_loc(sorted_time_traces.index[i])
            low_signal_outliers.add(time_traces.index[outlier_index])
            i += 1

    return low_signal_outliers


def compute_baseline(time_traces, baseline_lambda, baseline_tolerance):
    # Smoothed baseline of the summed time traces (lam=smoothing factor, tol=exit criteria)
    return pd.Series(whittaker.asls(
        time_traces.sum(1),
        lam=baseline_lambda,
        tol=baseline_tolerance)[0],
        time_traces.sum(1).index)


def find_baseline_outliers(baselined_time_traces, outlier_threshold):
    baseline_outliers = set()
    i = 0
    sorted_baselined_time_traces = abs(baselined_time_traces).sort_values(ascending=False)
    while sorted_baselined_time_traces.iloc[i] / baselined_time_traces.max() > outlier_threshold:
        baseline_outliers.add(sorted_baselined_time_traces.index[i])
        i += 1
    return baseline_outliers

import pandas as pd
from pybaselines.whittaker import asls


def find_outliers(traces: pd.DataFrame, threshold: float, lsw: str, lam: float, tol: float) -> list:
    """
    Find outlier spectra.

    Detects outlier spectra from the given time traces. Outliers typically
    occur when mixing or injecting solutions and result in big spikes or
    dips in the absorbance.

    Parameters
    ----------
    traces : :class:`pd.DataFrame`
        Time traces to find outliers with.
    threshold : float
        The outlier threshold, values closer to 0 produce more outliers
        while values closer to 1 produce fewer outliers. A value >>1 will
        produce no outliers.
    lsw : str
        The width of the low signal outlier window. Either 'wide' or 'narrow'.
    lam : float
        The smoothness of the baseline. Larger numbers result in a smoother
        baseline. Try values between 0.001 and 10000.
    tol : float
        Set the exit criteria for the baseline algorithm. Try values between
        0.001 and 10000. See :func:`pybaselines.whittaker.asls()` for more
        information.

    Returns
    -------
    outliers : list
        A list of time values for outlier data points.
    baseline : :class:`pd.Series`
        The baseline used for outlier detection.
    """
    outliers = []
    low_signal_outliers = find_low_signal_outliers(data=traces, window=lsw)
    time_traces = traces.drop(low_signal_outliers)

    baseline = compute_baseline(data=time_traces.sum(1), lam=lam, tol=tol)
    baselined_time_traces = time_traces.sum(1) - baseline
    baseline_outliers = find_baseline_outliers(data=baselined_time_traces, threshold=threshold)

    outliers.extend(low_signal_outliers)
    outliers.extend(baseline_outliers)
    return outliers, baseline


def find_low_signal_outliers(data: pd.DataFrame, window: str) -> set[float]:
    """
    Detect anomalous low signals in data.

    Low signal outliers usually occur when the cuvette is removed
    from the instrument during data collection, resulting in an
    abrupt dip in the time trace. It is important to remove
    these outliers as the baseline fitting algorithm is greatly
    affected by their presence.

    Parameters
    ----------
    data : :class:`pd.DataFrame`
        The data to check for low signal outliers.
    window : str
        The width of the low signal outlier window. Either 'wide' or 'narrow'.

    Returns
    -------
    outliers : set[float]
        A set of outlier x-axis values.
    """
    outlier_cutoff = len(data.columns) * 0.1
    outliers = set(data[data.sum(axis=1) < outlier_cutoff].index)
    if window.lower() == 'wide':
        outlier_indexes = data.index.get_indexer(outliers)
        neighboring_outliers = set(pd.Index.union(data.iloc[outlier_indexes - 1].index,
                                                  data.iloc[outlier_indexes + 1].index))
        outliers.update(neighboring_outliers)
    return outliers


def compute_baseline(data: pd.DataFrame, lam: float, tol: float) -> pd.Series:
    # lam=smoothing factor, tol=exit criteria
    return pd.Series(asls(data, lam=lam, tol=tol)[0], data.index)


def find_baseline_outliers(data: pd.DataFrame, threshold: float) -> set:
    # Normalize data and get index of rows above threshold.
    max_value = data.abs().max()
    outliers = data[data.abs() / max_value > threshold].index
    return outliers

"""
Contains data fitting functions.

@author: David Hebert
"""
import warnings
from collections import namedtuple
from typing import Optional, Callable
from scipy.optimize import curve_fit
from scipy.stats import linregress
import numpy as np
import pandas as pd


warnings.filterwarnings('ignore', message='overflow encountered in exp')


def rsquared(data: pd.Series, fit: pd.Series) -> float:
    """Calculate r-squared."""
    ss_res = np.sum((data - fit) ** 2)
    ss_tot = np.sum((data - np.mean(data)) ** 2)
    r2 = 1 - (ss_res / ss_tot)
    return r2


def fit_exponential(time_traces: pd.DataFrame) -> dict | None:
    """
    Fit exponential function to time traces.

    Parameters
    ----------
    time_traces : :class:`pandas.DataFrame`
        The time traces to fit.

    Returns
    -------
    fit : dict or None
        The fitting parameters for the given time traces.
    """
    def exponential_func(t: float, abs_0: float, abs_f: float, kobs: float) -> float:
        return abs_f + (abs_0 - abs_f) * np.exp(-kobs * t)

    def fit_params_handler(trace) -> dict:
        """Prepare parameters for the fitting function."""
        p0 = [trace.iloc[0], trace.iloc[-1], 0.02]
        curve_fit_params = {
            'f': exponential_func,
            'xdata': trace.index,
            'ydata': trace,
            'p0': p0,
            'bounds': ([-4, -4, -1], [4, 4, np.inf])
        }

        return curve_fit_params

    def post_fit_handler(trace, fit_params, fit_errors) -> tuple[dict, pd.Series]:
        """Handle result output and formatting."""
        abs_0, abs_f, kobs = fit_params
        abs_0_err, abs_f_err, kobs_err = np.sqrt(np.diag(fit_errors))

        curve = pd.Series(
            data=exponential_func(trace.index, *fit_params),
            index=trace.index,
            name=trace.name
        )

        return {
            'abs_0': abs_0,
            'abs_0 err': abs_0_err,
            'abs_f': abs_f,
            'abs_f err': abs_f_err,
            'kobs': kobs,
            'kobs err': kobs_err,
            'r2': rsquared(trace, curve)
        }, curve

    if fit := _fit_time_traces(
        time_traces,
        curve_fit,
        fit_params_handler,
        post_fit_handler
    ):
        return {'params': fit.params, 'curves': fit.fits}

    return None


def initial_rates(time_traces: pd.DataFrame, cutoff: float = 0.1) -> dict | None:
    """
    Perform a linear regression on time traces to determine initial rates.

    Parameters
    ----------
    time_traces : :class:`pandas.DataFrame`
        The time traces to fit.
    cutoff : float, optional
        The cutoff value for the change in absorbance. A cutoff of 0.1 would
        limit the initial rate fitting to the first 10% change in absorbance
        of the time traces.

    Returns
    -------
    fit : dict or None
        The fitting parameters for the given time traces.
    """
    def linear_func(x, slope, intercept) -> float:
        return slope * x + intercept

    def cutoff_handler(trace) -> pd.Series:
        abs_0 = trace.iloc[0]

        # Handle both growing and decaying traces
        cutoff_idx = max(
            abs(trace.iloc[2:] - abs_0 * (1 - cutoff)).idxmin(),
            abs(trace.iloc[2:] - abs_0 * (1 + cutoff)).idxmin()
        )

        return trace[:cutoff_idx]

    def fit_params_handler(trace: pd.Series) -> dict:
        """Prepare parameters for the fitting function."""
        trace = cutoff_handler(trace)
        return {'x': trace.index, 'y': trace.values}

    def post_fit_handler(trace, *fit_params) -> tuple[dict, pd.Series]:
        """Handle result output and formatting."""
        abs_0 = trace.iloc[0]
        abs_f = trace.iloc[-1]
        m, b, _, _, m_err = fit_params

        line = pd.Series(
            data=linear_func(trace.index, m, b),
            index=trace.index,
            name=trace.name
        )

        return {
            'slope': m,
            'slope err': m_err,
            'intercept': b,
            'abs_0': abs_0,
            'abs_f': abs_f,
            'delta_abs_%': (abs_f - abs_0) / abs_0,
            'delta_t': trace.index[-1] - trace.index[0],
            'r2': rsquared(trace, line)
        }, line

    if fit := _fit_time_traces(
        time_traces,
        linregress,
        fit_params_handler,
        post_fit_handler,
        trace_prehandler=cutoff_handler
    ):
        return {'params': fit.params, 'lines': fit.fits}

    return None


def _fit_time_traces(time_traces: pd.DataFrame, fit_func: Callable,
                     fit_params_handler: Callable, post_fit_handler: Callable,
                     trace_prehandler: Optional[Callable] = None,
                     min_data_points: int = 3) -> Optional[namedtuple]:
    """
    General fitting function for time traces.

    Parameters
    ----------
    time_traces : pd.DataFrame
        The time traces to fit.
    fit_func : Callable
        The function to use for fitting.
    fit_params_handler : Callable
        A function which returns keyword arguments to pass to ``fit_func``.
    post_fit_handler : Callable
        A function which a tuple of fitting parameters and the fits.
    trace_prehandler : Callable, optional
        A function which applies any necessary preprocessing to a time trace
        (a :class:`pandas.Series`). By default None.
    min_data_points : int, optional
        The minimum number of data points needed to perform fitting.

    Returns
    -------
    namedtuple | None
        A namedtuple with attributes ``params`` and ``fits`` of the fitting
        parameters and the fits.
    """
    if len(time_traces.index) <= min_data_points:
        print('Fitting skipped. Not enough data points...\n')
        return None

    fit_params = {}
    fitted_data = {}

    for column in time_traces.columns:
        if trace_prehandler:
            trace = trace_prehandler(time_traces[column])
        else:
            trace = time_traces[column]

        try:
            fit_result = fit_func(**fit_params_handler(trace))
            fit_params[column], fitted_data[column] = post_fit_handler(trace, *fit_result)

        except Exception:
            continue

    if fit_params and fitted_data:
        Fit = namedtuple('Fit', ['params', 'fits'])
        return Fit(params=pd.DataFrame(fit_params), fits=pd.DataFrame(fitted_data))

    return None

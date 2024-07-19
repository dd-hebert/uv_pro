"""
Contains data fitting functions.

@author: David Hebert
"""
import warnings
from scipy.optimize import curve_fit
from scipy.stats import linregress
import numpy as np
import pandas as pd


warnings.filterwarnings('ignore', message='overflow encountered in exp')


def _exponential(t: float, abs_0: float, abs_f: float, kobs: float) -> float:
    return abs_f + (abs_0 - abs_f) * np.exp(-kobs * t)


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
    if len(time_traces.index) <= 3:
        print('Fitting skipped. Not enough data points...\n')
        return None

    fit = {'params': {}, 'curves': {}}

    for column in time_traces.columns:
        try:
            p0 = [time_traces[column].iloc[0], time_traces[column].iloc[-1], 0.02]

            popt, pcov = curve_fit(
                f=_exponential,
                xdata=time_traces.index,
                ydata=time_traces[column],
                p0=p0,
                bounds=([-4, -4, -1], [4, 4, np.inf])
            )

            curve = pd.Series(
                data=_exponential(time_traces.index, *popt),
                index=time_traces.index,
                name=column
            )

            perr = np.sqrt(np.diag(pcov))
            r2 = rsquared(time_traces[column], curve)
            fit['curves'][column] = curve
            fit['params'][column] = {
                'abs_0': popt[0],
                'abs_0 err': perr[0],
                'abs_f': popt[1],
                'abs_f err': perr[1],
                'kobs': popt[2],
                'kobs err': perr[2],
                'r2': r2
            }

        except RuntimeError:
            print(f'\033[31mUnable to fit exponential to {column} nm.\033[0m')

    if fit:
        fit['params'] = pd.DataFrame(fit['params'])
        fit['curves'] = pd.DataFrame(fit['curves'])
        return fit
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
    if len(time_traces.index) < 3:
        print('Fitting skipped. Not enough data points...\n')
        return None

    init_rates = {'params': {}, 'lines': {}}

    for column in time_traces.columns:
        abs_0 = time_traces[column].iloc[0]

        # Handle both growing and decaying traces
        cutoff_idx = max(
            abs(time_traces[column].iloc[2:] - abs_0 * (1 - cutoff)).idxmin(),
            abs(time_traces[column].iloc[2:] - abs_0 * (1 + cutoff)).idxmin()
        )

        abs_f = time_traces[column].loc[cutoff_idx]
        trace = time_traces[column][:cutoff_idx]

        line_fit = linregress(
            x=trace.index,
            y=trace.values
        )

        m = line_fit.slope
        m_err = line_fit.stderr
        b = line_fit.intercept
        b_err = line_fit.intercept_stderr

        line = pd.Series(
            data=[m * x + b for x in trace.index],
            index=trace.index,
            name=column
        )

        r2 = rsquared(trace, line)
        init_rates['lines'][column] = line
        init_rates['params'][column] = {
            'abs_0': abs_0,
            'abs_f': abs_f,
            'delta_abs_%': (abs_f - abs_0) / abs_0,
            'delta_t': trace.index[-1] - trace.index[0],
            'slope': m,
            'slope err': m_err,
            'intercept': b,
            'intercept err': b_err,
            'r2': r2
        }

    if init_rates:
        init_rates['params'] = pd.DataFrame(init_rates['params'])
        init_rates['lines'] = pd.DataFrame(init_rates['lines'])
        return init_rates
    return None


def rsquared(data: pd.Series, fit: pd.Series) -> float:
    """Calculate r-squared."""
    ss_res = np.sum((data - fit) ** 2)
    ss_tot = np.sum((data - np.mean(data)) ** 2)
    r2 = 1 - (ss_res / ss_tot)
    return r2

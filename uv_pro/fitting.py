"""
Contains data fitting functions.

@author: David Hebert
"""
import warnings
from scipy.optimize import curve_fit
import numpy as np
import pandas as pd


warnings.filterwarnings('ignore', message='overflow encountered in exp')


def exponential(t: float, abs_0: float, abs_f: float, kobs: float) -> float:
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
    if len(time_traces) <= 3:
        print('Fitting skipped. Not enough data points...\n')
        return None

    fit = {'params': {}, 'curves': {}}
    for column in time_traces.columns:
        try:
            p0 = [time_traces[column].iloc[0], time_traces[column].iloc[-1], 0.1]

            popt, pcov = curve_fit(
                f=exponential,
                xdata=time_traces.index,
                ydata=time_traces[column],
                p0=p0,
                bounds=(-1, [10, 10, np.inf])
            )

            curve = pd.Series(
                data=exponential(time_traces.index, *popt),
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


def rsquared(data: pd.Series, fit: pd.Series) -> float:
    """Calculate r-squared."""
    ss_res = np.sum((data - fit) ** 2)
    ss_tot = np.sum((data - np.mean(data)) ** 2)
    r2 = 1 - (ss_res / ss_tot)
    return r2

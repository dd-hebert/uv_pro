import warnings
from scipy.optimize import curve_fit
import numpy as np
import pandas as pd


warnings.filterwarnings('ignore', message='overflow encountered in exp')


def exponential(t: float, abs_0: float,
                abs_f: float, kobs: float) -> float:
    return abs_f + (abs_0 - abs_f) * np.exp(-kobs * t)


def fit_exponential(time_traces: pd.DataFrame) -> dict | None:
    fit = {}
    for column in time_traces.columns:
        try:
            p0 = [time_traces[column].iloc[0], time_traces[column].iloc[-1], 0.1]
            popt, pcov = curve_fit(f=exponential,
                                   xdata=time_traces.index,
                                   ydata=time_traces[column],
                                   p0=p0)
            perr = np.sqrt(np.diag(pcov))
            curve = pd.Series(data=exponential(time_traces.index, *popt),
                              index=time_traces.index,
                              name=column)
            r2 = rsquared(time_traces[column], curve)
            fit[column] = {'popt': popt, 'perr': perr, 'curve': curve, 'r2': r2}
        except RuntimeError:
            print(f'Unable to fit exponential to {column}.')
    if fit:
        return fit
    return None


def rsquared(data: pd.Series, fit: pd.Series) -> float:
    residuals = data - fit
    ss_res = np.sum(residuals ** 2)
    ss_tot = np.sum((data - np.mean(data)) ** 2)
    r2 = 1 - (ss_res / ss_tot)
    return r2

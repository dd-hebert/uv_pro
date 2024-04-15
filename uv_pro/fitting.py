import warnings
from scipy.optimize import curve_fit
import numpy as np
import pandas as pd


warnings.filterwarnings('ignore', message='overflow encountered in exp')


def exponential(t: float, abs_0: float,
                abs_f: float, kobs: float) -> float:
    return abs_f + (abs_0 - abs_f) * np.exp(-kobs * t)


def fit_exponential(time_traces: pd.DataFrame) -> dict | None:
    """
    Fit exponential function to time traces.

    Parameters
    ----------
    time_traces : :class:`pd.DataFrame`
        The time traces to fit.

    Returns
    -------
    fit: dict or None
        The fitting parameters for the given time traces.
    """
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


def print_fit(fit: dict) -> None:
    # TODO use string formatting to make table prettier
    equation = 'f(t) = abs_f + (abs_0 - abs_f) * exp(-kobs * t)'
    print('\033[3m{}\033[23m'.format(equation))
    print('\n' + '┌' + '─' * 94 + '┐')
    table_headings = '│ \033[1m{}\t{:^18}\t{:^18}\t{:^18}\t{:^6}\033[22m │'
    print(table_headings.format('Wavelength', 'kobs', 'abs_0', 'abs_f', 'r2'))
    print('├' + '─' * 94 + '┤')
    for wavelength, fit in fit.items():
        abs_0 = '{:+.5f} ± {:.5f}'.format(fit['popt'][0], fit['perr'][0])
        abs_f = '{:+.5f} ± {:.5f}'.format(fit['popt'][1], fit['perr'][1])
        kobs = '{:.2e} ± {:.2e}'.format(fit['popt'][2], fit['perr'][2])
        r2 = '{:.4f}'.format(fit['r2'])
        print('│ {:>10}\t{}\t{}\t{}\t{} │'.format(wavelength, kobs, abs_0, abs_f, r2))
    print('└' + '─' * 94 + '┘')

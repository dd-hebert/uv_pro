"""
Contains data fitting functions.

@author: David Hebert
"""

from __future__ import annotations
import warnings
from dataclasses import dataclass
from typing import Callable, Literal, Optional, TYPE_CHECKING

import numpy as np
import pandas as pd
import scipy.stats as stats
from rich import print

if TYPE_CHECKING:
    from lmfit import Parameters

warnings.filterwarnings('ignore', message='overflow encountered in exp')


@dataclass
class FitResult:
    model: str
    global_fit: bool
    params: pd.DataFrame
    fitted_data: pd.DataFrame


def fit_time_traces(
    time_traces: pd.DataFrame,
    fit_model: Literal['initial-rates', 'exponential'],
    global_fit: bool = False,
    fit_cutoff: float = 0.1,
) -> FitResult:
    """
    Fit a model to time traces.

    Parameters
    ----------
    time_traces : pd.DataFrame
        The time traces to fit the model to.
    fit_model : str
        The model to use for fitting, either 'initial-rates' or 'exponential'.
    fit_global : bool, optional
        Perform individual or global fitting. Default False (individual fit).
    fit_cutoff : float, optional
        The % change in absorbance cutoff for initial rates fitting. \
        Has no effect if `fit_model` is 'exponential'.
        Default 0.1 (10% change in absorbance).

    Returns
    -------
    FitResult
        The parameters and data of the fit.
    """

    if fit_model == 'initial-rates':
        return InitialRates(time_traces, fit_cutoff, global_fit=global_fit).fit()
    if fit_model == 'exponential':
        return ExponentialFit(time_traces, global_fit=global_fit).fit()

def rsquared(data: pd.Series, fit: pd.Series) -> float:
    """Calculate r-squared."""
    ss_res = np.sum((data - fit) ** 2)
    ss_tot = np.sum((data - np.mean(data)) ** 2)
    r2 = 1 - (ss_res / ss_tot)
    return r2


class ExponentialFit:
    """
    Exponential fitting model for time traces.
    """
    def __init__(self, traces: pd.DataFrame, global_fit: bool = False) -> None:
        self.traces = traces
        self.global_fit = global_fit

    def model(self, t: np.ndarray, abs_0: float, abs_f: float, kobs: float) -> np.ndarray:
        """Exponential fit model: y = abs_f + (abs_0 - abs_f) * exp(-kobs * t)"""
        return abs_f + (abs_0 - abs_f) * np.exp(-kobs * t)

    def _setup_params(self) -> Parameters:
        from lmfit import Parameters
        params = Parameters()

        if self.global_fit:
            params.add('kobs', value=0.02, min=0)

        for i, (_, trace) in enumerate(self.traces.items()):
            key = f'_{i}'
            params.add(f'abs_0{key}', value=trace.iloc[0], min=-4, max=4)
            params.add(f'abs_f{key}', value=trace.iloc[-1], min=-4, max=4)
            if not self.global_fit:
                params.add(f'kobs{key}', value=0.02, min=0)

        return params

    def fit(self) -> FitResult | None:
        """Fit an exponential model to time traces for kobs calculations."""
        from lmfit import Minimizer

        result = Minimizer(self.residual, self._setup_params()).minimize()
        return FitResult('exponential', self.global_fit, *self._format_result(result.params))

    def residual(self, params: Parameters) -> np.ndarray:
        resids = []
        for i, (_, trace) in enumerate(self.traces.items()):
            key = f'_{i}'
            abs_0 = params[f'abs_0{key}']
            abs_f = params[f'abs_f{key}']
            kobs = params['kobs'] if self.global_fit else params[f'kobs{key}']
            model = self.model(trace.index, abs_0, abs_f, kobs)
            resids.append(model - trace)
        return np.concatenate(resids)

    def _format_result(self, params: Parameters) -> tuple[pd.DataFrame, pd.DataFrame]:
        fit_params = {}
        fitted_data = {}

        for i, (col, trace) in enumerate(self.traces.items()):
            key = f'_{i}'
            abs_0 = params[f'abs_0{key}'].value
            abs_f = params[f'abs_f{key}'].value
            kobs = params['kobs'].value if self.global_fit else params[f'kobs{key}'].value

            abs_0_err = params[f'abs_0{key}'].stderr
            abs_f_err = params[f'abs_f{key}'].stderr
            kobs_err = params['kobs'].stderr if self.global_fit else params[f'kobs{key}'].stderr

            # Compute 95% CI half-width for kobs
            n = len(trace)
            if kobs_err and np.isfinite(kobs_err) and n > 3:
                ci = stats.t.interval(0.95, df=n - 3, loc=kobs, scale=kobs_err)
                kobs_ci = (ci[1] - ci[0]) / 2
            else:
                kobs_ci = np.nan

            fit_curve = pd.Series(
                self.model(trace.index.values, abs_0, abs_f, kobs),
                index=trace.index,
                name=trace.name,
            )

            fit_params[col] = {
                "abs_0": abs_0,
                "abs_0 err": abs_0_err,
                "abs_f": abs_f,
                "abs_f err": abs_f_err,
                "kobs": kobs,
                "kobs err": kobs_err,
                "kobs ci": kobs_ci,
                "r2": rsquared(trace, fit_curve),
            }
            fitted_data[col] = fit_curve

        return pd.DataFrame(fit_params), pd.DataFrame(fitted_data)


class InitialRates:
    """
    Initial rates linear fitting model for time traces.
    """
    def __init__(self, traces: pd.DataFrame, cutoff: float = 0.1, global_fit: bool = False) -> None:
        self.traces = self.truncate_traces(traces, cutoff)
        self.global_fit = global_fit

    def model(self, t: np.ndarray, slope: float, intercept: float) -> np.ndarray:
        """Linear fit model: y = m * t + b"""
        return slope * t + intercept

    def _setup_params(self) -> Parameters:
        """Initialize the parameters for the fitting model."""
        from lmfit import Parameters
        params = Parameters()

        if self.global_fit:
            params.add('slope', value=0.01)

        for i, trace in enumerate(self.traces):
            key = f'_{i}'
            params.add(f'intercept{key}', value=trace.iloc[0])
            if not self.global_fit:
                params.add(f'slope{key}', value=0.01)

        return params

    def fit(self) -> FitResult | None:
        """Fit a linear model to time traces for initial rates calculations."""
        from lmfit import Minimizer

        result = Minimizer(self.residual, self._setup_params()).minimize()
        return FitResult('initial-rates', self.global_fit, *self._format_result(result.params))

    def truncate_traces(self, traces: pd.DataFrame, cutoff: float) -> list[pd.Series]:
        """
        Truncate traces to where the change in absorbance equals the cutoff.

        Parameters
        ----------
        traces : pd.DataFrame
            The time traces to fit.
        cutoff : float
            The fractional change in absorbance cutoff (e.g., 0.1 -> 10%).

        Returns
        -------
        truncated_traces : list[pd.Series]
            The truncated traces
        """
        mask = pd.DataFrame(index=traces.index, columns=traces.columns, dtype=bool)

        for col, trace in traces.items():
            start_val: float = trace.iloc[0]
            threshold = abs(start_val) * cutoff
            diff = (trace - start_val).abs()
            mask[col] = diff >= threshold

        cutoff_indices = {
            col: (mask[col].idxmax() if mask[col].any() else traces.index[-1])
            for col in traces.columns
        }

        truncated_traces = []
        for col, trace in traces.items():
            cutoff = cutoff_indices[col]
            end_idx = trace.index.get_loc(cutoff)
            truncated_traces.append(traces[col].iloc[:end_idx + 1])

        return truncated_traces

    def residual(self, params: Parameters) -> np.ndarray:
        resids = []
        for i, trace in enumerate(self.traces):
            key = f'_{i}'
            slope = params['slope'] if self.global_fit else params[f'slope{key}']
            intercept = params[f'intercept{key}']
            model = self.model(trace.index, slope, intercept)
            resids.append(model - trace)
        return np.concatenate(resids)

    def _format_result(self, params: Parameters) -> tuple[pd.DataFrame, pd.DataFrame]:
        fit_params = {}
        fitted_data = {}

        for i, trace in enumerate(self.traces):
            key = f'_{i}'
            abs_0 = trace.iloc[0]
            abs_f = trace.iloc[-1]
            slope = params['slope'].value if self.global_fit else params[f'slope{key}'].value
            intercept = params[f'intercept{key}'].value

            slope_err = params['slope'].stderr if self.global_fit else params[f'slope{key}'].stderr
            intercept_err = params[f'intercept{key}'].stderr

            # Compute 95% CI half-width for rate
            n = len(trace)
            if slope_err and np.isfinite(slope_err) and n > 3:
                ci = stats.t.interval(0.95, df=n - 2, loc=slope, scale=slope_err)
                slope_ci = (ci[1] - ci[0]) / 2
            else:
                slope_ci = np.nan

            fit_line = pd.Series(
                self.model(trace.index, slope, intercept),
                index=trace.index,
                name=trace.name,
            )

            fit_params[trace.name] = {
                'slope': slope,
                'slope err': slope_err,
                'slope ci': slope_ci,
                'intercept': intercept,
                'abs_0': abs_0,
                'abs_f': abs_f,
                'delta_abs_%': abs((abs_f - abs_0) / abs_0) * 100,
                'delta_t': trace.index[-1] - trace.index[0],
                'r2': rsquared(trace, fit_line),
            }
            fitted_data[trace.name] = fit_line

        return pd.DataFrame(fit_params), pd.DataFrame(fitted_data)

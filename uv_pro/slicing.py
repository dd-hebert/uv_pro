"""
Contains functions for slicing UV-vis spectra.

@author: David Hebert
"""
from pandas import DataFrame
import numpy as np


def slice_spectra(spectra: DataFrame, slicing: dict) -> DataFrame:
    """
    Reduce the given ``spectra`` down to a selection of slices.

    Slices can be taken at using equally- or unequally-spaced (variable) intervals \
    or from specific times. Equal slicing requires a single integer (e.g., a value \
    of 10 will produce 10 equally-spaced slices). Variable slicing requires two \
    floats, a coefficient and an exponent. For variable slicing, the step size \
    between slices is calculated by the equation step_size = coeff * x^expo + 1. \
    Specific slicing requires a list of float (time) values.

    Note
    ----
    Due to integer rounding, the number of equally-spaced slices returned may \
    differ slightly from the value given by ``slicing['slices']``.

    Parameters
    ----------
    spectra : :class:`pandas.DataFrame`
        The spectra to take slices from.
    slicing : dict
        The slicing parameters.
        For equal slicing: ``{'mode': 'equal', 'slices': int}``
        For variable (unequally-spaced) slicing: ``{'mode': 'variable', \
        'coeff': float, 'expo': float}``
        For specific slicing: ``{'mode': 'specific', 'times': list[float]}``.

    Returns
    -------
    sliced_spectra : :class:`pandas.DataFrame`
        The resulting spectra slices.
    """
    if slicing['mode'] == 'equal':
        return equal_slicing(spectra, slicing['slices'])

    if slicing['mode'] == 'variable':
        return variable_slicing(spectra, slicing['coeff'], slicing['expo'])

    if slicing['mode'] == 'specific':
        return specific_slicing(spectra, slicing['times'])

    raise ValueError(f'Invalid slicing mode: `{slicing.get("mode", None)}`.')


def variable_slicing(spectra: DataFrame, coeff: float, expo: float) -> DataFrame:
    """Get unequally-spaced slices from ``spectra``."""
    _check_variable_slice_coeff(coeff)
    slices = [0]
    for i in range(1, len(spectra.columns)):
        next_slice = slices[-1] + round(coeff * i**expo + 1)

        if next_slice >= len(spectra.columns):
            break

        slices.append(next_slice)

    return spectra.iloc[:, slices]


def _check_variable_slice_coeff(coeff) -> None:
    if coeff <= 0:
        raise ValueError('Invalid variable slicing coefficient. Value must be >0.')


def equal_slicing(spectra: DataFrame, num_slices: int) -> DataFrame:
    """Get equally-spaced slices from ``spectra``."""
    num_slices = min(num_slices, len(spectra.columns))
    return spectra.iloc[:, np.linspace(0, len(spectra.columns) - 1, num_slices).astype(int)]


def specific_slicing(spectra: DataFrame, times: list[int]) -> DataFrame:
    """Get the slices closest to the given ``times`` from ``spectra``."""
    closest_times = sorted(set([min(spectra.columns, key=lambda t: abs(t - time)) for time in times]))
    return spectra[closest_times]

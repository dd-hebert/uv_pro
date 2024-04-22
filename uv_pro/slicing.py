"""
Contains functions for slicing UV-vis spectra.

@author: David Hebert
"""
from pandas import DataFrame


def slice_spectra(spectra: DataFrame, slicing: dict) -> DataFrame:
    """
    Reduce the given ``spectra`` down to a selection of slices.

    Slices can be taken at equally- or unequally-spaced
    (gradient) intervals. Equal slicing requires a single integer
    (e.g., a value of 10 will produce 10 equally-spaced slices).
    Gradient slicing requires two floats, a coefficient and an exponent.
    For gradient slicing, the step size between slices is calculated
    by the equation step_size = coeff * x^expo + 1.

    Parameters
    ----------
    spectra : :class:`pandas.DataFrame`
        The spectra to take slices from.
    slicing : dict
        The slicing parameters. For equal slicing:
        ``{'mode': 'equal', 'slices': int}``.
        For gradient (unequally-spaced) slicing:
        ``{'mode': 'gradient', 'coeff': float, 'expo': float}``.

    Returns
    -------
    sliced_spectra : :class:`pandas.DataFrame`
        The resulting spectra slices.
    """
    if slicing['mode'] == 'gradient':
        sliced_spectra = gradient_slicing(spectra, slicing['coeff'], slicing['expo'])

    else:
        sliced_spectra = equal_slicing(spectra, slicing['slices'])

    return sliced_spectra


def gradient_slicing(spectra: DataFrame, coeff: float, expo: float) -> DataFrame:
    """Get unequally-spaced slices from ``spectra``."""
    _check_gradient_slice_coeff(coeff)
    slices = [0]
    for i in range(1, len(spectra.columns) + 1):
        next_slice = slices[-1] + round(coeff * i**expo + 1)

        if next_slice >= len(spectra.columns):
            break

        slices.append(next_slice)

    return spectra.iloc[:, slices]


def _check_gradient_slice_coeff(coeff) -> None:
    if coeff <= 0:
        raise ValueError('Invalid gradient slicing coefficient. Value must be >0.')


def equal_slicing(spectra: DataFrame, num_slices: int) -> DataFrame:
    """Get equally-spaced slices from ``spectra``."""
    step = max(1, len(spectra.columns) // num_slices)
    return spectra.iloc[:, list(range(0, len(spectra.columns), step))]

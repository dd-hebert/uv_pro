"""
Find peaks in UV-vis spectra.

@author: David Hebert
"""

import numpy as np
import pandas as pd
from scipy.signal import find_peaks as scipy_find_peaks
from scipy.signal import savgol_filter


def find_peaks(
    spectrum: pd.DataFrame,
    num_peaks: int = 0,
    conc: float | None = None,
    p_win: tuple[int, int] | None = None,
    s_win: int = 15,
    dist: int = 10,
    prom: float = 0.0,
    max_iter: int = 1000,
) -> dict:
    """
    Find UV-vis peaks using local maxima.

    Uses :func:`scipy.signal.find_peaks` to find peaks in ``spectrum``. \
    Savitzky-Golay smoothing is applied to ``spectrum`` to improve peak \
    detection. See :func:`scipy.signal.savgol_filter`.

    If ``num_peaks`` > 0, then ``prom`` will be iteratively adjusted until \
    the specified number of peaks is found or ``max_iter`` is reached.

    Parameters
    ----------
    spectrum : :class:`pandas.DataFrame`
        The spectrum to find peaks with.
    num_peaks : int, optional
        The number of peaks that should be found. Default is 0 (find all peaks).
    conc : float or None, optional
        The molar concentration of the species in the spectrum. Used for calculating \
        molar absorptivity (ε). Default is None.
    p_win : tuple[int, int] or None, optional
        Set the peak detection window (in nm). Search for peaks within the given \
        wavelength range. Default is None (search whole spectrum).
    s_win : int, optional
        Set the Savitzky-Golay smoothing window. Default is 15. \
        See :func:`scipy.signal.savgol_filter`.
    dist : int, optional
        Set the minimum distance between peaks (in nm). Default is 10.
    prom : float, optional
        Set the minimum peak prominance. Default is 0.
    max_iter : int, optional
        The max number of peak finding iterations. The default is 1000.

    Returns
    -------
    dict
        The found peaks ``{'peaks': list[int], 'info': pd.DataFrame}``. \
        The peak info is a :class:`pandas.DataFrame` with the peak wavelengths \
        (index) and their respective absorbance values ``'abs'`` and epsilon values \
        ``'epsilon'`` (if ``conc`` was provided).
    """
    spectrum, smoothed_spectrum = _preprocess_spectrum(spectrum, p_win, s_win)

    max_prom = smoothed_spectrum.max()
    delta_prom = max_prom * 0.001
    peaks, _ = scipy_find_peaks(
        x=smoothed_spectrum, distance=dist, prominence=(prom, max_prom)
    )

    if int(num_peaks) > 0:
        for i in range(1, max_iter + 1):
            if len(peaks) == int(num_peaks):
                break

            prom += delta_prom if len(peaks) > num_peaks else -delta_prom

            if not 0 < prom < max_prom:
                break

            peaks, _ = scipy_find_peaks(
                x=smoothed_spectrum, distance=dist, prominence=(prom, max_prom)
            )

        else:
            print(f'Max iterations ({max_iter}) reached!')

    return _process_peaks(spectrum, peaks, conc)


def find_peaks_dxdy(
    spectrum: pd.DataFrame,
    conc: float | None = None,
    p_win: tuple[int, int] | None = None,
    s_win: int = 15,
) -> dict:
    """
    Find peaks from zero-crossings in the derivative of the smoothed UV-vis spectrum.

    Savitzky-Golay smoothing is applied to ``spectrum`` to improve peak detection. \
    See :func:`scipy.signal.savgol_filter`.

    Parameters
    ----------
    spectrum : :class:`pandas.DataFrame`
        The spectrum to find peaks with.
    conc : float or None, optional
        The molar concentration of the species in the spectrum. Used for calculating \
        molar absorptivity (ε). Default is None.
    p_win : tuple[int, int] or None, optional
        Set the peak detection window (in nm). Search for peaks within the given \
        wavelength range. Default is None (search whole spectrum).
    s_win : int, optional
        Set the Savitzky-Golay smoothing window. Default is 15. \
        See :func:`scipy.signal.savgol_filter`.

    Returns
    -------
    dict
        The found peaks ``{'peaks': list[int], 'info': pd.DataFrame}``. \
        The peak info is a :class:`pandas.DataFrame` with the peak wavelengths \
        (index) and their respective absorbance values ``'abs'`` and epsilon values \
        ``'epsilon'`` (if ``conc`` was provided).
    """
    spectrum, smoothed_spectrum = _preprocess_spectrum(spectrum, p_win, s_win)
    spectrum_deriv = np.gradient(smoothed_spectrum)
    peaks = _get_zero_crossings(spectrum_deriv) + 1

    return _process_peaks(spectrum, peaks, conc)


def find_peaks_hidden(
    spectrum: pd.DataFrame,
    conc: float | None = None,
    p_win: tuple[int, int] | None = None,
    s_win: int = 15,
) -> dict:
    """
    Find hidden peaks from the second-derivative of the smoothed UV-vis spectrum.

    Note
    ----
    WORK IN PROGRESS


    Parameters
    ----------
    spectrum : :class:`pandas.DataFrame`
        The spectrum to find peaks with.
    conc : float or None, optional
        The molar concentration of the species in the spectrum. Used for calculating \
        molar absorptivity (ε). Default is None.
    p_win : tuple[int, int] or None, optional
        Set the peak detection window (in nm). Search for peaks within the given \
        wavelength range. Default is None (search whole spectrum).
    s_win : int, optional
        Set the Savitzky-Golay smoothing window. Default is 15. \
        See :func:`scipy.signal.savgol_filter`.

    Returns
    -------
    dict
        The found peaks ``{'peaks': list[int], 'info': pd.DataFrame}``. \
        The peak info is a :class:`pandas.DataFrame` with the peak wavelengths \
        (index) and their respective absorbance values ``'abs'`` and epsilon values \
        ``'epsilon'`` (if ``conc`` was provided).
    """
    # WORK IN PROGRESS
    spectrum, smoothed_spectrum = _preprocess_spectrum(spectrum, p_win, s_win)
    spectrum_deriv = np.gradient(np.gradient(smoothed_spectrum))
    peaks, _ = scipy_find_peaks(
        x=spectrum_deriv * -1, threshold=0.0002, prominence=(0.001, 3), distance=10
    )

    return _process_peaks(spectrum, peaks, conc)


def smooth_spectrum(spectrum: pd.DataFrame, s_win: int = 15) -> np.ndarray:
    """
    Perform Savitzky-Golay smoothing on ``spectrum``.

    See :func:`scipy.signal.savgol_filter`.

    Parameters
    ----------
    spectrum : :class:`pandas.DataFrame`
        The spectrum to apply smoothing to.
    s_win : int, optional
        The smoothing window. The default is 15.

    Returns
    -------
    np.ndarray
        The smoothed
    """
    smoothed_spectrum = savgol_filter(
        x=spectrum, window_length=s_win, polyorder=3, axis=0
    )

    return smoothed_spectrum.flatten()


def _preprocess_spectrum(
    spectrum: pd.DataFrame, p_win: tuple[int, int] | None = None, s_win: int = 15
) -> tuple[pd.DataFrame, np.ndarray]:
    """Slice ``spectrum`` to ``p_win`` and get smoothed spectrum."""
    if p_win:
        spectrum = spectrum.loc[min(p_win) : max(p_win)]

    smoothed_spectrum = smooth_spectrum(spectrum, s_win)

    return spectrum, smoothed_spectrum


def _process_peaks(
    spectrum: pd.DataFrame, peaks: list[int], conc: float | None = None
) -> dict:
    peaks = _idx_to_wavelength(spectrum, peaks)
    absorbance = _get_absorbance(spectrum, peaks)
    peak_info = {'peaks': peaks, 'info': absorbance}

    if conc:
        epsilon = _get_epsilon(absorbance, conc)
        peak_info['info'] = pd.concat([absorbance, epsilon], axis='columns')

    return peak_info


def _idx_to_wavelength(spectrum: pd.DataFrame, peaks: np.ndarray) -> list[int]:
    """Convert peak indices to wavelength."""
    return [peak for peak in spectrum.iloc[peaks].index]


def _get_absorbance(spectrum: pd.DataFrame, peaks: list[int]) -> pd.DataFrame:
    absorbance = spectrum.loc[peaks]
    absorbance.rename(columns={absorbance.columns[0]: 'abs'}, inplace=True)
    absorbance.columns.name = ''

    return absorbance


def _get_epsilon(absorbance: pd.DataFrame, conc: float) -> pd.DataFrame:
    epsilon = absorbance // conc
    epsilon.rename(columns={epsilon.columns[0]: 'epsilon'}, inplace=True)

    return epsilon


def _get_zero_crossings(arr: np.ndarray) -> np.ndarray:
    return np.where(np.logical_and(np.diff(np.sign(arr)), (np.sign(arr[:-1]) == 1)))[0]

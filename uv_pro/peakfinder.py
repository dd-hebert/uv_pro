"""
An interactive UV-vis peak finder based on Matplotlib.

@author: David Hebert
"""
import pandas as pd
from uv_pro.dataset import Dataset
from uv_pro.peaks import find_peaks, find_peaks_dxdy


class PeakFinder:
    """
    UV-vis Peak finder.

    Attributes
    ----------
    dataset : :class:`~uv_pro.dataset.Dataset`
        The UV-vis dataset to find peaks with.
    peaks : dict
        The found peaks ``{'peaks': list[int], 'info': pd.DataFrame}``. \
        The peak info is a :class:`pandas.DataFrame` with the peak wavelengths \
        (index) and their respective absorbance values ``'abs'`` and epsilon values \
        ``'epsilon'`` (if a molar concentration was provided).
    peak_labels : list[:class:`matplotlib.text.Annotation`]
        The labels for peaks in the plot.
    peak_scatter : :class:`matplotlib.lines.Line2D`
        A scatter plot of the detected peaks in the current spectrum.
    smooth_spectrum : :class:`matplotlib.lines.Line2D`
        A line plot of the smoothed current spectrum.
    spectrum : :class:`pandas.DataFrame`
        The current spectrum to find peaks with.
    spectrum_scatter : :class:`matplotlib.lines.Line2D`
        A scatter plot of the current spectrum.
    """

    def __init__(self, path: str, *, method: str = 'localmax', num_peaks: int = 0,
                 conc: float | None = None, p_win: tuple[int, int] | None = None,
                 s_win: int = 15, dist: int = 10, prom: float = 0.0,
                 max_iter: int = 1000) -> None:
        """
        Initialize a :class:`~uv_pro.peakfinder.PeakFinder` and find peaks in UV-vis spectra.

        Parameters
        ----------
        path : str
            The path to a .KD file.
        method : str, optional
            The peak detection method. Either 'localmax' or 'deriv'. Default is 'localmax'.
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
        """
        self.method = method
        self.num_peaks = num_peaks
        self.conc = conc
        self.p_win = p_win
        self.s_win = s_win
        self.dist = dist
        self.prom = prom
        self.max_iter = max_iter
        self.peak_labels = []
        self.dataset = Dataset(path=path, view_only=False)
        self.time = self.dataset.spectra_times[0]
        self.spectrum = self._get_spectrum()
        self.peaks = self.find_peaks()

    def find_peaks(self) -> dict:
        """
        Find peaks in UV-vis spectra.

        Peak detection can be performed using local maxima or \
        first derivative methods. See :func:`~uv_pro.peaks.find_peaks` and \
        :func:`~uv_pro.peaks.find_peaks_dxdy`.

        Returns
        -------
        peaks : dict
            The found peaks ``{'peaks': list[int], 'info': pd.DataFrame}``. \
            The peak info is a :class:`pandas.DataFrame` with the peak wavelengths \
            (index) and their respective absorbance values ``'abs'`` and epsilon values \
            ``'epsilon'`` (if a molar concentration was provided).
        """
        if self.method == 'localmax':
            peaks = find_peaks(
                spectrum=self.spectrum,
                num_peaks=self.num_peaks,
                conc=self.conc,
                p_win=self.p_win,
                s_win=self.s_win,
                dist=self.dist,
                prom=self.prom,
                max_iter=self.max_iter
            )

        if self.method == 'deriv':
            peaks = find_peaks_dxdy(
                spectrum=self.spectrum,
                conc=self.conc,
                p_win=self.p_win,
                s_win=self.s_win
            )

        return peaks

    def _get_spectrum(self) -> pd.DataFrame:
        return self.dataset.raw_spectra.loc[:, [self.time]]

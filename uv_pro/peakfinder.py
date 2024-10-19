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

    # def _update_plot(self, val) -> None:
    #     """Update the plot when the time slider is changed."""
    #     self.time = val
    #     self.spectrum = self._get_spectrum()
    #     self.peaks = self.find_peaks()

    #     self.spectrum_scatter.set_ydata(self.spectrum)
    #     self.smooth_spectrum.set_ydata(
    #         smooth_spectrum(
    #             self.spectrum,
    #             s_win=self.s_win
    #         )
    #     )
    #     self.peak_scatter.set_data(
    #         self.peaks['info']['abs'].index,
    #         self.peaks['info']['abs']
    #     )

    #     self._adjust_ybounds()
    #     self._label_peaks()

    #     self.fig.canvas.draw_idle()

    def _get_spectrum(self) -> pd.DataFrame:
        return self.dataset.raw_spectra.loc[:, [self.time]]

    # def plot_peaks(self, plot_size: tuple[int, int] = (12, 6)) -> None:
    #     """Generate an interactive peak detection plot with time slider."""
    #     subplot: tuple[Figure, Axes] = plt.subplots(figsize=plot_size)
    #     self.fig, self.ax = subplot
    #     self.fig.suptitle('Peak Finder', fontweight='bold')
    #     self.fig.subplots_adjust(bottom=0.2)
    #     self.ax.set(
    #         title=self.dataset.name,
    #         xlabel='Wavelength (nm)',
    #         ylabel='Absorbance (AU)',
    #         xlim=(self.spectrum.index.min(), self.spectrum.index.max())
    #     )

    #     self.spectrum_scatter, = self.ax.plot(
    #         self.spectrum.index,
    #         self.spectrum,
    #         color='0.6',
    #         marker='o',
    #         linestyle='',
    #         zorder=0
    #     )
    #     self.smooth_spectrum, = self.ax.plot(
    #         self.spectrum.index,
    #         smooth_spectrum(self.spectrum, s_win=self.s_win),
    #         color='k',
    #         zorder=1
    #     )
    #     self.peak_scatter, = self.ax.plot(
    #         self.peaks['info']['abs'].index,
    #         self.peaks['info']['abs'],
    #         color='#0400FF',
    #         marker='|',
    #         markersize=15,
    #         linestyle='',
    #         zorder=2
    #     )

    #     self._label_peaks()

    #     ax_time = self.fig.add_axes([0.2, 0.03, 0.65, 0.03])
    #     time_slider = Slider(
    #         ax=ax_time,
    #         label='Time (s)',
    #         valmin=min(self.dataset.raw_spectra.columns),
    #         valmax=max(self.dataset.raw_spectra.columns),
    #         valinit=self.time,
    #         valstep=self.dataset.spectra_times,
    #         color='#0400FF',
    #         initcolor='none'
    #     )

    #     time_slider.on_changed(self._update_plot)

    #     plt.show()

    #     if self.peaks['peaks']:
    #         self._print_peaks()

    # def _label_peaks(self) -> None:
    #     self._clear_peak_labels()
    #     self.peak_labels = []

    #     for peak in self.peaks['peaks']:
    #         self.peak_labels.append(
    #             self.ax.annotate(
    #                 text=str(peak),
    #                 xy=(peak, self.peaks['info']['abs'].loc[peak] + 0.01),
    #                 color='#0400FF',
    #                 fontweight='bold',
    #                 fontsize='large',
    #                 zorder=3
    #             )
    #         )

    # def _clear_peak_labels(self) -> None:
    #     for label in self.peak_labels:
    #         label.remove()

    # def _adjust_ybounds(self) -> None:
    #     if self.peaks['info']['abs'].max() * 1.1 > self.ax.get_ylim()[1]:
    #         self.ax.set_ylim(top=self.peaks['info']['abs'].max() * 1.1)

    # def _print_peaks(self) -> str:
    #     out = []

    #     has_epsilon = 'epsilon' in self.peaks['info'].columns
    #     table_width = 34 if has_epsilon else 20
    #     headings = ['λ', 'abs'] + (['epsilon'] if has_epsilon else [])

    #     table_headings = f'│ \033[1m{headings[0]:^4}   '
    #     table_headings += ('   '.join([f'{heading:^11}' for heading in headings[1:]]))
    #     table_headings += ('\033[22m │')

    #     out.append('┌' + '─' * table_width + '┐')
    #     out.append(table_headings)
    #     out.append('├' + '─' * table_width + '┤')

    #     for wavelength in self.peaks['info'].index:
    #         row = f'│ {wavelength:^4}   {self.peaks['info']['abs'].loc[wavelength]:^11.3e}'
    #         row += f'   {self.peaks['info']['epsilon'].loc[wavelength]:^11.3e} │' if has_epsilon else ' │'
    #         out.append(row)

    #     out.append('└' + '─' * table_width + '┘')

    #     print('\n'.join(out))

"""
Functions for the ``peaks`` command.

@author: David Hebert
"""
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from matplotlib.widgets import Slider
from uv_pro.dataset import Dataset
from uv_pro.peaks import find_peaks, find_peaks_dxdy, smooth_spectrum
from uv_pro.commands.process import _handle_path


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
    peak_scatter : :class:`matplotlib.lines.Line2D`
        A scatter plot of the detected peaks in the current spectrum.
    smooth_spectrum : :class:`matplotlib.lines.Line2D`
        A line plot of the smoothed current spectrum.
    spectrum : :class:`pandas.DataFrame`
        The current spectrum to find peaks with.
    spectrum_scatter : :class:`matplotlib.lines.Line2D`
        A scatter plot of the current spectrum.
    """
    logo = '\n'.join(
        [
            '\n┏┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┓',
            '┇ uv_pro Peak Finder ┇',
            '┗┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┛',
            'Close plot window to continue.\n'
        ]
    )

    def __init__(self, args):
        """
        Initialize a :class:`~uv_pro.commands.peaks.PeakFinder` and find peaks in UV-vis spectra.

        Parameters
        ----------
        args : argparse.Namespace
            The command line args for peak detection.
        """
        print(PeakFinder.logo)
        _handle_path(args)
        self.args = args
        self.peak_labels = []
        self.dataset = Dataset(path=self.args.path, view_only=False)
        self.args.time = self.dataset.spectra_times[0]
        self.spectrum = self._get_spectrum()
        self.peaks = self.find_peaks()
        self.plot_peaks()

    def find_peaks(self) -> dict:
        """
        Find peaks in UV-vis spectra.

        Peak detection can be performed using local maxima or \
        first derivative methods.

        Returns
        -------
        peaks : dict
            The found peaks ``{'peaks': list[int], 'info': pd.DataFrame}``. \
            The peak info is a :class:`pandas.DataFrame` with the peak wavelengths \
            (index) and their respective absorbance values ``'abs'`` and epsilon values \
            ``'epsilon'`` (if a molar concentration was provided).
        """
        if self.args.method == 'localmax':
            peaks = find_peaks(
                spectrum=self.spectrum,
                num_peaks=self.args.num_peaks,
                conc=self.args.concentration,
                p_win=self.args.peak_window,
                s_win=self.args.smooth_window,
                dist=self.args.distance,
                prom=self.args.prominance,
                max_iter=self.args.max_iter
            )

        if self.args.method == 'deriv':
            peaks = find_peaks_dxdy(
                spectrum=self.spectrum,
                conc=self.args.concentration,
                p_win=self.args.peak_window,
                s_win=self.args.smooth_window
            )

        return peaks

    def _update_plot(self, val) -> None:
        """Update the plot when the time slider is changed."""
        self.args.time = val
        self.spectrum = self._get_spectrum()
        self.peaks = self.find_peaks()

        self.spectrum_scatter.set_ydata(self.spectrum)
        self.smooth_spectrum.set_ydata(smooth_spectrum(self.spectrum))
        self.peak_scatter.set_data(
            self.peaks['info']['abs'].index,
            self.peaks['info']['abs']
        )

        self._adjust_ybounds()
        self._label_peaks()

        self.fig.canvas.draw_idle()

    def _get_spectrum(self) -> pd.DataFrame:
        return self.dataset.raw_spectra.loc[:, [self.args.time]]

    def plot_peaks(self) -> None:
        """Generate an interactive peak detection plot with time slider."""
        subplot: tuple[Figure, Axes] = plt.subplots()
        self.fig, self.ax = subplot
        self.fig.suptitle('Peak Finder', fontweight='bold')
        self.fig.subplots_adjust(bottom=0.2)
        self.ax.set(
            title=self.dataset.name,
            xlabel='Wavelength (nm)',
            ylabel='Absorbance (AU)',
            xlim=(self.spectrum.index.min(), self.spectrum.index.max())
        )

        self.spectrum_scatter, = self.ax.plot(
            self.spectrum.index,
            self.spectrum,
            'k.',
            zorder=0
        )
        self.smooth_spectrum, = self.ax.plot(
            self.spectrum.index,
            smooth_spectrum(self.spectrum),
            'c',
            zorder=1
        )
        self.peak_scatter, = self.ax.plot(
            self.peaks['info']['abs'].index,
            self.peaks['info']['abs'],
            'r+',
            zorder=2
        )

        print(type(self.spectrum_scatter))

        self._label_peaks()

        ax_time = self.fig.add_axes([0.2, 0.03, 0.65, 0.03])
        time_slider = Slider(
            ax=ax_time,
            label='Time (s)',
            valmin=min(self.dataset.raw_spectra.columns),
            valmax=max(self.dataset.raw_spectra.columns),
            valinit=self.args.time,
            valstep=self.dataset.spectra_times
        )

        time_slider.on_changed(self._update_plot)

        plt.show()
        self._print_peaks()

    def _label_peaks(self) -> None:
        self._clear_peak_labels()
        self.peak_labels = []

        for peak in self.peaks['peaks']:
            self.peak_labels.append(
                self.ax.annotate(
                    text=str(peak),
                    xy=(peak, self.peaks['info']['abs'].loc[peak] + 0.01),
                    color='r',
                    fontweight='bold'
                )
            )

    def _clear_peak_labels(self) -> None:
        for label in self.peak_labels:
            label.remove()

    def _adjust_ybounds(self) -> None:
        if self.peaks['info']['abs'].max() * 1.1 > self.ax.get_ylim()[1]:
            self.ax.set_ylim(top=self.peaks['info']['abs'].max() * 1.1)

    def _print_peaks(self) -> str:
        out = []

        has_epsilon = 'epsilon' in self.peaks['info'].columns
        table_width = 34 if has_epsilon else 20
        headings = ['λ', 'abs'] + (['epsilon'] if has_epsilon else [])

        table_headings = f'│ \033[1m{headings[0]:^4}   '
        table_headings += ('   '.join([f'{heading:^11}' for heading in headings[1:]]))
        table_headings += ('\033[22m │')

        out.append('┌' + '─' * table_width + '┐')
        out.append(table_headings)
        out.append('├' + '─' * table_width + '┤')

        for wavelength in self.peaks['info'].index:
            row = f'│ {wavelength:^4}   {self.peaks['info']['abs'].loc[wavelength]:^11.3e}'
            row += f'   {self.peaks['info']['epsilon'].loc[wavelength]:^11.3e} │' if has_epsilon else ' │'
            out.append(row)

        out.append('└' + '─' * table_width + '┘')

        print('\n'.join(out))

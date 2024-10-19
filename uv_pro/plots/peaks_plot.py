import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from matplotlib.text import Annotation
from matplotlib.widgets import Slider
from uv_pro.peakfinder import PeakFinder
from uv_pro.peaks import smooth_spectrum


class PeaksPlot:
    def __init__(self, pf: PeakFinder, **fig_kw) -> None:
        self.pf = pf
        self.fig, self.ax = self._create_fig(**fig_kw)
        self.plot_peaks()

    def _create_fig(self, **fig_kw):
        subplot: tuple[Figure, Axes] = plt.subplots(**fig_kw)
        fig, ax = subplot
        fig.suptitle('Peak Finder', fontweight='bold')
        fig.subplots_adjust(bottom=0.2)

        ax.set(
            title=self.pf.dataset.name,
            xlabel='Wavelength (nm)',
            ylabel='Absorbance (AU)',
            xlim=(self.pf.spectrum.index.min(), self.pf.spectrum.index.max())
        )

        return fig, ax

    def plot_peaks(self) -> None:
        """Generate an interactive peak detection plot with time slider."""
        self.spectrum_scatter = self._spectrum_scatter_plot(
            self.ax,
            self.pf.spectrum
        )

        self.smoothed_plot = self._smoothed_plot(
            self.ax,
            pd.DataFrame(
                smooth_spectrum(self.pf.spectrum, s_win=self.pf.s_win),
                index=self.pf.spectrum.index
            )
        )

        self.peak_scatter = self._peak_scatter_plot(
            self.ax,
            self.pf.peaks['info']['abs']
        )

        self._label_peaks()

        time_slider = Slider(
            ax=self.fig.add_axes([0.2, 0.03, 0.65, 0.03]),
            label='Time (s)',
            valmin=min(self.pf.dataset.raw_spectra.columns),
            valmax=max(self.pf.dataset.raw_spectra.columns),
            valinit=self.pf.time,
            valstep=self.pf.dataset.spectra_times,
            color='#0400FF',
            initcolor='none'
        )

        time_slider.on_changed(self._update_plot)

        plt.show()

    def _update_plot(self, val) -> None:
        """Update the plot when the time slider is changed."""
        self._update_peakfinder(val)

        self._update_spectrum_scatter()
        self._update_smoothed_plot()
        self._update_peak_scatter()

        self._adjust_ybounds()
        self._label_peaks()

        self.fig.canvas.draw_idle()

    def _update_peakfinder(self, val: float):
        setattr(self.pf, 'time', val)
        setattr(self.pf, 'spectrum', self.pf._get_spectrum())
        setattr(self.pf, 'peaks', self.pf.find_peaks())

    def _update_spectrum_scatter(self):
        self.spectrum_scatter.set_ydata(self.pf.spectrum)

    def _update_smoothed_plot(self):
        self.smoothed_plot.set_ydata(
            smooth_spectrum(
                self.pf.spectrum,
                s_win=self.pf.s_win
            )
        )

    def _update_peak_scatter(self):
        self.peak_scatter.set_data(
            self.pf.peaks['info']['abs'].index,
            self.pf.peaks['info']['abs']
        )

    def _spectrum_scatter_plot(self, ax: Axes, spectrum: pd.DataFrame):
        plot, = ax.plot(
            spectrum.index,
            spectrum,
            color='0.6',
            marker='o',
            linestyle='',
            zorder=0
        )

        return plot

    def _smoothed_plot(self, ax: Axes, spectrum: pd.DataFrame):
        plot, = ax.plot(
            self.pf.spectrum.index,
            smooth_spectrum(self.pf.spectrum, s_win=self.pf.s_win),
            color='k',
            zorder=1
        )

        return plot

    def _peak_scatter_plot(self, ax: Axes, peaks: pd.Series):
        plot, = ax.plot(
            peaks.index,
            peaks,
            color='#0400FF',
            marker='|',
            markersize=15,
            linestyle='',
            zorder=2
        )

        return plot

    def _label_peaks(self) -> None:
        self._clear_peak_labels(self.ax)
        self.peak_labels = []

        for peak in self.pf.peaks['peaks']:
            self.peak_labels.append(
                self.ax.annotate(
                    text=str(peak),
                    xy=(peak, self.pf.peaks['info']['abs'].loc[peak] + 0.01),
                    color='#0400FF',
                    fontweight='bold',
                    fontsize='large',
                    zorder=3
                )
            )

    def _clear_peak_labels(self, ax: Axes) -> None:
        [child.remove() for child in ax.get_children() if isinstance(child, Annotation)]

    def _adjust_ybounds(self) -> None:
        if self.pf.peaks['info']['abs'].max() * 1.1 > self.ax.get_ylim()[1]:
            self.ax.set_ylim(top=self.pf.peaks['info']['abs'].max() * 1.1)

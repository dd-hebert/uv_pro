from functools import partial
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from matplotlib.lines import Line2D
from matplotlib.text import Annotation
from matplotlib.widgets import Slider
from uv_pro.peakfinder import PeakFinder
from uv_pro.peaks import smooth_spectrum


SPLASH = '\n'.join(
    [
        '\n┏┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┓',
        '┇ uv_pro Peak Finder ┇',
        '┗┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┛',
        'Close plot window to continue.\n'
    ]
)


def plot_peakfinder(pf: PeakFinder, **fig_kw) -> None:
    """Interactive peak finder plot."""
    print(SPLASH)
    fig, ax = _create_fig(pf, **fig_kw)

    spectrum_scatter = _plot_spectrum_scatter(ax, pf)
    smoothed_plot = _plot_smoothed_spectrum(ax, pf)
    peak_scatter = _plot_peak_scatter(ax, pf)
    _label_peaks(ax, pf)

    time_slider = Slider(
        ax=fig.add_axes([0.2, 0.03, 0.65, 0.03]),
        label='Time (s)',
        valmin=min(pf.dataset.raw_spectra.columns),
        valmax=max(pf.dataset.raw_spectra.columns),
        valinit=pf.time,
        valstep=pf.dataset.spectra_times,
        color='#0400FF',
        initcolor='none'
    )

    update_args = (pf, fig, ax, spectrum_scatter, smoothed_plot, peak_scatter)
    time_slider.on_changed(partial(_update_plot, *update_args))

    plt.show()


def _create_fig(pf: PeakFinder, **fig_kw):
    subplot: tuple[Figure, Axes] = plt.subplots(**fig_kw)
    fig, ax = subplot
    fig.suptitle('Peak Finder', fontweight='bold')
    fig.subplots_adjust(bottom=0.2)

    ax.set(
        title=pf.dataset.name,
        xlabel='Wavelength (nm)',
        ylabel='Absorbance (AU)',
        xlim=(pf.spectrum.index.min(), pf.spectrum.index.max())
    )

    return fig, ax


def _update_plot(pf: PeakFinder, fig: Figure, ax: Axes, spectrum_scatter: Line2D,
                 smoothed_plot: Line2D, peak_scatter: Line2D, val: float) -> None:
    """Update the plot when the time slider is changed."""
    def _update_peakfinder():
        setattr(pf, 'time', val)
        setattr(pf, 'spectrum', pf._get_spectrum())
        setattr(pf, 'peaks', pf.find_peaks())

    def _update_spectrum_scatter():
        spectrum_scatter.set_ydata(pf.spectrum)

    def _update_smoothed_plot():
        smoothed_plot.set_ydata(smooth_spectrum(pf.spectrum, s_win=pf.s_win))

    def _update_peak_scatter(peaks: pd.DataFrame):
        peak_scatter.set_data(peaks.index, peaks)

    def _adjust_ybounds(peaks: pd.DataFrame) -> None:
        ymax = peaks.max() * 1.1
        if ymax > ax.get_ylim()[1]:
            ax.set_ylim(top=ymax)

    _update_peakfinder()
    _update_spectrum_scatter()
    _update_smoothed_plot()
    _update_peak_scatter(pf.peaks['info']['abs'])
    _adjust_ybounds(pf.peaks['info']['abs'])
    _label_peaks(ax, pf)

    fig.canvas.draw_idle()


def _plot_spectrum_scatter(ax: Axes, pf: PeakFinder):
    plot, = ax.plot(
        pf.spectrum.index,
        pf.spectrum,
        color='0.6',
        marker='o',
        linestyle='',
        zorder=0
    )

    return plot


def _plot_smoothed_spectrum(ax: Axes, pf: PeakFinder):
    spectrum = pd.DataFrame(
        smooth_spectrum(pf.spectrum, s_win=pf.s_win),
        index=pf.spectrum.index
    )

    plot, = ax.plot(
        spectrum.index,
        spectrum,
        color='k',
        zorder=1
    )

    return plot


def _plot_peak_scatter(ax: Axes, pf: PeakFinder):
    peaks = pf.peaks['info']['abs']

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


def _label_peaks(ax: Axes, pf: PeakFinder) -> None:
    _clear_peak_labels(ax)
    peak_labels = []

    for peak in pf.peaks['peaks']:
        peak_labels.append(
            ax.annotate(
                text=str(peak),
                xy=(peak, pf.peaks['info']['abs'].loc[peak] + 0.01),
                color='#0400FF',
                fontweight='bold',
                fontsize='large',
                zorder=3
            )
        )


def _clear_peak_labels(ax: Axes) -> None:
    [child.remove() for child in ax.get_children() if isinstance(child, Annotation)]

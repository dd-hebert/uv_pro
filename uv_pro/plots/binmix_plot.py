"""
Interactive Binary Mixture solver plot.

@author: David Hebert
"""

from functools import partial

import matplotlib.colors as colors
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.collections import QuadMesh
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.text import Annotation
from matplotlib.widgets import Slider

from uv_pro.binarymixture import BinaryMixture


def plot_binarymixture(bm: BinaryMixture, **fig_kw) -> None:
    """
    Interactive binary mixture solver plot.

    A 1x3 plot showing:
        Overlaid raw and fitted spectra.
        A difference spectrum between raw and fitted data.
        A color mesh of linear combinations of mixture components.

    Parameters
    ----------
    binary_mixture : :class:`~uv_pro.binarymix.BinaryMixture`.
        The :class:`~uv_pro.binarymix.BinaryMixture` to plot.
    """
    fig, ax_binmix, ax_diff, ax_mesh = _create_fig(**fig_kw)

    _ = _mixture_subplot(ax_binmix, bm)
    fit_plot = _fit_subplot(ax_binmix, bm)
    diff_plot = _difference_subplot(ax_diff, bm)
    _, mesh_plot_marker = _heatmap_subplot(ax_mesh, bm)
    _label_mean_squared_error(ax_diff, bm.mean_squared_error())

    component_a_slider = Slider(
        fig.add_axes([0.2, 0.08, 0.65, 0.03]),
        'Component A',
        0,
        bm.coeff_a_max,
        valinit=bm.coeff_a,
        valstep=0.01,
        color='#0032FF',
    )

    component_b_slider = Slider(
        fig.add_axes([0.2, 0.03, 0.65, 0.03]),
        'Component B',
        0,
        bm.coeff_b_max,
        valinit=bm.coeff_b,
        valstep=0.01,
        color='#FF3200',
    )

    update_args = (bm, fig, fit_plot, diff_plot, mesh_plot_marker, ax_diff)
    component_a_slider.on_changed(partial(_update_plots, *update_args, 'coeff_a'))
    component_b_slider.on_changed(partial(_update_plots, *update_args, 'coeff_b'))

    plt.show()


def _create_fig(**fig_kw) -> tuple[Figure, Axes, Axes, Axes]:
    fig, (ax_binmix, ax_diff, ax_mesh) = plt.subplots(1, 3, **fig_kw)
    fig.suptitle('Binary Mixture Fitting', fontweight='bold')
    fig.subplots_adjust(bottom=0.2)

    return fig, ax_binmix, ax_diff, ax_mesh


def _update_plots(
    bm: BinaryMixture,
    fig: Figure,
    fit_plot: Line2D,
    diff_plot: Line2D,
    mesh_plot_marker: Line2D,
    ax_diff: Axes,
    coeff: str,
    val: float,
) -> None:
    """Update plots when a slider is changed."""

    def update_binary_mixture() -> None:
        setattr(bm, coeff, val)
        setattr(bm, 'fit', bm.linear_combination(bm.coeff_a, bm.coeff_b))

    def update_fit_plot() -> None:
        fit_plot.set_color(
            _get_fit_color(bm.coeff_a, bm.coeff_a_max, bm.coeff_b, bm.coeff_b_max)
        )
        fit_plot.set_ydata(bm.fit)

    def update_diff_plot() -> None:
        diff = bm.difference_spectrum()
        diff_plot.set_ydata(diff)
        diff_plot_ylim_max = max(abs(max(diff.min(), diff.max(), key=abs) * 1.1), 1.0)
        ax_diff.set_ylim(-diff_plot_ylim_max, diff_plot_ylim_max)
        _label_mean_squared_error(ax_diff, bm.mean_squared_error())

    def update_mesh_plot():
        mesh_plot_marker.set_data([bm.coeff_a], [bm.coeff_b])

    update_binary_mixture()
    update_fit_plot()
    update_diff_plot()
    update_mesh_plot()

    fig.canvas.draw_idle()


def _mixture_subplot(ax: Axes, bm: BinaryMixture) -> Line2D:
    ax.set(
        title='Fitting Spectra Overlay',
        xlabel='Wavelength (nm)',
        ylabel='Absorbance (AU)',
        xlim=(bm.mixture.index.min(), bm.mixture.index.max()),
        ylim=(ax.get_ylim()[0], bm.mixture.max() * 1.1),
    )

    (plot,) = ax.plot(
        bm.mixture.index,
        bm.mixture,
        color='k',
        marker='o',
        linestyle='',
        zorder=0,
    )

    return plot


def _fit_subplot(ax: Axes, bm: BinaryMixture) -> Line2D:
    rgb = _get_fit_color(
        bm.coeff_a,
        bm.coeff_a_max,
        bm.coeff_b,
        bm.coeff_b_max,
    )

    (plot,) = ax.plot(
        bm.fit.index,
        bm.fit,
        color=rgb,
        # marker='.',
        linestyle='-',
        linewidth=4,
        zorder=1,
    )

    return plot


def _get_fit_color(
    a: float, a_max: float, b: float, b_max: float
) -> tuple[float, float, float]:
    blue = min(max(a / a_max, 0), 1)
    red = min(max(b / b_max, 0), 1)

    return red, 0.2, blue


def _difference_subplot(ax: Axes, bm: BinaryMixture) -> Line2D:
    spectrum = bm.difference_spectrum()
    ylim_max = max(max(map(abs, (spectrum.min(), spectrum.max()))) * 1.1, 1.0)

    ax.set(
        title='Difference Spectrum',
        xlabel='Wavelength (nm)',
        # ylabel='Absorbance (AU)',
        xlim=(spectrum.index.min(), spectrum.index.max()),
        ylim=(-ylim_max, ylim_max),
    )

    (plot,) = ax.plot(
        spectrum.index,
        spectrum,
        color='k',
        marker='.',
        linestyle='',
        zorder=0,
    )

    return plot


def _label_mean_squared_error(ax: Axes, mse: float) -> None:
    _clear_label(ax)

    ax.annotate(
        text=f'MSE = {mse}',
        xy=(0.02, 0.02),
        xycoords='axes fraction',
        color='#000000',
        fontweight='bold',
        fontsize='medium',
        zorder=3,
    )


def _clear_label(ax: Axes) -> None:
    [child.remove() for child in ax.get_children() if isinstance(child, Annotation)]


def _heatmap_subplot(ax: Axes, bm: BinaryMixture) -> tuple[QuadMesh, Line2D]:
    ax.set(
        title='Fitting Heatmap',
        xlabel='Component A',
        ylabel='Component B',
    )

    x, y, z = _compute_mesh(bm)

    plot = ax.pcolormesh(
        x,
        y,
        z,
        norm=colors.LogNorm(vmin=z.min(), vmax=z.max()),
        cmap='BuPu_r',
        shading='auto',
    )

    (marker,) = ax.plot(bm.coeff_a, bm.coeff_b, color='k', marker='+', linestyle='')
    return plot, marker


def _compute_mesh(bm: BinaryMixture) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    comp_a = bm.component_a.to_numpy().flatten()
    comp_b = bm.component_b.to_numpy().flatten()
    spectrum = bm.mixture.to_numpy().flatten()

    rng_a = np.linspace(
        0, bm.coeff_a_max, num=int(bm.coeff_a_max / 0.01), endpoint=True
    )
    rng_b = np.linspace(
        0, bm.coeff_b_max, num=int(bm.coeff_b_max / 0.01), endpoint=True
    )

    a_vals, b_vals = np.meshgrid(rng_a, rng_b, indexing='ij')
    combinations = a_vals[:, :, np.newaxis] * comp_a + b_vals[:, :, np.newaxis] * comp_b
    squared_diffs = (spectrum - combinations) ** 2

    return a_vals, b_vals, np.mean(squared_diffs, axis=2)

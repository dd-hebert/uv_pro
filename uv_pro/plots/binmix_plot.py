"""
Interactive Binary Mixture solver plot.

@author: David Hebert
"""
from functools import partial
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.collections import QuadMesh
import matplotlib.colors as colors
from matplotlib.widgets import Slider
from matplotlib.text import Annotation
from uv_pro.binarymix import BinaryMixture


class BinMixPlot:
    """
    Interactive Binary Mixture Solver Plot.

    A 1x3 plot showing:
        Overlaid raw and fitted spectra.
        A difference spectrum between raw and fitted data.
        A color mesh of linear combinations of mixture components.
    """
    logo = '\n'.join(
        [
            '\n┏┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┓',
            '┇ uv_pro Binary Mixture Fitter ┇',
            '┗┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┛',
            'Close plot window to continue.\n'
        ]
    )

    def __init__(self, binary_mixture: BinaryMixture, **fig_kw) -> None:
        """
        Initialize a :class:`~uv_pro.plots.BinMixPlot` and show an interactive plot.

        Parameters
        ----------
        binary_mixture : :class:`~uv_pro.binarymix.BinaryMixture`.
            The :class:`~uv_pro.binarymix.BinaryMixture` to plot.
        """
        print(BinMixPlot.logo)
        self.bm = binary_mixture
        self.fig, (self.ax_binmix, self.ax_diff, self.ax_mesh) = self._create_fig(**fig_kw)
        self.plot()

    def _create_fig(self, **fig_kw) -> tuple[Figure, tuple[Axes, Axes, Axes]]:
        fig, (ax_binmix, ax_diff, ax_mesh) = plt.subplots(1, 3, **fig_kw)
        fig.suptitle('Binary Mixture Fitting', fontweight='bold')
        fig.subplots_adjust(bottom=0.2)
        return fig, (ax_binmix, ax_diff, ax_mesh)

    def plot(self) -> None:
        """Generate an interactive peak detection plot with time slider."""
        self.mixture_plot = self._mixture_subplot(
            self.ax_binmix,
            self.bm.mixture
        )

        self.fit_plot = self._fit_subplot(
            self.ax_binmix,
            self.bm.fit,
            rgb=self._get_fit_color()
        )

        self.diff_plot = self._difference_subplot(
            self.ax_diff,
            self.bm.difference_spectrum()
        )

        self._label_mean_squared_error(
            self.ax_diff,
            self.bm.mean_squared_error()
        )

        _, self.mesh_plot_dot = self._mesh_plot(
            self.ax_mesh,
            *self._compute_mesh(),
            xy=[self.bm.coeff_a, self.bm.coeff_b]
        )

        component_a_slider = Slider(
            self.fig.add_axes([0.2, 0.08, 0.65, 0.03]),
            label='Component A',
            valmin=0,
            valmax=self.bm.coeff_a_max,
            valinit=self.bm.coeff_a,
            valstep=0.01,
            color='#0032FF',
        )

        component_b_slider = Slider(
            self.fig.add_axes([0.2, 0.03, 0.65, 0.03]),
            label='Component B',
            valmin=0,
            valmax=self.bm.coeff_b_max,
            valinit=self.bm.coeff_b,
            valstep=0.01,
            color='#FF3200',
        )

        component_a_slider.on_changed(partial(self._update_plots, 'coeff_a'))
        component_b_slider.on_changed(partial(self._update_plots, 'coeff_b'))

        plt.show()

    def _update_plots(self, coeff_name, val) -> None:
        """Update plots when a slider is changed."""
        self._update_fit_plot(coeff_name, val)
        self._update_diff_plot()

        if self.mesh_plot_dot:
            self.mesh_plot_dot.set_data([self.bm.coeff_a], [self.bm.coeff_b])

        self.fig.canvas.draw_idle()

    def _update_fit_plot(self, coeff, val) -> None:
        setattr(self.bm, coeff, val)
        setattr(self.bm, 'fit', self.bm.linear_combination(self.bm.coeff_a, self.bm.coeff_b))
        self.fit_plot.set_color(self._get_fit_color())
        self.fit_plot.set_ydata(self.bm.fit)

    def _update_diff_plot(self) -> None:
        diff = self.bm.difference_spectrum()
        self.diff_plot.set_ydata(diff)
        diff_plot_ylim_max = max(abs(max(diff.min(), diff.max(), key=abs) * 1.1), 1.0)
        self.ax_diff.set_ylim(-diff_plot_ylim_max, diff_plot_ylim_max)
        self._label_mean_squared_error(self.ax_diff, self.bm.mean_squared_error())

    def _mixture_subplot(self, ax: Axes, spectrum: pd.Series) -> Line2D:
        ax.set(
            title='Fitting Spectra Overlay',
            xlabel='Wavelength (nm)',
            ylabel='Absorbance (AU)',
            xlim=(spectrum.index.min(), spectrum.index.max()),
            ylim=(ax.get_ylim()[0], spectrum.max() * 1.1)
        )

        plot, = ax.plot(
            spectrum.index,
            spectrum,
            color='k',
            marker='o',
            linestyle='',
            zorder=0
        )

        return plot

    def _fit_subplot(self, ax: Axes, spectrum: pd.Series, rgb: tuple[int, int, int] = (0, 0, 0)) -> Line2D:
        plot, = ax.plot(
            spectrum.index,
            spectrum,
            color=rgb,
            # marker='.',
            linestyle='-',
            linewidth=4,
            zorder=1
        )

        return plot

    def _get_fit_color(self) -> tuple[float, float, float]:
        blue = min(max(self.bm.coeff_a / self.bm.coeff_a_max, 0), 1)
        red = min(max(self.bm.coeff_b / self.bm.coeff_b_max, 0), 1)

        return red, 0.2, blue

    def _difference_subplot(self, ax: Axes, spectrum: pd.Series) -> Line2D:
        ylim_max = max(max(map(abs, (spectrum.min(), spectrum.max()))) * 1.1, 1.0)

        ax.set(
            title='Difference Spectrum',
            xlabel='Wavelength (nm)',
            # ylabel='Absorbance (AU)',
            xlim=(spectrum.index.min(), spectrum.index.max()),
            ylim=(-ylim_max, ylim_max)
        )

        plot, = ax.plot(
            spectrum.index,
            spectrum,
            color='k',
            marker='.',
            linestyle='',
            zorder=0
        )

        return plot

    def _label_mean_squared_error(self, ax: Axes, mse: float) -> None:
        self._clear_label(ax)

        ax.annotate(
            text=f'MSE = {mse}',
            xy=(0.02, 0.02),
            xycoords='axes fraction',
            color='#000000',
            fontweight='bold',
            fontsize='medium',
            zorder=3
        )

    def _clear_label(self, ax: Axes) -> None:
        [child.remove() for child in ax.get_children() if isinstance(child, Annotation)]

    def _add_slider(self, fig: Figure, pos: tuple[float, float, float, float], label: str = '',
                    valmin: float = 0, valmax: float = 1.0, valinit: float = 0.5,
                    valstep: float = 0.1, color: str = '#FFFFFF', initcolor='none') -> Slider:
        slider = Slider(
            ax=fig.add_axes(pos),
            label=label,
            valmin=valmin,
            valmax=valmax,
            valinit=valinit,
            valstep=valstep,
            color=color,
            initcolor=initcolor
        )

        return slider

    def _mesh_plot(self, ax: Axes, x: np.ndarray, y: np.ndarray, z: np.ndarray,
                   xy: tuple[float, float] | None = None) -> tuple[QuadMesh, Line2D] | tuple[QuadMesh, None]:
        ax.set(
            title='Fitting Heatmap',
            xlabel='Component A',
            ylabel='Component B',
        )

        plot = ax.pcolormesh(
            x, y, z,
            norm=colors.LogNorm(vmin=z.min(), vmax=z.max()),
            cmap='BuPu_r',
            shading='auto'
        )

        if xy:
            dot, = ax.plot(*xy, color='k', marker='+', linestyle='')
            return plot, dot

        return plot, None

    def _compute_mesh(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        comp_a = self.bm.component_a.to_numpy().flatten()
        comp_b = self.bm.component_b.to_numpy().flatten()
        spectrum = self.bm.mixture.to_numpy().flatten()

        rng_a = np.linspace(0, self.bm.coeff_a_max, num=int(self.bm.coeff_a_max / 0.01), endpoint=True)
        rng_b = np.linspace(0, self.bm.coeff_b_max, num=int(self.bm.coeff_b_max / 0.01), endpoint=True)
        a_vals, b_vals = np.meshgrid(rng_a, rng_b, indexing='ij')

        combinations = a_vals[:, :, np.newaxis] * comp_a + b_vals[:, :, np.newaxis] * comp_b

        squared_diffs = (spectrum - combinations) ** 2

        return a_vals, b_vals, np.mean(squared_diffs, axis=2)

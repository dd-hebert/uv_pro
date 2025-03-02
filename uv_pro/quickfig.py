"""
Make quick figures.

Create and export figures quickly with custom plot titles and other settings.
Quick figure behavior is determined by the settings used to process a UV-vis
dataset.

@author: David Hebert
"""

import os
import re

import matplotlib.pyplot as plt
from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from rich import print
from rich.columns import Columns

from uv_pro.dataset import Dataset
from uv_pro.io.export import export_figure
from uv_pro.plots.dataset_plots import (
    CMAPS,
    _processed_data_subplot,
    _time_traces_subplot,
)
from uv_pro.utils.prompts import user_choice


class QuickFig:
    """
    Contains methods for interactively creating UV-Vis figures.

    Attributes
    ----------
    dataset : :class:`~uv_pro.dataset.Dataset`
        The :class:`~uv_pro.dataset.Dataset` to create a quick figure with.
    exported_figure : str
        The filename of the exported quick figure.
    """

    def __init__(self, dataset: Dataset, cmap: str = 'default') -> None:
        """
        Create a quick figure with :class:`~uv_pro.dataset.Dataset`.

        Parameters
        ----------
        dataset : :class:`~uv_pro.dataset.Dataset`
            The Dataset to create a figure with.
        cmap : str, optional
            The name of a Matplotlib built-in colormap, by default 'default'.
        """
        self.dataset = dataset
        self.quick_figure(cmap=cmap)

    def quick_figure(
        self,
        title: str | None = None,
        x_bounds: tuple[int] | None = None,
        cmap: str | None = 'default',
    ) -> None:
        """
        Create a quick figure for exporting.

        If the :class:`~uv_pro.dataset.Dataset` to be plotted has \
        :attr:`~uv_pro.dataset.Dataset.chosen_traces`, these will \
        be included in the figure. Otherwise, only the \
        :attr:`~uv_pro.dataset.Dataset.processed_spectra` will be plotted.

        Parameters
        ----------
        title : str or None, optional
            The figure title. Default is None.
        x_bounds : tuple[int, int] or None, optional
            The processed data plot x-axis bounds. Default is None \
            (bounds determined automatically).
        """
        try:
            if title is None:
                title = self._get_plot_title()
            if x_bounds is None:
                x_bounds = self._get_plot_xbounds()
            if cmap is None:
                cmap = self._get_colormap()

        except (EOFError, KeyboardInterrupt):
            return

        if self.dataset.chosen_traces is None:
            fig, ax_processed_data = self._processed_data_plot(cmap)

        else:
            fig, (ax_processed_data, ax_traces) = self._1x2_plot(cmap)

        fig.suptitle(title, fontweight='bold', wrap=True)
        self._touchup_processed_data_plot(ax_processed_data, x_bounds)

        print('Close plot window to continue...', end='\n')
        plt.show()

        self._prompt_for_changes(fig, title, x_bounds)

    def export(self, fig: Figure) -> str:
        output_dir = os.path.dirname(self.dataset.path)
        filename = os.path.splitext(self.dataset.name)[0]
        return export_figure(fig, output_dir, filename)

    def _get_plot_title(self) -> str:
        title = input('Enter a plot title: ')
        return title

    def _get_plot_xbounds(self) -> tuple[int, int]:
        pattern = re.compile('([0-9]+)[ ]+([0-9]+)')
        x_bounds = input('Enter x-axis bounds [min max]: ').strip()
        match = re.search(pattern, x_bounds)

        while match is None:
            x_bounds = input('Invalid input. Enter x-axis bounds [min max]: ').strip()
            match = re.search(pattern, x_bounds)

        x_bounds = [bound for bound in map(int, match.groups())]
        return tuple(x_bounds)

    def _get_colormap(self) -> str:
        cmap = input('Enter a colormap name: ')

        while cmap not in CMAPS:
            if cmap in ['list', 'l']:
                print(Columns(CMAPS, column_first=True))

            else:
                print('Invalid colormap. Type "list" for the list of valid colormaps.')

            cmap = input('Enter a colormap name: ')

        return cmap

    def _processed_data_plot(self, cmap: str = 'default') -> tuple[Figure, Axes]:
        """Create processed data plot."""
        fig, ax_processed_data = plt.subplots()
        _processed_data_subplot(ax_processed_data, self.dataset, cmap)
        ax_processed_data.set(title=None)
        return fig, ax_processed_data

    def _1x2_plot(self, cmap: str = 'default') -> tuple[Figure, tuple[Axes, Axes]]:
        """Create 1x2 plot with processed data and time traces."""
        fig, (ax_processed_data, ax_traces) = plt.subplots(
            nrows=1,
            ncols=2,
            figsize=(10, 5),
            layout='constrained',
            sharey=True,
        )

        _processed_data_subplot(ax_processed_data, self.dataset, cmap)
        _time_traces_subplot(ax_traces, self.dataset, show_slices=False)
        self._touchup_time_traces_plot(ax_traces)
        return fig, (ax_processed_data, ax_traces)

    def _touchup_processed_data_plot(self, ax: Axes, x_bounds: tuple[int, int]) -> None:
        """Modify x-axis bounds and plot text."""
        ax.set_title('UV-vis Spectra', fontstyle='normal')
        ax.set_xbound(*x_bounds)
        Artist.remove(ax.texts[0])
        t0 = int(self.dataset.processed_spectra.columns[0])
        t1 = int(self.dataset.processed_spectra.columns[-1])
        delta_t = t1 - t0

        ax.text(
            x=0.99,
            y=0.99,
            s=f'Δt = {delta_t} sec',
            verticalalignment='top',
            horizontalalignment='right',
            transform=ax.transAxes,
            color='gray',
            fontsize=8,
        )

    def _touchup_time_traces_plot(self, ax: Axes) -> None:
        """Modify plot tick labels and x-axis bounds."""
        ax.set_title('Time Traces', fontstyle='normal')
        ax.tick_params(labelleft=True)
        ax.set_xbound(
            int(self.dataset.processed_spectra.columns[0]),
            int(self.dataset.processed_spectra.columns[-1]),
        )

    def _prompt_for_changes(self, fig: Figure, title: str, x_bounds: tuple[int]) -> None:
        """
        Prompt the user for plot changes or export.

        Parameters
        ----------
        fig : Figure
            The current quick figure.
        title : str
            The quick figure plot title.
        x_bounds : tuple[int]
            The x-axis bounds for the processed data plot.
        """
        header = 'Make changes?'
        options = [
            {'key': '1', 'name': 'Save plot'},
            {'key': '2', 'name': 'Change title'},
            {'key': '3', 'name': 'Change x-axis bounds'},
            {'key': '4', 'name': 'Change colors'},
        ]

        if user_choices := user_choice(header, options):
            if '1' in user_choices:
                self.exported_figure = self.export(fig)
                return
            if '2' in user_choices:
                title = None
            if '3' in user_choices:
                x_bounds = None
            if '4' in user_choices:
                cmap = None

            self.quick_figure(title=title, x_bounds=x_bounds, cmap=cmap)

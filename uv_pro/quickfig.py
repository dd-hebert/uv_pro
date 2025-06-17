"""
Make quick figures.

Create and export figures quickly with custom plot titles and other settings.
Quick figure behavior is determined by the settings used to process a UV-vis
dataset.

@author: David Hebert
"""

import re
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from rich import print
from rich.columns import Columns

from uv_pro.const import CMAPS
from uv_pro.dataset import Dataset
from uv_pro.io.export import export_figure
from uv_pro.plots.dataset_plots import (
    _processed_data_subplot,
    _time_traces_subplot,
)
from uv_pro.utils.prompts import ask, autocomplete, checkbox


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
        self.exported_figure = None
        self.quick_figure(title=dataset.name, cmap=cmap)

    def quick_figure(
        self,
        title: str | None = None,
        x_bounds: tuple[int] | None = (300, 1100),
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
            The processed data plot x-axis bounds. Default is (300, 1100).
        cmap : str or None, optional
            Any valid matplotlib colormap. Default is 'default'.
        """
        try:
            if title is None:
                title = self._get_plot_title()
            if x_bounds is None:
                x_bounds = self._get_plot_xbounds()
            if cmap is None:
                cmap = self._get_colormap()

        except KeyboardInterrupt:
            return

        if self.dataset.chosen_traces is None:
            fig, ax_processed_data = self._processed_data_plot(cmap)

        else:
            fig, (ax_processed_data, ax_traces) = self._1x2_plot(cmap)

        fig.suptitle(title, fontweight='bold', wrap=True)
        self._touchup_processed_data_plot(ax_processed_data, x_bounds)

        print('Close plot window to continue...', end='\n')
        plt.show()

        self._prompt_for_changes(fig, title, x_bounds, cmap)

    def export(self, fig: Figure) -> str:
        output_dir = self.dataset.path.parent
        filename = Path(self.dataset.name).stem
        return export_figure(fig, output_dir, filename)

    def _get_plot_title(self) -> str:
        title = ask('Enter plot title:')

        if title is None:
            raise KeyboardInterrupt
        return title

    def _get_plot_xbounds(self) -> tuple[int, int]:
        pattern = re.compile(r'^\s*(\d+)\s+(\d+)\s*$')
        while True:
            x_bounds = ask('Enter x-axis bounds <MIN MAX>:')

            if x_bounds is None:
                raise KeyboardInterrupt

            match = pattern.match(x_bounds)
            if match:
                return tuple(map(int, match.groups()))

            print('Invalid input. Please enter two integers separated by space.')

    def _get_colormap(self) -> str:
        import difflib

        LIST_COMMANDS = {'list', 'l'}

        while True:
            # cmap = ask('Enter a colormap name:').lower()
            cmap = autocomplete(
                'Enter a colormap name:', choices=CMAPS.values()
            ).lower()

            if cmap is None:
                raise KeyboardInterrupt

            if cmap in LIST_COMMANDS:
                print(Columns(CMAPS, column_first=True))
                continue

            if cmap in CMAPS:
                return CMAPS[cmap]

            closest = difflib.get_close_matches(cmap, CMAPS)

            print(f'[repr.error]Invalid colormap:[/repr.error] "{cmap}"')

            if closest:
                print(f'\nDid you mean "{closest[0]}"?')

            print('\nType "list" for the list of valid colormaps.')

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

    def _prompt_for_changes(
        self, fig: Figure, title: str, x_bounds: tuple[int], cmap: str | None
    ) -> None:
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
        message = 'Make changes'
        options = [
            'Save plot',
            'Change title',
            'Change x-axis bounds',
            'Change colors',
        ]

        if user_selection := checkbox(message, options):
            if 'Save plot' in user_selection:
                self.exported_figure = self.export(fig)
                return
            if 'Change title' in user_selection:
                title = None
            if 'Change x-axis bounds' in user_selection:
                x_bounds = None
            if 'Change colors' in user_selection:
                cmap = None

            self.quick_figure(title=title, x_bounds=x_bounds, cmap=cmap)

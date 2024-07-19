"""
Make quick figures.

Create and export figures quickly with custom plot titles and other settings.
Quick figure behavior is determined by the settings used to process a UV-vis
dataset.

@author: David Hebert
"""

import re
import os
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.artist import Artist
from matplotlib.figure import Figure
from uv_pro.dataset import Dataset
import uv_pro.plots as uvplt
from uv_pro.utils.printing import prompt_user_choice
from uv_pro.io.export import export_figure


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
    def __init__(self, dataset: Dataset) -> None:
        self._print_logo()
        self.dataset = dataset
        self.quick_figure()

    def quick_figure(self, title: str = None, x_bounds: list[int] = None) -> None:
        """
        Create a quick figure for exporting.

        If the :class:`~uv_pro.dataset.Dataset` to be plotted has \
        :attr:`~uv_pro.dataset.Dataset.chosen_traces`, these will \
        be included in the figure. Otherwise, only the \
        :attr:`~uv_pro.dataset.Dataset.processed_spectra` will be plotted.

        Parameters
        ----------
        title : str, optional
            The figure title. Default is None.
        x_bounds : list[int, int], optional
            The processed data plot x-axis bounds. Default is None \
            (bounds determined automatically).
        """
        try:
            if title is None:
                title = self._get_plot_title()
            if x_bounds is None:
                x_bounds = self._get_plot_xbounds()

        except (EOFError, KeyboardInterrupt):
            return

        if self.dataset.chosen_traces is None:
            fig, ax_processed_data = self._processed_data_plot()

        else:
            fig, (ax_processed_data, ax_traces) = self._1x2_plot()

        fig.suptitle(title, fontweight='bold')
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

    def _get_plot_xbounds(self) -> list[int, int]:
        pattern = re.compile('([0-9]+)[ ]+([0-9]+)')
        x_bounds = input('Enter x-axis bounds [min max]: ').strip()
        match = re.search(pattern, x_bounds)

        while match is None:
            x_bounds = input('Invalid input. Enter x-axis bounds [min max]: ').strip()
            match = re.search(pattern, x_bounds)

        x_bounds = [bound for bound in map(int, match.groups())]
        return x_bounds

    def _processed_data_plot(self) -> tuple[Figure, Axes]:
        """Create processed data plot."""
        fig, ax_processed_data = plt.subplots()
        uvplt._processed_data_subplot(ax_processed_data, self.dataset)
        ax_processed_data.set(title=None)

        return fig, ax_processed_data

    def _1x2_plot(self) -> tuple[Figure, tuple[Axes, Axes]]:
        """Create 1x2 plot with processed data and time traces."""
        fig, (ax_processed_data, ax_traces) = plt.subplots(
            nrows=1,
            ncols=2,
            figsize=(10, 5),
            layout='constrained',
            sharey=True
        )

        uvplt._processed_data_subplot(ax_processed_data, self.dataset)
        uvplt._time_traces_subplot(ax_traces, self.dataset, show_slices=False)
        self._touchup_time_traces_plot(ax_traces)

        return fig, (ax_processed_data, ax_traces)

    def _touchup_processed_data_plot(self, ax: Axes, x_bounds: list[int, int]) -> None:
        """Modify x-axis bounds and plot text."""
        ax.set_title('UV-vis Spectra', fontstyle='normal')
        ax.set_xbound(*x_bounds)
        Artist.remove(ax.texts[0])
        delta_t = int(self.dataset.processed_spectra.columns[-1]) - int(self.dataset.processed_spectra.columns[0])
        ax.text(
            x=0.99,
            y=0.99,
            s=f'Δt = {delta_t} sec',
            verticalalignment='top',
            horizontalalignment='right',
            transform=ax.transAxes,
            color='gray',
            fontsize=8
        )

    def _touchup_time_traces_plot(self, ax: Axes) -> None:
        """Modify plot tick labels and x-axis bounds."""
        ax.set_title('Time Traces', fontstyle='normal')
        ax.tick_params(labelleft=True)
        ax.set_xbound(
            int(self.dataset.processed_spectra.columns[0]),
            int(self.dataset.processed_spectra.columns[-1])
        )

    def _prompt_for_changes(self, fig: Figure, title: str, x_bounds: list[int]) -> None:
        """
        Prompt the user for plot changes or export.

        Parameters
        ----------
        fig : Figure
            The current quick figure.
        title : str
            The quick figure plot title.
        x_bounds : list[int]
            The x-axis bounds for the processed data plot.
        """
        header = 'Make changes?'
        options = [
            {'key': '1', 'name': 'Save plot'},
            {'key': '2', 'name': 'Change title'},
            {'key': '3', 'name': 'Change x-axis bounds'}
        ]

        if user_choices := prompt_user_choice(header=header, options=options):
            if '1' in user_choices:
                self.exported_figure = self.export(fig)
            if '2' in user_choices:
                self.quick_figure(x_bounds=x_bounds)
            if '3' in user_choices:
                self.quick_figure(title=title)

    def _print_logo(self) -> None:
        print('\n┏┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┓')
        print('┇ uv_pro Quick Figure ┇')
        print('┗┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┛')
        print('Enter ctrl-c to quit.\n')

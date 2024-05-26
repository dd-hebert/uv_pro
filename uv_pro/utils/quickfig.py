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
from matplotlib.figure import Figure
from matplotlib.artist import Artist
from uv_pro.process import Dataset
import uv_pro.plots as uvplt


class QuickFig:
    def __init__(self, dataset: Dataset) -> None:
        self._print_logo()
        self.dataset = dataset

    def _print_logo(self) -> None:
        print('\n┏┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┓')
        print('┇ uv_pro Quick Figure ┇')
        print('┗┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┛')
        print('Enter ctrl-z or ctrl-c to quit.\n')

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

    def quick_figure(self, title=None, x_bounds=None) -> str | list:
        """
        Create a quick figure for exporting.

        If the :class:`~uv_pro.process.Dataset` to be plotted has \
        :attr:`~uv_pro.process.Dataset.chosen_traces`, these will \
        be included in the figure. Otherwise, only the \
        :attr:`~uv_pro.process.Dataset.processed_spectra` will be plotted.

        Parameters
        ----------
        title : str, optional
            The figure title. Default is None.
        x_bounds : list[int, int], optional
            The processed data plot x-axis bounds. Default is None \
            (bounds determined automatically).

        Returns
        -------
        str or list
            The filename of the exported figure (if figure is exported).
            Otherwise returns an empty list.
        """
        try:
            if title is None:
                title = self._get_plot_title()
            if x_bounds is None:
                x_bounds = self._get_plot_xbounds()

            if self.dataset.chosen_traces is None:  # Processed data plot only
                fig, ax_processed_data = plt.subplots()
                uvplt._processed_data_subplot(ax_processed_data, self.dataset)
                ax_processed_data.set(title=None)

            else:  # 1x2 plot (processed data + traces)
                fig, (ax_processed_data, ax_traces) = plt.subplots(
                    nrows=1,
                    ncols=2,
                    figsize=(10, 5),
                    layout='constrained',
                    sharey=True
                )
                uvplt._processed_data_subplot(ax_processed_data, self.dataset)
                uvplt._time_traces_subplot(ax_traces, self.dataset)
                self._touchup_time_traces_plot(ax_traces)

            fig.suptitle(title, fontweight='bold')
            self._touchup_processed_data_plot(ax_processed_data, x_bounds)

            print('Close plot window to continue...', end='\n')
            plt.show()

            return self._prompt_for_changes(fig, title, x_bounds)

        except EOFError:  # crtl-z
            return []

        except KeyboardInterrupt:  # ctrl-c
            return []

    def _touchup_processed_data_plot(self, ax, x_bounds) -> None:
        """Modify x-axis bounds and plot text."""
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

    def _touchup_time_traces_plot(self, ax) -> None:
        """Modify plot tick labels and x-axis bounds."""
        ax.tick_params(labelleft=True)
        ax.set_xbound(
            int(self.dataset.processed_spectra.columns[0]),
            int(self.dataset.processed_spectra.columns[-1])
        )

    def _prompt_for_changes(self, fig: Figure, title: str, x_bounds: tuple) -> str:
        """
        Prompt the user for plot changes or export.

        Parameters
        ----------
        fig : Figure
            The current quick figure.
        title : str
            The quick figure plot title.
        x_bounds : tuple
            The x-axis bounds for the processed dataa plot.

        Returns
        -------
        str
            The filename of the exported quick figure.
        """
        options = ['Save plot', 'Change title', 'Change x-axis bounds']

        prompt = f'\nMake changes?\n{'=' * 13}\n'
        prompt += '\n'.join([f'({i}) {option}' for i, option in enumerate(options, start=1)])
        prompt += '\n(q) Quit\n\nChoice: '

        valid_choices = [str(i) for i in range(1, len(options) + 1)] + ['q']
        user_choice = [char for char in input(prompt).strip().lower() if char in valid_choices]

        while not user_choice:
            print('\nInvalid selection. Enter one or more of the displayed options.')
            user_choice = [char for char in input(prompt).strip().lower() if char in valid_choices]

        if '1' in user_choice:
            return self.save_figure(fig)
        if '2' in user_choice:
            self.quick_figure(title=title)
        if '3' in user_choice:
            self.quick_figure(x_bounds=x_bounds)

    def save_figure(self, fig) -> str:
        save_path = os.path.join(os.path.dirname(self.dataset.path), f'{self.dataset.name}.png')
        fig.savefig(
            fname=save_path,
            format='png',
            dpi=600
        )
        return f'{self.dataset.name}.png'

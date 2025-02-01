from __future__ import annotations
from typing import TYPE_CHECKING
import os
import argparse
from functools import partial
import pandas as pd
from rich import box
from rich.columns import Columns
from rich.console import RenderableType, TextType, Group
from rich.panel import Panel
from rich.table import Table, Column
from rich.text import Text

if TYPE_CHECKING:
    from dataset import Dataset


STYLES = {
    'bold': 'bold medium_purple1',
    'highlight': 'grey0 on medium_purple3'
}


def truncate_title(title: str, max_length: int = 74) -> str:
    """Truncate strings longer than ``max_length`` using elipsis."""
    half = max_length // 2
    return title if len(title) < 74 else title[:half + 1] + '...' + title[-half:]


def splash(text: str, title: str, width: int = 80, **kwargs) -> Panel:
    """A pre-formatted ``Panel`` for splashes."""
    return Panel(
        Text(text, style='bold grey100', justify='center'),
        title=Text(title, style='table.title'),
        box=box.SIMPLE,
        border_style='grey27',
        width=width,
        **kwargs
    )


def table_panel(table: Table, title: str, subtitle: TextType | None = None,
                width: int = 80, **kwargs) -> Panel:
    """A pre-formatted ``Panel`` for displaying tables."""
    return Panel(
        table,
        title=Text(title, style=STYLES['highlight']),
        subtitle=Text(subtitle, style='table.caption') if subtitle else None,
        box=box.SIMPLE,
        width=width,
        **kwargs
    )


def fancy_panel(renderable: RenderableType, title: str,
                subtitle: TextType | None = None, width: int = 80,
                **kwargs) -> Panel:
    """A fancy pre-formatted rich ``Panel``."""
    return Panel(
        renderable,
        title=Text(title, style=STYLES['highlight']),
        subtitle=Text.assemble(subtitle, style='table.caption') if subtitle else None,
        box=box.ROUNDED,
        width=width,
        **kwargs
    )


def simple_panel(renderable: RenderableType, title: str, **kwargs) -> Panel:
    """A simple pre-formatted rich ``Panel``."""
    return Panel(
        renderable,
        title=Text(title, style=STYLES['highlight']),
        title_align='center',
        expand=False,
        box=box.MINIMAL,
        **kwargs
    )


def fancy_table(*columns, width: int = 77) -> Table:
    """A fancy pre-formatted rich ``Table``."""
    return Table(
        *columns,
        width=width,
        box=box.HORIZONTALS,
        collapse_padding=True
    )


class ProcessingOutput:
    """
    ``rich`` renderables for :class:`~uv_pro.dataset.Dataset``.

    Attributes
    ----------
    renderables : list[RenderableType]
        A list of ``rich`` renderables.
    title : str
        The title (filename) of the processed UV-vis file.
    """
    def __init__(self, dataset: Dataset) -> None:
        """
        Create ``rich`` renderables for :class:`~uv_pro.dataset.Dataset``.

        Parameters
        ----------
        dataset : :class:`~uv_pro.dataset.Dataset``
            The ``Dataset`` to pretty-print.
        """
        self.title = truncate_title(dataset.name)
        renderables = ['', self.processing_panel(dataset)]
        log = []

        if dataset.fit is not None:
            renderables.extend(['', self.fit_panel(dataset.fit)])

            log.extend(self._unable_to_fit(dataset))

        if dataset.init_rate is not None:
            renderables.extend(['', self.init_rate_panel(dataset.init_rate)])

        if log:
            renderables.extend(log)

        self.renderables = renderables

    def __rich__(self) -> Group:
        renderables = Group(*self.renderables)
        return renderables

    def _get_subtitle(self, dataset) -> list[Text]:
        subtitle = [
            Text.assemble('Total Spectra: ', (f'{len(dataset.raw_spectra.columns)}', STYLES['bold'])),
            Text.assemble('Total time: ', (f'{dataset.spectra_times.max()} s', STYLES['bold']))
        ]

        if dataset.cycle_time:
            subtitle.append(Text.assemble('Cycle time: ', (f'{dataset.cycle_time} s', STYLES['bold'])))

        return subtitle

    def processing_panel(self, dataset: Dataset) -> Panel:
        """Create a nicely formatted rich ``Panel`` for ``dataset``."""
        subtitle = self._get_subtitle(dataset)
        bold_text = partial(Text, style=STYLES['bold'])

        if not dataset.is_processed:
            return simple_panel(
                Text('\n').join(subtitle),
                title=self.title,
            )

        def left_table() -> Table:
            """Shows trimming and outliers info."""
            table = Table('', '', show_header=False, box=box.SIMPLE)

            if dataset.trim:
                for loc, val in zip(['start', 'end'], dataset.trim):
                    table.add_row(f'Trimmed {loc} (s)', bold_text(f'{val}'))

            table.add_row('Outliers found', bold_text(f'{len(dataset.outliers)}'))

            return table

        def right_table() -> Table:
            """Shows slicing info."""
            table = Table('', '', show_header=False, box=box.SIMPLE)

            if dataset.slicing is None:
                table.add_row('Spectra remaining', bold_text(f'{len(dataset.processed_spectra.columns)}'))

            else:
                table.add_row('Slicing mode', bold_text(f'{dataset.slicing["mode"]}'))

                if dataset.slicing['mode'] == 'gradient':
                    table.add_row('Slicing coefficient', bold_text(f'{dataset.slicing["coeff"]}'))
                    table.add_row('Slicing exponent', bold_text(f'{dataset.slicing["expo"]}'))

                table.add_row('Slices ', bold_text(f'{len(dataset.processed_spectra.columns)}'))

            return table

        return fancy_panel(
            Columns([left_table(), right_table()], expand=True, align='left'),
            title=self.title,
            subtitle=Text('\t').join(subtitle)
        )

    def fit_panel(self, fit: dict) -> Panel:
        """Create a nicely formatted rich ``Panel`` for fitting data."""
        table = fancy_table(
            Column('λ (nm)', justify='center', ratio=1),
            Column('kobs (s⁻¹)', justify='center', ratio=3),
            Column('abs_0 (a.u.)', justify='center', ratio=2),
            Column('abs_f (a.u.)', justify='center', ratio=2),
            Column('r²', justify='center', ratio=2),
        )

        for wavelength in fit['params'].columns:
            vals = fit['params'][wavelength]
            r2_color = 'red' if vals.loc['r2'] < 0.85 else 'none'
            table.add_row(
                str(wavelength),
                '{: .2e} ± {:.2e}'.format(vals.loc['kobs'], vals.loc['kobs ci']),
                '{: .3f}'.format(vals['abs_0']),
                '{: .3f}'.format(vals['abs_f']),
                Text('{:.4f}'.format(vals['r2']), style=r2_color),
            )

        equation = 'f(t) = abs_f + (abs_0 - abs_f) * exp(-kobs * t)'

        return table_panel(
            table,
            title='Exponential Fit Results',
            subtitle=f'Fit function: {equation}'
        )

    def init_rate_panel(self, init_rate: dict) -> Panel:
        """Create a nicely formatted rich ``Panel`` for initial rates data."""
        table = fancy_table(
            Column('λ (nm)', justify='center', ratio=1),
            Column('rate (a.u./s)', justify='center', ratio=3),
            Column('Δabs (%)', justify='center', ratio=2),
            Column('Δt (s)', justify='center', ratio=2),
            Column('r²', justify='center', ratio=2),
        )

        for wavelength in init_rate['params'].columns:
            vals = init_rate['params'][wavelength]
            r2_color = 'red' if vals.loc['r2'] < 0.85 else 'none'
            table.add_row(
                str(wavelength),
                '{: .2e} ± {:.2e}'.format(vals.loc['slope'], vals.loc['slope ci']),
                '{:.2%}'.format(vals['delta_abs_%']),
                '{:.1f}'.format(vals['delta_t']),
                Text('{:.4f}'.format(vals['r2']), style=r2_color),
            )

        return table_panel(
            table,
            title='Initial Rates Results'
        )

    def _unable_to_fit(self, dataset: Dataset) -> list[Text] | list:
        chosen_wavelengths = set(dataset.chosen_traces.columns)
        fit_wavelengths = set(dataset.fit['curves'].columns)

        unable_to_fit = [
            Text(f'Unable to fit exponential to {wavelength} nm.', style='red')
            for wavelength in chosen_wavelengths.difference(fit_wavelengths)
        ]

        return unable_to_fit


class PeaksOutput:
    """
    ``rich`` renderables for :py:mod:`~uv_pro.commands.peaks` results.

    Attributes
    ----------
    has_epsilon : bool
        Specifies if the peak detection results contain epsilon values.
    method : str
        The peak detection method.
    peaks : :class:`pandas.DataFrame`
        The peak detection output from :py:mod:`~uv_pro.commands.peaks`.
    """
    def __init__(self, args: argparse.Namespace, peaks: dict) -> None:
        """
        Create ``rich`` renderables for :py:mod:`~uv_pro.commands.peaks` results.

        Parameters
        ----------
        args : argparse.Namespace
            The command line args used for peak detection.
        peaks : dict
            The peak detection output.
        """
        self.peaks = peaks['info']
        self.method = args.method
        self.has_epsilon = 'epsilon' in self.peaks.columns

    def __rich__(self) -> Panel:
        return self._create_table_panel()

    def _create_table_panel(self) -> Panel:
        """Create a fancy rich ``Panel`` for peak detection data."""
        table = fancy_table(
            Column("λ", justify="center"),
            Column("abs", justify="center"),
            width=30,
        )

        if self.has_epsilon:
            table.add_column("ε", justify="center")

        for _, row in self.peaks.iterrows():
            table.add_row(
                f"{row.name}",
                f"{row['abs']:.3f}",
                f"{row['epsilon']:.3e}" if self.has_epsilon else None
            )

        return table_panel(
            table,
            title='Peak Finder Results',
            subtitle=f'Method: {self.method}',
            width=34
        )


class BinmixOutput:
    """
    ``rich`` renderables for the :py:mod:`~uv_pro.commands.binmix` command.

    Attributes
    ----------
    component_concs : list[float] | list[None]
        The concentrations of each component, if provided.
    component_paths : list[str]
        File paths to the component .csv files.
    results : :class:`pandas.DataFrame`
        The binmix fitting output.
    title : str
        The title (filename) of the fitted mixture .csv file.
    """
    def __init__(self, args: argparse.Namespace, results: pd.DataFrame):
        """
        Create ``rich`` renderables for the :py:mod:`~uv_pro.commands.binmix` command.

        Parameters
        ----------
        args : argparse.Namespace
            The command line args used with binmix.
        results : pd.DataFrame
            The binmix fitting output.
        """
        self.results = results
        self.title = truncate_title(os.path.basename(args.path))
        self.component_paths = [args.component_a, args.component_b]
        self.component_concs = [getattr(args, 'molarity_a', None), getattr(args, 'molarity_b', None)]

    def __rich__(self) -> Group:
        return Group(self.files_panel(), self.fit_panel())

    def files_panel(self) -> Panel:
        """Create a rich ``Panel`` for the binmix component .csv files."""
        tables = []

        for letter, path, conc in zip(['A', 'B'], self.component_paths, self.component_concs):
            table = Table(
                Column(f'Component {letter}', justify='center', overflow='fold'),
                caption=f'[{letter}]: {conc:.3e} (M)' if conc else None,
                width=35,
                box=box.ROUNDED,
                expand=False
            )

            row = Text.assemble(
                Text(f'{os.path.dirname(path)}\\', style='medium_purple4'),
                Text(f'{os.path.basename(path)}', style=STYLES['bold'])
            )

            table.add_row(row)
            tables.append(table)

        return Panel(
            Columns(tables, expand=True, align='center'),
            title=Text(self.title, style=STYLES['highlight']),
            width=80,
            box=box.SIMPLE,
            expand=False
        )

    def fit_panel(self) -> Panel:
        """Create a rich ``Panel`` for binmix fitting results."""
        table = fancy_table(
            Column('Label', justify='center', max_width=20, overflow='fold'),
            Column('Coeff. A', justify='center'),
            Column('[A] (M)', justify='center'),
            Column('Coeff. B', justify='center'),
            Column('[B] (M)', justify='center'),
            Column('MSE', justify='center')
        )

        for label in self.results.columns:
            vals = self.results[label]
            table.add_row(
                label,
                '{:.3}'.format(vals.loc['coeff_a']),
                '{:.2e}'.format(vals.loc['conc_a']) if vals.loc['conc_a'] else '--',
                '{:.3}'.format(vals.loc['coeff_b']),
                '{:.2e}'.format(vals.loc['conc_b']) if vals.loc['conc_b'] else '--',
                '{:.2e}'.format(vals.loc['MSE'])
            )

        return table_panel(
            table,
            title='Binary Mixture Fitting Results'
        )

"""
Functions for plotting and visualizing uv_pro Datasets.

@author: David Hebert
"""

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from cycler import cycler
from pandas import DataFrame
from uv_pro.dataset import Dataset


plt.style.use('seaborn-v0_8-bright')
CMAPS = sorted(plt.colormaps(), key=str.lower)


def plot_spectra(dataset: Dataset, spectra) -> None:
    """
    Show a simple spectra plot.

    Parameters
    ----------
    dataset : :class:`~uv_pro.dataset.Dataset`
        A :class:`~uv_pro.dataset.Dataset` containing the spectra to be plotted.
    spectra : :class:`pandas.DataFrame`
        The spectra to be plotted, such as :attr:`~uv_pro.dataset.Dataset.raw_spectra`
        or :attr:`~uv_pro.dataset.Dataset.processed_spectra`.
    """
    _, ax = plt.subplots()
    ax.set(xlabel='Wavelength (nm)', ylabel='Absorbance (AU)')
    plt.title(dataset.name, fontweight='bold')
    plt.plot(spectra)
    plt.xlim(200, 1100)
    plt.show()


def plot_time_traces(dataset: Dataset) -> None:
    """
    Plot the :attr:`~uv_pro.dataset.Dataset.time_traces` of a ``dataset``.

    Parameters
    ----------
    dataset : :class:`~uv_pro.dataset.Dataset`
        The :class:`~uv_pro.dataset.Dataset` containing the time traces to be
        plotted.
    """
    _, ax = plt.subplots()
    ax.set(xlabel='Time (s)', ylabel='Absorbance (AU)')
    plt.title(f'{dataset.name}\nTime Traces')
    plt.plot(dataset.time_traces)
    plt.ylim(auto=True)
    plt.xlim(auto=True)
    plt.show()


def plot_1x2(dataset: Dataset, cmap: str = 'default', **fig_kw) -> None:
    """
    Show the 1-by-2 plot.

    Show a 1-by-2 plot of :attr:`~uv_pro.dataset.Dataset.raw_spectra` and
    :attr:`~uv_pro.dataset.Dataset.processed_spectra` in ``dataset``.

    Parameters
    ----------
    dataset : :class:`~uv_pro.dataset.Dataset`
        The :class:`~uv_pro.dataset.Dataset` to be plotted.
    cmap : str or None
        The name of a ``matplotlib`` built-in colormap.
        Sets the colors of the processed spectra plot.
        Default is ``'default'``.
    fig_kw : any
        Any valid :class:`~matplotlib.figure.Figure` keyword arguments.
    """
    fig, (ax_raw_data, ax_processed_data) = plt.subplots(1, 2, layout='constrained', **fig_kw)
    fig.suptitle(dataset.name, fontweight='bold')
    _raw_data_subplot(ax_raw_data, dataset)
    _processed_data_subplot(ax_processed_data, dataset, cmap)

    plt.show()


def plot_1x3(dataset: Dataset, cmap: str = 'default', **fig_kw) -> None:
    """
    Show the 1-by-3 plot.

    Show a 1-by-3 plot of :attr:`~uv_pro.dataset.Dataset.raw_spectra`,
    :attr:`~uv_pro.dataset.Dataset.processed_spectra`, and
    :attr:`~uv_pro.dataset.Dataset.time_traces` in ``dataset``.

    Parameters
    ----------
    dataset : :class:`~uv_pro.dataset.Dataset`
        The :class:`~uv_pro.dataset.Dataset` to be plotted.
    cmap : str or None
        The name of a ``matplotlib`` built-in colormap.
        Sets the colors of the processed spectra plot.
        Default is ``'default'``.
    fig_kw : any
        Any valid :class:`~matplotlib.figure.Figure` keyword arguments.
    """
    fig, (ax_raw_data, ax_processed_data, ax_time_traces) = plt.subplots(1, 3, layout='constrained', **fig_kw)
    fig.suptitle(dataset.name, fontweight='bold')
    _raw_data_subplot(ax_raw_data, dataset)
    _processed_data_subplot(ax_processed_data, dataset, cmap)
    _time_traces_subplot(ax_time_traces, dataset)

    plt.show()


def plot_2x2(dataset: Dataset, cmap: str = 'default', **fig_kw) -> None:
    """
    Show the 2-by-2 plot.

    Show a 2-by-2 plot of :attr:`~uv_pro.dataset.Dataset.raw_spectra`,
    :attr:`~uv_pro.dataset.Dataset.processed_spectra`,
    :attr:`~uv_pro.dataset.Dataset.time_traces`, and
    :attr:`~uv_pro.dataset.Dataset.baseline` with
    :attr:`~uv_pro.dataset.Dataset.outliers` highlighted.

    Note
    ----
    If specific time traces have been chosen, then the time traces
    plot will instead show :attr:`~uv_pro.dataset.Dataset.chosen_traces`.

    Parameters
    ----------
    dataset : :class:`~uv_pro.dataset.Dataset`
        The :class:`~uv_pro.dataset.Dataset` to be plotted.
    cmap : str or None
        The name of a ``matplotlib`` built-in colormap.
        Sets the colors of the processed spectra plot.
        Default is ``'default'``.
    fig_kw : any
        Any valid :class:`~matplotlib.figure.Figure` keyword arguments.
    """
    fig, ((ax_raw_data, ax_processed_data), (ax_time_traces, ax_outliers)) = plt.subplots(2, 2, constrained_layout=True, **fig_kw)
    fig.suptitle(dataset.name, fontweight='bold')
    _raw_data_subplot(ax_raw_data, dataset)
    _processed_data_subplot(ax_processed_data, dataset, cmap)
    _time_traces_subplot(ax_time_traces, dataset)
    _outliers_subplot(ax_outliers, dataset)

    plt.show()


def _raw_data_subplot(ax: Axes, dataset: Dataset) -> None:
    """
    Create a raw data subplot.

    Parameters
    ----------
    ax : :class:`matplotlib.axes.Axes`
        The axes to plot on.
    dataset : :class:`~uv_pro.dataset.Dataset`
        The :class:`~uv_pro.dataset.Dataset` to be plotted.
    """
    spectra = dataset.raw_spectra
    cycler = _get_linestyles(spectra)
    ax.set_prop_cycle(cycler)
    ax.set_title('Raw Data', size=10, weight='bold', fontstyle='oblique')
    ax.set_xlim(190, 1100)
    ax.set(
        xlabel='Wavelength (nm)',
        ylabel='Absorbance (AU)'
    )

    ax.plot(spectra)


def _processed_data_subplot(ax: Axes, dataset: Dataset, cmap: str = 'default') -> None:
    """
    Create a processed data subplot.

    Parameters
    ----------
    ax : :class:`matplotlib.axes.Axes`
        The axes to plot on.
    dataset : :class:`~uv_pro.dataset.Dataset`
        The :class:`~uv_pro.dataset.Dataset` to be plotted.
    cmap : str or None
        The name of a ``matplotlib`` built-in colormap.
        Default is ``'default'``.
    """
    spectra = dataset.processed_spectra
    cycler = _get_linestyles(spectra, cmap)
    ax.set_prop_cycle(cycler)
    ax.set_title('Processed Data', size=10, weight='bold', fontstyle='oblique')
    ax.set_xlim(300, 1100)
    ax.set(
        xlabel='Wavelength (nm)',
        ylabel='Absorbance (AU)'
    )

    ax.text(
        x=0.99,
        y=0.99,
        s=f'showing: {len(spectra.columns)} spectra',
        verticalalignment='top',
        horizontalalignment='right',
        transform=ax.transAxes,
        color='gray',
        fontsize=8
    )

    ax.plot(spectra)


def _time_traces_subplot(ax: Axes, dataset: Dataset, show_slices: bool = True) -> None:
    """
    Create a time traces subplot.

    Parameters
    ----------
    ax : :class:`matplotlib.axes.Axes`
        The axes to plot on.
    dataset : :class:`~uv_pro.dataset.Dataset`
        The :class:`~uv_pro.dataset.Dataset` to be plotted.
    show_slices : bool
        Show vertical lines where slices are taken.
    """
    color = None
    linestyle = None
    alpha = 1
    ax.set_title('Time Traces', size=10, weight='bold', fontstyle='oblique')
    ax.set(
        xlabel='Time (s)',
        ylabel='Absorbance (AU)'
    )

    if dataset.chosen_traces is None:
        time_traces = dataset.time_traces
        ax.set_xlim(0, time_traces.index[-1])

    else:
        time_traces = dataset.chosen_traces
        ax.set_xlim(0, time_traces.index[-1])

        if dataset.fit or dataset.init_rate:
            color = 'k'
            linestyle = ':'
            alpha = 0.8

            for func in [_plot_init_rate_lines, _plot_fit_curves]:
                try:
                    func(ax, dataset)

                except TypeError:
                    continue

        _time_trace_plot_text(ax, dataset)

    if show_slices is True:
        _plot_slices_lines(ax, dataset)

    ax.plot(time_traces, alpha=alpha, linestyle=linestyle, color=color, zorder=2)


def _outliers_subplot(ax: Axes, dataset: Dataset) -> None:
    """
    Create outliers subplot.

    Parameters
    ----------
    ax : :class:`matplotlib.axes.Axes`
        The axes to plot on.
    dataset : :class:`~uv_pro.dataset.Dataset`
        The :class:`~uv_pro.dataset.Dataset` to be plotted.
    """
    ax.set_title('Baseline & Outliers', size=10, weight='bold', fontstyle='oblique')
    ax.set_xlim(left=0, right=dataset.spectra_times.iloc[-1])
    ax.set(
        xlabel='Time (s)',
        ylabel='Intensity (arb. units)'
    )

    _plot_baseline(ax, dataset)

    summed_time_traces = dataset.time_traces.sum(1)

    ax.scatter(
        x=dataset.outliers,
        y=summed_time_traces[dataset.outliers],
        color='red',
        marker='x',
        zorder=2
    )

    ax.plot(
        summed_time_traces,
        color='black',
        linestyle='solid',
        zorder=3
    )


def _plot_baseline(ax: Axes, dataset: Dataset) -> None:
    baselined_traces = dataset.time_traces.sum(1) - dataset.baseline
    upper_bound = dataset.outlier_threshold * baselined_traces.max() + dataset.baseline
    lower_bound = -dataset.outlier_threshold * baselined_traces.max() + dataset.baseline

    ax.plot(upper_bound, color='skyblue', linestyle='solid', alpha=0.5)
    ax.plot(lower_bound, color='skyblue', linestyle='solid', alpha=0.5)

    ax.fill_between(
        x=upper_bound.index,
        y1=upper_bound,
        y2=lower_bound,
        color='powderblue',
        alpha=0.5
    )

    ax.plot(
        dataset.baseline,
        color='skyblue',
        linestyle='dashed',
        alpha=0.8,
        zorder=1
    )

    ax.text(
        x=0.99,
        y=0.99,
        s=f'smooth={dataset.baseline_smoothness} tol={dataset.baseline_tolerance}',
        verticalalignment='top',
        horizontalalignment='right',
        transform=ax.transAxes,
        color='gray',
        fontsize=8
    )


def _plot_slices_lines(ax: Axes, dataset: Dataset) -> None:
    if dataset.slicing:
        for time in dataset.processed_spectra.columns:
            ax.axvline(
                x=time,
                color='k',
                linestyle='--',
                alpha=0.1,
                zorder=0
            )


def _plot_fit_curves(ax: Axes, dataset: Dataset) -> None:
    for wavelength in dataset.fit['curves'].columns:
        linecolor = f'C{dataset.chosen_traces.columns.get_loc(wavelength)}'
        ax.plot(
            dataset.fit['curves'][wavelength],
            label=wavelength,
            color=linecolor,
            alpha=0.6,
            linewidth=6,
            zorder=1
        )

    if dataset.trim:
        x_padding = (dataset.trim[1] - dataset.trim[0]) * 0.2
        left_bound = max(dataset.trim[0] - x_padding, 0)
        right_bound = min(dataset.trim[1] + x_padding, dataset.chosen_traces.index[-1])
        ax.set_xlim(left=left_bound, right=right_bound)


def _plot_init_rate_lines(ax: Axes, dataset: Dataset):
    for wavelength in dataset.init_rate['lines'].columns:
        linecolor = f'C{dataset.chosen_traces.columns.get_loc(wavelength)}'
        ax.plot(
            dataset.init_rate['lines'][wavelength],
            label=wavelength,
            color=linecolor,
            alpha=0.6,
            linewidth=3,
            zorder=2
        )

    if dataset.trim:
        x_padding = (dataset.init_rate['lines'].index[-1] - dataset.init_rate['lines'].index[0]) * 10
        left_bound = max(dataset.init_rate['lines'].index[0] - x_padding, 0)
        right_bound = min(dataset.init_rate['lines'].index[-1] + x_padding, dataset.chosen_traces.index[-1])
        ax.set_xlim(left=left_bound, right=right_bound)


def _get_linestyles(dataframe: DataFrame, color: str = 'default') -> cycler:
    import numpy as np
    num_lines = len(dataframe.columns)
    linewidths = [3] + [1] * (num_lines - 2) + [3]

    if color == 'default':
        line_colors = ['k'] + ['0.8'] * (num_lines - 2) + ['r']
    else:
        cmap = plt.get_cmap(color)
        line_colors = cmap(np.linspace(0, 1, num_lines))

    line_styles = cycler(color=line_colors) + cycler(linewidth=linewidths)

    return line_styles


def _time_trace_plot_text(ax: Axes, dataset: Dataset) -> None:

    def _add_text(text: list[str], row_number: int, text_color: str) -> None:
        ax.text(
            x=0.99,
            y=0.99 - row_number * 0.04,
            s=text,
            verticalalignment='top',
            horizontalalignment='right',
            transform=ax.transAxes,
            color=text_color,
            fontsize=8
        )

    row_number = 0
    if dataset.init_rate:
        for wavelength in dataset.init_rate['lines'].columns:
            text_color = f'C{dataset.chosen_traces.columns.get_loc(wavelength)}'
            text = [
                f'{wavelength}',
                'rate =',
                f'{dataset.init_rate["params"][wavelength]["slope"]:.2e}',
                f'± {dataset.init_rate["params"][wavelength]["slope err"]:.2e}',
                r'$r^2 =$',
                f'{dataset.init_rate["params"][wavelength]["r2"]:.3f}'
            ]

            _add_text(' '.join(text), row_number, text_color)
            row_number += 1

    if dataset.fit:
        for wavelength in dataset.fit['curves'].columns:
            text_color = f'C{dataset.chosen_traces.columns.get_loc(wavelength)}'
            text = [
                f'{wavelength}',
                r'$k_{obs} =$',
                f'{dataset.fit["params"][wavelength]["kobs"]:.2e}',
                f'± {dataset.fit["params"][wavelength]["kobs err"]:.2e}',
                r'$r^2 =$',
                f'{dataset.fit["params"][wavelength]["r2"]:.3f}'
            ]

            _add_text(' '.join(text), row_number, text_color)
            row_number += 1

    if not dataset.fit and not dataset.init_rate:
        for i, wavelength in enumerate(dataset.chosen_traces.columns):
            _add_text(f'{wavelength} nm', row_number, f'C{i}')
            row_number += 1

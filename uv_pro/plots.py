"""
Functions for plotting and visualizing uv_pro Datasets.

@author: David Hebert
"""

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from cycler import cycler
from pandas import DataFrame
from uv_pro.process import Dataset


plt.style.use('seaborn-v0_8-bright')


def plot_spectra(dataset: Dataset, spectra) -> None:
    """
    Show a simple spectra plot.

    Parameters
    ----------
    dataset : :class:`~uv_pro.process.Dataset`
        A :class:`~uv_pro.process.Dataset` containing the spectra to be plotted.
    spectra : :class:`pandas.DataFrame`
        The spectra to be plotted, such as :attr:`~uv_pro.process.Dataset.raw_spectra`
        or :attr:`~uv_pro.process.Dataset.processed_spectra`.
    """
    _, ax = plt.subplots()
    ax.set(xlabel='Wavelength (nm)', ylabel='Absorbance (AU)')
    plt.title(dataset.name, fontweight='bold')
    plt.plot(spectra)
    plt.xlim(200, 1100)
    print('Close plot window to continue...', end='\n')
    plt.show()


def plot_time_traces(dataset: Dataset) -> None:
    """
    Plot the :attr:`~uv_pro.process.Dataset.time_traces` of a ``dataset``.

    Parameters
    ----------
    dataset : :class:`~uv_pro.process.Dataset`
        The :class:`~uv_pro.process.Dataset` containing the time traces to be
        plotted.
    """
    _, ax = plt.subplots()
    ax.set(xlabel='Time (s)', ylabel='Absorbance (AU)')
    plt.title(f'{dataset.name}\nTime Traces')
    plt.plot(dataset.time_traces)
    plt.ylim(auto=True)
    plt.xlim(auto=True)
    plt.show()


def plot_1x2(dataset: Dataset) -> None:
    """
    Show the 1-by-2 plot.

    Show a 1-by-2 plot of :attr:`~uv_pro.process.Dataset.raw_spectra` and
    :attr:`~uv_pro.process.Dataset.processed_spectra` in ``dataset``.

    Parameters
    ----------
    dataset : :class:`~uv_pro.process.Dataset`
        The :class:`~uv_pro.process.Dataset` to be plotted.
    """
    fig, (ax_raw_data, ax_processed_data) = plt.subplots(1, 2, figsize=(10, 5), layout='constrained')
    fig.suptitle(dataset.name, fontweight='bold')
    _raw_data_subplot(ax_raw_data, dataset)
    _processed_data_subplot(ax_processed_data, dataset)

    print('Close plot window to continue...', end='\n')
    plt.show()


def plot_1x3(dataset: Dataset) -> None:
    """
    Show the 1-by-3 plot.

    Show a 1-by-3 plot of :attr:`~uv_pro.process.Dataset.raw_spectra`,
    :attr:`~uv_pro.process.Dataset.processed_spectra`, and
    :attr:`~uv_pro.process.Dataset.time_traces` in ``dataset``.

    Parameters
    ----------
    dataset : :class:`~uv_pro.process.Dataset`
        The :class:`~uv_pro.process.Dataset` to be plotted.
    """
    fig, (ax_raw_data, ax_processed_data, ax_time_traces) = plt.subplots(1, 3, figsize=(16, 4), layout='constrained')
    fig.suptitle(dataset.name, fontweight='bold')
    _raw_data_subplot(ax_raw_data, dataset)
    _processed_data_subplot(ax_processed_data, dataset)
    _time_traces_subplot(ax_time_traces, dataset)

    print('Close plot window to continue...', end='\n')
    plt.show()


def plot_2x2(dataset: Dataset) -> None:
    """
    Show the 2-by-2 plot.

    Show a 2-by-2 plot of :attr:`~uv_pro.process.Dataset.raw_spectra`,
    :attr:`~uv_pro.process.Dataset.processed_spectra`,
    :attr:`~uv_pro.process.Dataset.time_traces`, and
    :attr:`~uv_pro.process.Dataset.baseline` with
    :attr:`~uv_pro.process.Dataset.outliers` highlighted.

    Note
    ----
    If specific time traces have been chosen, then the time traces
    plot will instead show :attr:`~uv_pro.process.Dataset.chosen_traces`.

    Parameters
    ----------
    dataset : :class:`~uv_pro.process.Dataset`
        The :class:`~uv_pro.process.Dataset` to be plotted.
    """
    fig, ((ax_raw_data, ax_processed_data), (ax_time_traces, ax_combined)) = plt.subplots(2, 2, figsize=(16, 8), constrained_layout=True)
    fig.suptitle(dataset.name, fontweight='bold')
    _raw_data_subplot(ax_raw_data, dataset)
    _processed_data_subplot(ax_processed_data, dataset)
    _time_traces_subplot(ax_time_traces, dataset)
    _combined_time_traces_subplot(ax_combined, dataset)

    print('Close plot window to continue...')
    plt.show()


def _raw_data_subplot(ax: Axes, dataset: Dataset) -> None:
    """
    Create a raw data subplot.

    Parameters
    ----------
    ax : :class:`matplotlib.axes.Axes`
        The axes to plot on.
    dataset : :class:`~uv_pro.process.Dataset`
        The :class:`~uv_pro.process.Dataset` to be plotted.
    """
    spectra = dataset.raw_spectra
    ax.set_xlim(190, 1100)
    ax.set(
        xlabel='Wavelength (nm)',
        ylabel='Absorbance (AU)',
        title='Raw Data'
    )

    ax.plot(spectra)


def _processed_data_subplot(ax: Axes, dataset: Dataset) -> None:
    """
    Create a processed data subplot.

    Parameters
    ----------
    ax : :class:`matplotlib.axes.Axes`
        The axes to plot on.
    dataset : :class:`~uv_pro.process.Dataset`
        The :class:`~uv_pro.process.Dataset` to be plotted.
    """
    spectra = dataset.processed_spectra
    cycler = _get_linestyles(spectra)
    ax.set_prop_cycle(cycler)
    ax.set_xlim(300, 1100)
    ax.set(
        xlabel='Wavelength (nm)',
        ylabel='Absorbance (AU)',
        title='Processed Data'
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


def _time_traces_subplot(ax: Axes, dataset: Dataset) -> None:
    """
    Create a time traces subplot.

    Parameters
    ----------
    ax : :class:`matplotlib.axes.Axes`
        The axes to plot on.
    dataset : :class:`~uv_pro.process.Dataset`
        The :class:`~uv_pro.process.Dataset` to be plotted.
    """
    color = None
    linestyle = None
    alpha = 1
    ax.set(
        xlabel='Time (s)',
        ylabel='Absorbance (AU)',
        title='Time Traces'
    )

    if dataset.chosen_traces is None:
        time_traces = dataset.time_traces
        ax.set_xlim(0, time_traces.index[-1])

    else:
        time_traces = dataset.chosen_traces
        ax.set_xlim(0, time_traces.index[-1])

        if dataset.fit:
            _plot_fit_curves(ax, dataset)
            color = 'k'
            linestyle = ':'
            alpha = 0.8

        if dataset.init_rate:
            _plot_init_rate_lines(ax, dataset)
            color = 'k'
            linestyle = ':'
            alpha = 0.8

        else:
            for i, wavelength in enumerate(time_traces.columns):
                ax.text(
                    x=0.99,
                    y=0.99 - i * 0.04,
                    s=f'{wavelength} nm',
                    verticalalignment='top',
                    horizontalalignment='right',
                    transform=ax.transAxes,
                    color=f'C{i}',
                    fontsize=8
                )

    ax.plot(time_traces, alpha=alpha, linestyle=linestyle, color=color, zorder=2)


def _combined_time_traces_subplot(ax: Axes, dataset: Dataset) -> None:
    """
    Create combined time traces subplot.

    Parameters
    ----------
    ax : :class:`matplotlib.axes.Axes`
        The axes to plot on.
    dataset : :class:`~uv_pro.process.Dataset`
        The :class:`~uv_pro.process.Dataset` to be plotted.
    """
    ax.set_xlim(left=0, right=dataset.spectra_times.iloc[-1])
    ax.set(
        xlabel='Time (s)',
        ylabel='Intensity (arb. units)',
        title='Combined Time Traces & Baseline'
    )

    _plot_baseline(ax, dataset)

    ax.scatter(
        dataset.outliers,
        dataset.time_traces.sum(1)[dataset.outliers],
        color='red',
        marker='x',
        zorder=2
    )

    ax.plot(
        dataset.time_traces.sum(1),
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
        upper_bound.index,
        upper_bound,
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
        s=f'lam={dataset.baseline_lambda} tol={dataset.baseline_tolerance}',
        verticalalignment='top',
        horizontalalignment='right',
        transform=ax.transAxes,
        color='gray',
        fontsize=8
    )


def _plot_fit_curves(ax: Axes, dataset: Dataset) -> None:
    for i, wavelength in enumerate(dataset.fit['curves'].columns):
        linecolor = f'C{dataset.chosen_traces.columns.get_loc(wavelength)}'
        ax.plot(
            dataset.fit['curves'][wavelength],
            label=wavelength,
            color=linecolor,
            alpha=0.6,
            linewidth=6,
            zorder=1
        )

        kobs_text = ' '.join(
            [
                f'{wavelength}',
                r'$k_{obs} =$',
                f'{dataset.fit['params'][wavelength]['kobs']:.2e}',
                f'± {dataset.fit['params'][wavelength]['kobs err']:.2e}',
                r'$r^2 =$',
                f'{dataset.fit['params'][wavelength]['r2']:.3f}'
            ]
        )

        ax.text(
            x=0.99,
            y=0.99 - i * 0.04,
            s=kobs_text,
            verticalalignment='top',
            horizontalalignment='right',
            transform=ax.transAxes,
            color=linecolor,
            fontsize=8
        )

    if dataset.trim:
        xaxis_padding = (dataset.trim[1] - dataset.trim[0]) * 0.2
        left_bound = max(dataset.trim[0] - xaxis_padding, 0)
        right_bound = dataset.trim[1] + xaxis_padding
        ax.set_xlim(left=left_bound, right=right_bound)


def _plot_init_rate_lines(ax: Axes, dataset: Dataset):
    for i, wavelength in enumerate(dataset.init_rate['lines'].columns):
        linecolor = f'C{dataset.chosen_traces.columns.get_loc(wavelength)}'
        ax.plot(
            dataset.init_rate['lines'][wavelength],
            label=wavelength,
            color=linecolor,
            alpha=0.6,
            linewidth=3,
            zorder=1
        )

        rates_text = ' '.join(
            [
                f'{wavelength}',
                'rate =',
                f'{dataset.init_rate['params'][wavelength]['slope']:.2e}',
                f'± {dataset.init_rate['params'][wavelength]['slope err']:.2e}',
                'intercept =',
                f'{dataset.init_rate['params'][wavelength]['intercept']:.2e}',
                f'± {dataset.init_rate['params'][wavelength]['intercept err']:.2e}',
                r'$r^2 =$',
                f'{dataset.init_rate['params'][wavelength]['r2']:.3f}'
            ]
        )

        ax.text(
            x=0.99,
            y=0.99 - i * 0.04,
            s=rates_text,
            verticalalignment='top',
            horizontalalignment='right',
            transform=ax.transAxes,
            color=linecolor,
            fontsize=8
        )

    if dataset.trim:
        xaxis_padding = (dataset.trim[1] - dataset.trim[0]) * 0.2
        left_bound = max(dataset.trim[0] - xaxis_padding, 0)
        right_bound = dataset.trim[1] + xaxis_padding
        ax.set_xlim(left=left_bound, right=right_bound)

def _get_linestyles(dataframe: DataFrame) -> cycler:
    num_lines = len(dataframe.columns)
    colors = ['k'] + ['0.8'] * (num_lines - 2) + ['r']
    linewidths = [3] + [1] * (num_lines - 2) + [3]
    line_styles = cycler(color=colors) + cycler(linewidth=linewidths)
    return line_styles

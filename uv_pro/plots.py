"""
Functions for plotting and visualizing uv_pro Datasets.

@author: David Hebert
"""

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from cycler import cycler
from pandas import DataFrame
from uv_pro.process import Dataset


plt.style.use('fast')


def plot_spectra(dataset: Dataset, spectra):
    """
    Show a simple plot of a single or multiple spectra.

    Parameters
    ----------
    dataset : :class:`~uv_pro.process.Dataset`
        A :class:`~uv_pro.process.Dataset` containing the spectra to be plotted.
    spectra : :class:`pandas.DataFrame`
        The spectra to be plotted, such as ``dataset.all_spectra`` or
        ``dataset.cleaned_spectra``.

    Returns
    -------
    None. Shows a plot.
    """
    _, ax = plt.subplots()
    ax.set(xlabel='Wavelength (nm)', ylabel='Absorbance (AU)')
    plt.title(dataset.name, fontweight='bold')
    plt.plot(spectra)
    plt.xlim(200, 1100)
    print('Close plot window to continue...', end='\n')
    plt.show()


def plot_time_traces(dataset: Dataset):
    """
    Plot the :attr:`~uv_pro.process.Dataset.time_traces` of a ``dataset``.

    Parameters
    ----------
    dataset : :class:`~uv_pro.process.Dataset`
        The :class:`~uv_pro.process.Dataset` containing the time traces to be
        plotted.

    Returns
    -------
    None. Shows a plot.
    """
    _, ax = plt.subplots()
    ax.set(xlabel='Time (s)',
           ylabel='Absorbance (AU)')
    plt.title(f'{dataset.name}\nTime Traces')
    plt.plot(dataset.time_traces)
    plt.ylim(auto=True)
    plt.xlim(auto=True)
    plt.show()


def plot_1x2(dataset: Dataset):
    """
    Show the 1-by-2 plot.

    Show a 1-by-2 plot of :attr:`~uv_pro.process.Dataset.all_spectra` and
    :attr:`~uv_pro.process.Dataset.sliced_spectra` in ``dataset``.

    Parameters
    ----------
    dataset : :class:`~uv_pro.process.Dataset`
        The :class:`~uv_pro.process.Dataset` to be plotted.

    Returns
    -------
    None. Shows a plot.
    """
    fig, (ax_raw_data, ax_processed_data) = plt.subplots(1, 2, figsize=(10, 5), layout='constrained')
    fig.suptitle(dataset.name, fontweight='bold')
    _raw_data_subplot(ax_raw_data, dataset)
    _processed_data_subplot(ax_processed_data, dataset)
    print('Close plot window to continue...', end='\n')
    plt.show()


def plot_1x3(dataset: Dataset):
    """
    Show the 1-by-3 plot.

    Show a 1-by-3 plot of :attr:`~uv_pro.process.Dataset.all_spectra`,
    :attr:`~uv_pro.process.Dataset.sliced_spectra`, and
    :attr:`~uv_pro.process.Dataset.time_traces` in ``dataset``.

    Parameters
    ----------
    dataset : :class:`~uv_pro.process.Dataset`
        The :class:`~uv_pro.process.Dataset` to be plotted.

    Returns
    -------
    None. Shows a plot.
    """
    fig, (ax_raw_data, ax_processed_data, ax_time_traces) = plt.subplots(1, 3, figsize=(16, 4), layout='constrained')
    fig.suptitle(dataset.name, fontweight='bold')
    _raw_data_subplot(ax_raw_data, dataset)
    _processed_data_subplot(ax_processed_data, dataset)
    _time_traces_subplot(ax_time_traces, dataset)
    print('Close plot window to continue...', end='\n')
    plt.show()


def plot_2x2(dataset: Dataset):
    """
    Show the 2-by-2 plot.

    Show a 2-by-2 plot of :attr:`~uv_pro.process.Dataset.all_spectra`,
    :attr:`~uv_pro.process.Dataset.sliced_spectra`,
    :attr:`~uv_pro.process.Dataset.time_traces`, and
    :attr:`~uv_pro.process.Dataset.baseline` with
    :attr:`~uv_pro.process.Dataset.outliers` highlighted.

    Parameters
    ----------
    dataset : :class:`~uv_pro.process.Dataset`
        The :class:`~uv_pro.process.Dataset` to be plotted.

    Returns
    -------
    None. Shows a plot.
    """
    fig, ((ax_raw_data, ax_processed_data), (ax_time_traces, ax_combined)) = plt.subplots(2, 2, figsize=(16, 8), constrained_layout=True)
    fig.suptitle(dataset.name, fontweight='bold')
    _raw_data_subplot(ax_raw_data, dataset)
    _processed_data_subplot(ax_processed_data, dataset)
    _time_traces_subplot(ax_time_traces, dataset)
    _combined_time_traces_subplot(ax_combined, dataset)
    print('Close plot window to continue...')
    plt.show()


def _raw_data_subplot(ax: Axes, dataset: Dataset):
    """
    Create a raw data subplot.

    Parameters
    ----------
    ax : :class:`matplotlib.axes.Axes`
        The axes to plot on.
    dataset : :class:`~uv_pro.process.Dataset`
        The :class:`~uv_pro.process.Dataset` to be plotted.
    """
    spectra = dataset.all_spectra
    ax.set(xlabel='Wavelength (nm)', ylabel='Absorbance (AU)',
           title='Raw Data')
    ax.plot(spectra)


def _processed_data_subplot(ax: Axes, dataset: Dataset):
    """
    Create a processed data subplot.

    Parameters
    ----------
    ax : :class:`matplotlib.axes.Axes`
        The axes to plot on.
    dataset : :class:`~uv_pro.process.Dataset`
        The :class:`~uv_pro.process.Dataset` to be plotted.
    """
    spectra = dataset.sliced_spectra
    cycler = _get_linestyles(spectra)
    ax.set_prop_cycle(cycler)
    ax.set(xlabel='Wavelength (nm)', ylabel='Absorbance (AU)',
           title='Processed Data')
    ax.plot(spectra)
    ax.text(x=0.99, y=0.99,
            s=f'showing: {len(spectra.columns)} spectra',
            verticalalignment='top', horizontalalignment='right',
            transform=ax.transAxes, color='gray', fontsize=8)


def _time_traces_subplot(ax: Axes, dataset: Dataset):
    """
    Create a time traces subplot.

    Parameters
    ----------
    ax : :class:`matplotlib.axes.Axes`
        The axes to plot on.
    dataset : :class:`~uv_pro.process.Dataset`
        The :class:`~uv_pro.process.Dataset` to be plotted.
    """
    if dataset.specific_time_traces is not None:
        # TODO add legend for specific time traces
        time_traces = dataset.specific_time_traces
    else:
        time_traces = dataset.time_traces
        ax.text(x=0.99, y=0.99, s='saturated wavelengths not shown',
                verticalalignment='top', horizontalalignment='right',
                transform=ax.transAxes, color='gray', fontsize=8)

    ax.set(xlabel='Time (s)', ylabel='Absorbance (AU)', title='Time Traces')

    ax.plot(time_traces)

    if dataset.fit is not None:
        _plot_fit_curves(ax, dataset)


def _combined_time_traces_subplot(ax: Axes, dataset: Dataset):
    """
    Create combined time traces subplot.

    Parameters
    ----------
    ax : :class:`matplotlib.axes.Axes`
        The axes to plot on.
    dataset : :class:`~uv_pro.process.Dataset`
        The :class:`~uv_pro.process.Dataset` to be plotted.
    """
    ax.set(xlabel='Time (s)',
           ylabel='Intensity (arb. units)',
           title='Combined Time Traces & Baseline')

    baselined_time_traces = dataset.time_traces.sum(1) - dataset.baseline
    upper_bound = dataset.outlier_finder.outlier_threshold * baselined_time_traces.max() + dataset.baseline
    lower_bound = -dataset.outlier_finder.outlier_threshold * baselined_time_traces.max() + dataset.baseline

    ax.plot(upper_bound, color='skyblue', linestyle='solid', alpha=0.5)
    ax.plot(lower_bound, color='skyblue', linestyle='solid', alpha=0.5)
    ax.fill_between(upper_bound.index, upper_bound,
                    y2=lower_bound, color='powderblue', alpha=0.5)

    ax.plot(dataset.baseline, color='skyblue', linestyle='dashed', alpha=0.8)
    ax.plot(dataset.time_traces.sum(1), color='black', linestyle='solid')
    ax.text(x=0.99, y=0.99,
            s=(f'lam={dataset.outlier_finder.baseline_lambda} '
               f'tol={dataset.outlier_finder.baseline_tolerance}'),
            verticalalignment='top', horizontalalignment='right',
            transform=ax.transAxes, color='gray', fontsize=8)

    ax.scatter(dataset.outliers, dataset.time_traces.sum(1)[dataset.outliers], color='red', marker='x')


def _plot_fit_curves(ax: Axes, dataset: Dataset):
    for i, wavelength in enumerate(dataset.fit.keys()):
        # ax.scatter(x=dataset.fit[wavelength]['curve'].index,
        #            y=dataset.fit[wavelength]['curve'],
        #            label=wavelength,
        #            marker='.',
        #            facecolors='none',
        #            edgecolors=f'k',
        #            alpha=0.5,
        #            zorder=1)
        ax.plot(dataset.fit[wavelength]['curve'], color='k',
                linestyle=':', linewidth=4, alpha=1, zorder=1)
        kobs_text = (' ').join([
            f'{wavelength}',
            r'$k_{obs} =$',
            f'{dataset.fit[wavelength]['popt'][2].round(5)}',
            f'± {dataset.fit[wavelength]['perr'][2].round(5)}',
            r'$r^2 =$',
            f'{dataset.fit[wavelength]['r2'].round(4)}'])
        ax.text(x=0.99, y=0.99 - i * 0.04, s=kobs_text,
                verticalalignment='top', horizontalalignment='right',
                transform=ax.transAxes, color=f'C{i}', fontsize=8)

    xaxis_padding = (dataset.trim[1] - dataset.trim[0]) * 0.2
    ax.set_xlim(dataset.trim[0] - xaxis_padding,
                dataset.trim[1] + xaxis_padding)


def _get_linestyles(dataframe: DataFrame):
    num_lines = len(dataframe.columns)
    line_styles = (cycler(color=['k'] + ['0.8'] * (num_lines - 2) + ['r'])
                   + cycler(linewidth=[3] + [1] * (num_lines - 2) + [3]))
    return line_styles

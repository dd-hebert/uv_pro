"""
Functions for plotting and visualizing uv_pro Datasets.

@author: David Hebert
"""

import matplotlib.pyplot as plt


def plot_spectra(dataset, spectra, num_spectra=0):
    """
    Show a simple plot of a single or multiple spectra.

    Parameters
    ----------
    dataset : :class:`~uv_pro.process.Dataset`
        A :class:`~uv_pro.process.Dataset` containing the spectra to be plotted.
    spectra : list of :class:`pandas.DataFrame` objects
        The spectra to be plotted, such as ``dataset.all_spectra`` or
        ``dataset.cleaned_spectra``.
    num_spectra : int, optional
        The number of slices to plot. The default is 0, where all spectra in
        ``spectra`` are plot. Example: if ``spectra`` contains 100 spectra and
        ``num_spectra`` is 10, then every tenth spectrum will be plotted.

    Returns
    -------
    None. Shows a plot.

    """
    _, ax = plt.subplots()
    ax.set(xlabel='Wavelength (nm)',
           ylabel='Absorbance (AU)')

    plt.title(dataset.name, fontweight='bold')

    if num_spectra == 0 or num_spectra > len(spectra):
        for i, spectrum in enumerate(spectra):
            plt.plot(spectrum['Wavelength (nm)'],
                     spectrum['Absorbance (AU)'])

    else:
        for i in range(0, len(spectra), len(spectra) // int(num_spectra)):
            plt.plot(spectra[i]['Wavelength (nm)'],
                     spectra[i]['Absorbance (AU)'])

    plt.xlim(200, 1100)
    print('Close plot window to continue...', end='\n')
    plt.show()


def plot_time_traces(dataset):
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


def plot_1x2(dataset, num_spectra=0):
    """
    Show the 1-by-2 plot.

    Show a 1-by-2 plot of :attr:`~uv_pro.process.Dataset.all_spectra` and
    :attr:`~uv_pro.process.Dataset.trimmed_spectra` in ``dataset``.

    Parameters
    ----------
    dataset : :class:`~uv_pro.process.Dataset`
        The :class:`~uv_pro.process.Dataset` to be plotted.
    num_spectra : int, optional
        The number of slices to plot. The default is 0, where all spectra in
        ``dataset.all_spectra`` and ``dataset.trimmed_spectra`` are plotted.
        Example: if ``dataset.trimmed_spectra`` contains 400 spectra and
        ``num_spectra`` is 10, then every 40th spectrum will be plotted.

    Returns
    -------
    None. Shows a plot.

    """
    fig, (ax_raw_data, ax_processed_data) = plt.subplots(1, 2, figsize=(10, 5), layout='constrained')
    fig.suptitle(dataset.name, fontweight='bold')

    # Plot raw data
    _raw_data_subplot(ax_raw_data, dataset)

    # Plot processed data
    _processed_data_subplot(ax_processed_data, dataset, num_spectra)

    print('Close plot window to continue...', end='\n')
    plt.show()


def plot_1x3(dataset, num_spectra=0):
    """
    Show the 1-by-3 plot.

    Show a 1-by-3 plot of :attr:`~uv_pro.process.Dataset.all_spectra`,
    :attr:`~uv_pro.process.Dataset.trimmed_spectra`, and
    :attr:`~uv_pro.process.Dataset.time_traces` in ``dataset``.

    Parameters
    ----------
    dataset : :class:`~uv_pro.process.Dataset`
        The :class:`~uv_pro.process.Dataset` to be plotted.
    num_spectra : int, optional
        The number of slices to plot. The default is 0, where all spectra are
        plotted. Example: if ``dataset.trimmed_spectra`` contains 400 spectra
        and ``num_spectra`` is 10, then every 40th spectrum will be plotted.

    Returns
    -------
    None. Shows a plot.

    """
    fig, (ax_raw_data, ax_processed_data, ax_time_traces) = plt.subplots(1, 3, figsize=(16, 4), layout='constrained')
    fig.suptitle(dataset.name, fontweight='bold')

    # Plot raw data
    _raw_data_subplot(ax_raw_data, dataset)

    # Plot processed data
    _processed_data_subplot(ax_processed_data, dataset, num_spectra)

    # Plot time traces
    _time_traces_subplot(ax_time_traces, dataset)

    print('Close plot window to continue...', end='\n')
    plt.show()


def plot_2x2(dataset, num_spectra=0):
    """
    Show the 2-by-2 plot.

    Show a 2-by-2 plot of :attr:`~uv_pro.process.Dataset.all_spectra`,
    :attr:`~uv_pro.process.Dataset.trimmed_spectra`,
    :attr:`~uv_pro.process.Dataset.time_traces`, and
    :attr:`~uv_pro.process.Dataset.baseline` with
    :attr:`~uv_pro.process.Dataset.outliers` highlighted.

    Parameters
    ----------
    dataset : :class:`~uv_pro.process.Dataset`
        The :class:`~uv_pro.process.Dataset` to be plotted.
    num_spectra : int, optional
        The number of slices to plot. The default is 0, where all spectra are
        plotted. Example: if ``dataset.trimmed_spectra`` contains 400 spectra
        and ``num_spectra`` is 10, then every 40th spectrum will be plotted.

    Returns
    -------
    None. Shows a plot.

    """
    fig, ((ax_raw_data, ax_processed_data), (ax_time_traces, ax_combined)) = plt.subplots(2, 2, figsize=(16, 8), constrained_layout=True)
    fig.suptitle(dataset.name, fontweight='bold')

    # Plot raw data
    _raw_data_subplot(ax_raw_data, dataset)

    # Plot processed data
    _processed_data_subplot(ax_processed_data, dataset, num_spectra)

    # Plot time traces
    _time_traces_subplot(ax_time_traces, dataset)

    # Plot combined time traces with baseline
    _combined_time_traces_subplot(ax_combined, dataset)

    print('Close plot window to continue...')
    plt.show()


def _raw_data_subplot(ax, dataset):
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

    ax.set(xlabel='Wavelength (nm)',
           ylabel='Absorbance (AU)',
           title='Raw Data')

    for spectrum in spectra:
        ax.plot(spectrum['Wavelength (nm)'], spectrum['Absorbance (AU)'])


def _processed_data_subplot(ax, dataset, num_spectra=0):
    """
    Create a processed data subplot.

    Parameters
    ----------
    ax : :class:`matplotlib.axes.Axes`
        The axes to plot on.
    dataset : :class:`~uv_pro.process.Dataset`
        The :class:`~uv_pro.process.Dataset` to be plotted.
    num_spectra : int, optional
        The number of slices to plot. The default is 0, where all spectra are
        plotted. Example: if ``dataset.trimmed_spectra`` contains 400 spectra
        and ``num_spectra`` is 10, then every 40th spectrum will be plotted.

    """
    spectra = dataset.trimmed_spectra

    ax.set(xlabel='Wavelength (nm)',
           ylabel='Absorbance (AU)',
           title='Processed Data')

    if num_spectra == 0 or num_spectra > len(spectra):
        for spectrum in spectra:
            ax.plot(spectrum['Wavelength (nm)'], spectrum['Absorbance (AU)'])

        ax.text(0.99, 0.99, 'showing: all spectra',
                verticalalignment='top',
                horizontalalignment='right',
                transform=ax.transAxes,
                color='gray', fontsize=8)
    else:
        step = len(spectra) // num_spectra
        for i in range(0, len(spectra), step):
            ax.plot(spectra[i]['Wavelength (nm)'], spectra[i]['Absorbance (AU)'])

        ax.text(0.99, 0.99, f'showing: {num_spectra} spectra',
                verticalalignment='top',
                horizontalalignment='right',
                transform=ax.transAxes,
                color='gray', fontsize=8)


def _time_traces_subplot(ax, dataset):
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
        time_traces = dataset.specific_time_traces
        x_axis = 'time (s)'
    else:
        time_traces = dataset.time_traces
        x_axis = 'Spectrum (time / cycle time)'

    ax.set(xlabel=x_axis,
           ylabel='Absorbance (AU)',
           title='Time Traces')

    ax.plot(time_traces)

    ax.text(0.99, 0.99, 'saturated wavelengths excluded',
            verticalalignment='top',
            horizontalalignment='right',
            transform=ax.transAxes,
            color='gray', fontsize=8)


def _combined_time_traces_subplot(ax, dataset):
    """
    Create combined time traces subplot.

    Parameters
    ----------
    ax : :class:`matplotlib.axes.Axes`
        The axes to plot on.
    dataset : :class:`~uv_pro.process.Dataset`
        The :class:`~uv_pro.process.Dataset` to be plotted.

    """
    baseline = dataset.baseline
    time_traces = dataset.time_traces
    outlier_threshold = dataset.outlier_threshold
    baseline_lambda = dataset.baseline_lambda
    baseline_tolerance = dataset.baseline_tolerance
    outliers = dataset.outliers

    ax.set(xlabel='Spectrum (time / cycle time)',
           ylabel='Intensity (arb. units)',
           title='Combined Time Traces & Baseline')

    baselined_time_traces = time_traces.sum(1) - baseline

    upper_bound = outlier_threshold * baselined_time_traces.max() + baseline
    lower_bound = -outlier_threshold * baselined_time_traces.max() + baseline

    ax.plot(upper_bound, color='skyblue', linestyle='solid', alpha=0.5)
    ax.plot(lower_bound, color='skyblue', linestyle='solid', alpha=0.5)
    ax.fill_between(upper_bound.index, upper_bound, y2=lower_bound, color='powderblue', alpha=0.5)

    ax.plot(baseline, color='skyblue', linestyle='dashed', alpha=0.8)
    ax.plot(time_traces.sum(1), color='black', linestyle='solid')
    ax.text(0.99, 0.99, f'lam={baseline_lambda}, tol={baseline_tolerance}',
            verticalalignment='top',
            horizontalalignment='right',
            transform=ax.transAxes,
            color='gray', fontsize=8)

    ax.scatter(outliers, time_traces.sum(1)[outliers], color='red', marker='x')

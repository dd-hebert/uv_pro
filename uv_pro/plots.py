'''
Functions for plotting and visualizing uv_pro Datasets.

'''

import matplotlib.pyplot as plt


def plot_spectra(dataset, spectra, num_spectra=0):
    '''
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

    '''

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
    plt.ylim(-0.2, 3)
    print('Close plot window to continue...', end='\n')
    plt.show()


def plot_time_traces(dataset):
    '''
    Plots the :attr:`~uv_pro.process.Dataset.time_traces` of a ``dataset``.

    Parameters
    ----------
    dataset : :class:`~uv_pro.process.Dataset`
        The :class:`~uv_pro.process.Dataset` containing the time traces to be
        plotted.

    Returns
    -------
    None. Shows a plot.

    '''

    _, ax = plt.subplots()
    ax.set(xlabel='Time (s)',
           ylabel='Absorbance (AU)')

    plt.title(f'{dataset.name}\nTime Traces')

    plt.plot(dataset.time_traces)

    plt.ylim(auto=True)
    plt.xlim(auto=True)
    plt.show()


def plot_1x2(dataset, num_spectra=0):
    '''
    Shows a 1-by-2 plot of :attr:`~uv_pro.process.Dataset.all_spectra` and
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

    '''

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5), layout='constrained')
    fig.suptitle(dataset.name, fontweight='bold')
    ax1.set(xlabel='Wavelength (nm)',
            ylabel='Absorbance (AU)',
            title='Raw Data')

    ax2.set(xlabel='Wavelength (nm)',
            ylabel='Absorbance (AU)',
            title='Processed Data')

    for i, _ in enumerate(dataset.all_spectra):
        ax1.plot(dataset.all_spectra[i]['Wavelength (nm)'],
                 dataset.all_spectra[i]['Absorbance (AU)'])

    if num_spectra == 0 or num_spectra > len(dataset.trimmed_spectra):
        for i, _ in enumerate(dataset.cleaned_spectra):
            ax2.plot(dataset.trimmed_spectra[i]['Wavelength (nm)'],
                     dataset.trimmed_spectra[i]['Absorbance (AU)'])

        ax2.text(0.99, 0.99, 'all spectra',
                 verticalalignment='top',
                 horizontalalignment='right',
                 transform=ax2.transAxes,
                 color='gray',
                 fontsize=8)

    else:
        for i in range(0, len(dataset.trimmed_spectra), len(dataset.trimmed_spectra) // int(num_spectra)):
            ax2.plot(dataset.trimmed_spectra[i]['Wavelength (nm)'],
                     dataset.trimmed_spectra[i]['Absorbance (AU)'])

        ax2.text(0.99, 0.99, f'{num_spectra} spectra',
                 verticalalignment='top',
                 horizontalalignment='right',
                 transform=ax2.transAxes,
                 color='gray',
                 fontsize=8)

    print('Close plot window to continue...', end='\n')
    plt.show()


def plot_1x3(dataset, num_spectra=0):
    '''
    Shows a 1-by-3 plot of :attr:`~uv_pro.process.Dataset.all_spectra`,
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

    '''

    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(16, 4), layout='constrained')
    fig.suptitle(dataset.name, fontweight='bold')
    ax1.set(xlabel='Wavelength (nm)',
            ylabel='Absorbance (AU)',
            title='Raw Data')

    ax2.set(xlabel='Wavelength (nm)',
            ylabel='Absorbance (AU)',
            title='Processed Data')

    ax3.set(xlabel='Spectrum (time / cycle time)',
            ylabel='Absorbance (AU)',
            title='Time Traces')

    for i, _ in enumerate(dataset.all_spectra):
        ax1.plot(dataset.all_spectra[i]['Wavelength (nm)'],
                 dataset.all_spectra[i]['Absorbance (AU)'])

    if num_spectra == 0 or num_spectra > len(dataset.trimmed_spectra):
        for i, _ in enumerate(dataset.trimmed_spectra):
            ax2.plot(dataset.trimmed_spectra[i]['Wavelength (nm)'],
                     dataset.trimmed_spectra[i]['Absorbance (AU)'])

        ax2.text(0.99, 0.99, 'showing: all spectra',
                 verticalalignment='top',
                 horizontalalignment='right',
                 transform=ax2.transAxes,
                 color='gray',
                 fontsize=8)

    else:
        for i in range(0, len(dataset.trimmed_spectra), len(dataset.trimmed_spectra) // int(num_spectra)):
            ax2.plot(dataset.trimmed_spectra[i]['Wavelength (nm)'],
                     dataset.trimmed_spectra[i]['Absorbance (AU)'])

        ax2.text(0.99, 0.99, f'showing: {num_spectra} spectra',
                 verticalalignment='top',
                 horizontalalignment='right',
                 transform=ax2.transAxes,
                 color='gray',
                 fontsize=8)

    ax3.plot(dataset.time_traces)
    ax3.text(0.99, 0.99, 'saturated wavelengths excluded',
             verticalalignment='top',
             horizontalalignment='right',
             transform=ax3.transAxes,
             color='gray',
             fontsize=8)

    print('Close plot window to continue...', end='\n')
    plt.show()


def plot_2x2(dataset, num_spectra=0):
    '''
    Shows a 2-by-2 plot of :attr:`~uv_pro.process.Dataset.all_spectra`,
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

    '''

    fig, ([ax1, ax2], [ax3, ax4]) = plt.subplots(2, 2, figsize=(16, 8), layout='constrained')
    fig.suptitle(dataset.name, fontweight='bold')
    ax1.set(xlabel='Wavelength (nm)',
            ylabel='Absorbance (AU)',
            title='Raw Data')

    ax2.set(xlabel='Wavelength (nm)',
            ylabel='Absorbance (AU)',
            title='Processed Data')

    ax3.set(xlabel='Spectrum (time / cycle time)',
            ylabel='Absorbance (AU)',
            title='Time Traces')

    ax4.set(xlabel='Spectrum (time / cycle time)',
            ylabel='Absorbance (AU)',
            title='Combined Time Traces & Baseline')

    for i, _ in enumerate(dataset.all_spectra):
        ax1.plot(dataset.all_spectra[i]['Wavelength (nm)'],
                 dataset.all_spectra[i]['Absorbance (AU)'])

    if num_spectra == 0 or num_spectra > len(dataset.trimmed_spectra):
        for i, _ in enumerate(dataset.trimmed_spectra):
            ax2.plot(dataset.trimmed_spectra[i]['Wavelength (nm)'],
                     dataset.trimmed_spectra[i]['Absorbance (AU)'])

            ax2.text(0.99, 0.99, 'showing: all spectra',
                     verticalalignment='top',
                     horizontalalignment='right',
                     transform=ax2.transAxes,
                     color='gray',
                     fontsize=8)

    else:
        for i in range(0, len(dataset.trimmed_spectra), len(dataset.trimmed_spectra) // int(num_spectra)):
            ax2.plot(dataset.trimmed_spectra[i]['Wavelength (nm)'],
                     dataset.trimmed_spectra[i]['Absorbance (AU)'])

        ax2.text(0.99, 0.99, f'showing: {num_spectra} spectra',
                 verticalalignment='top',
                 horizontalalignment='right',
                 transform=ax2.transAxes,
                 color='gray',
                 fontsize=8)

    ax3.plot(dataset.time_traces)
    ax3.text(0.99, 0.99, 'saturated wavelengths excluded',
             verticalalignment='top',
             horizontalalignment='right',
             transform=ax3.transAxes,
             color='gray',
             fontsize=8)

    baselined_time_traces = dataset.time_traces.sum(1) - dataset.baseline

    # Use if classic outlier detection is being used (outlier threshold 0-1, normalized time traces)
    upper_bound = dataset.outlier_threshold * baselined_time_traces.max() + dataset.baseline
    lower_bound = -dataset.outlier_threshold * baselined_time_traces.max() + dataset.baseline

    # Use if new outlier detection is being used (baseline +- outlier_threshold)
    # upper_bound = dataset.baseline  + dataset.outlier_threshold
    # lower_bound = dataset.baseline  - dataset.outlier_threshold

    ax4.plot(upper_bound, color='skyblue', linestyle='solid', alpha=0.5)
    ax4.plot(lower_bound, color='skyblue', linestyle='solid', alpha=0.5)
    ax4.fill_between(upper_bound.index, upper_bound, y2=lower_bound, color='powderblue', alpha=0.5)

    ax4.plot(dataset.baseline, color='skyblue', linestyle="dashed", alpha=0.8)
    ax4.plot(dataset.time_traces.sum(1), color='black', linestyle="solid")
    ax4.text(0.99, 0.99, f'lam={dataset.baseline_lambda}, tol={dataset.baseline_tolerance}',
             verticalalignment='top',
             horizontalalignment='right',
             transform=ax4.transAxes,
             color='gray',
             fontsize=8)

    ax4.scatter(dataset.outliers,
                dataset.time_traces.sum(1)[dataset.outliers],
                color='red',
                marker='x')

    print('Close plot window to continue...', end='\n')
    plt.show()

"""
Printing helper functions.

@author: David Hebert
"""


def print_dataset(dataset) -> None:
    print(f'Filename: {dataset.name}')
    print(f'Spectra found: {len(dataset.raw_spectra.columns)}')
    print(f'Cycle time (s): {dataset.cycle_time}')

    if dataset.is_processed is True:
        print(f'Outliers found: {len(dataset.outliers)}')

        if dataset.trim:
            print(f'Removed data before {dataset.trim[0]} and after {dataset.trim[1]} seconds.')

        if dataset.slicing is None:
            print(f'Spectra remaining: {len(dataset.processed_spectra.columns)}')

        else:
            print(f'Slicing mode: {dataset.slicing['mode']}')
            if dataset.slicing['mode'] == 'gradient':
                print(f'Coefficient: {dataset.slicing['coeff']}')
                print(f'Exponent: {dataset.slicing['expo']}')

            print(f'Slices: {len(dataset.processed_spectra.columns)}')

        if dataset.fit is not None:
            equation = 'f(t) = abs_f + (abs_0 - abs_f) * exp(-kobs * t)'
            print(f'Fit function: {equation}')
            print_fit(dataset.fit)

    return ''


def print_fit(fit: dict) -> None:
    # TODO use string formatting to make table prettier
    table_width = 94
    table_headings = '│ \033[1m{}\t{:^18}\t{:^18}\t{:^18}\t{:^6}\033[22m │'

    print('\n' + '┌' + '─' * table_width + '┐')
    print(table_headings.format('Wavelength', 'kobs', 'abs_0', 'abs_f', 'r2'))
    print('├' + '─' * table_width + '┤')

    for wavelength, fit in fit.items():
        abs_0 = '{:+.5f} ± {:.5f}'.format(fit['popt'][0], fit['perr'][0])
        abs_f = '{:+.5f} ± {:.5f}'.format(fit['popt'][1], fit['perr'][1])
        kobs = '{:.2e} ± {:.2e}'.format(fit['popt'][2], fit['perr'][2])
        r2 = '{:.4f}'.format(fit['r2'])
        print('│ {:>10}\t{}\t{}\t{}\t{} │'.format(wavelength, kobs, abs_0, abs_f, r2))

    print('└' + '─' * table_width + '┘')

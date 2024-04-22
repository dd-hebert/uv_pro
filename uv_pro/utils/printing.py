"""
Printing helper functions.

@author: David Hebert
"""


def print_dataset(dataset) -> None:
    print('')
    print(f'Filename: {dataset.name}')
    print(f'Spectra found: {len(dataset.raw_spectra.columns)}')

    if dataset.cycle_time:
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
            if unable_to_fit := set(dataset.chosen_traces.columns).difference(set(dataset.fit.keys())):
                print(f'\033[31mUnable to fit: {", ".join(map(str, unable_to_fit))} nm.\033[0m')

    return ''


def print_fit(fit: dict) -> None:
    # TODO use string formatting to make table prettier
    table_width = 61
    table_headings = '│ \033[1m{:^4}   {:^19}   {:^9}   {:^9}   {:^6}\033[22m │'

    print('\n' + '┌' + '─' * table_width + '┐')
    print(table_headings.format('λ', 'kobs', 'abs_0', 'abs_f', 'r2'))
    print('├' + '─' * table_width + '┤')

    for wavelength, fit in fit.items():
        abs_0 = '{:+.2e}'.format(fit['popt'][0])
        abs_f = '{:+.2e}'.format(fit['popt'][1])
        kobs = '{:.2e} ± {:.2e}'.format(fit['popt'][2], fit['perr'][2])
        r2 = '{:.4f}'.format(fit['r2'])
        print('│ {:<4}   {}   {}   {}   {} │'.format(wavelength, kobs, abs_0, abs_f, r2))

    print('└' + '─' * table_width + '┘')

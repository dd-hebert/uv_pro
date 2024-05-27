"""
Helper functions for printing and prompting.

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
            if unable_to_fit := set(dataset.chosen_traces.columns).difference(set(dataset.fit['curves'].columns)):
                print(f'\033[31mUnable to fit: {", ".join(map(str, unable_to_fit))} nm.\033[0m')

    return ''


def print_fit(fit: dict) -> None:
    # TODO use string formatting to make table prettier
    table_width = 61
    table_headings = '│ \033[1m{:^4}   {:^19}   {:^9}   {:^9}   {:^6}\033[22m │'

    print('\n' + '┌' + '─' * table_width + '┐')
    print(table_headings.format('λ', 'kobs', 'abs_0', 'abs_f', 'r2'))
    print('├' + '─' * table_width + '┤')

    for wavelength in fit['params'].columns:
        abs_0 = '{:+.2e}'.format(fit['params'][wavelength]['abs_0'])
        abs_f = '{:+.2e}'.format(fit['params'][wavelength]['abs_f'])
        kobs = '{:.2e} ± {:.2e}'.format(fit['params'][wavelength]['kobs'], fit['params'][wavelength]['kobs err'])
        r2 = '{:.4f}'.format(fit['params'][wavelength]['r2'])
        print('│ {:<4}   {}   {}   {}   {} │'.format(wavelength, kobs, abs_0, abs_f, r2))

    print('└' + '─' * table_width + '┘')


def prompt_user(header: str, options: list[dict]):
    """
    Prompt the user for input.

    Parameters
    ----------
    header : str
        The prompt header.
    options : list[dict]
        The input choices, a list of dicts. Example: [{'key': 'q', 'name': 'Quit'}]
        An option's 'key' is the accepted input for that option.

    Returns
    -------
    list[str]
        The user's input selections.
    """
    prompt = f'\n{header}\n{'=' * len(header)}\n'
    prompt += '\n'.join([f'({option['key']}) {option['name']}' for option in options])
    prompt += '\n\nChoice: '

    valid_choices = [option['key'] for option in options]

    try:
        user_choices = [char for char in input(prompt).strip() if char in valid_choices]

        while not user_choices:
            print('\nInvalid selection. Enter one or more of the displayed options or ctrl-z to quit.')
            user_choices = [char for char in input(prompt).strip() if char in valid_choices]

        return user_choices

    except EOFError:  # crtl-z
        return []

    except KeyboardInterrupt:  # ctrl-c
        return []

"""
Helper functions for printing and prompting.

@author: David Hebert
"""


def print_dataset(dataset) -> None:
    out = []
    out.append(f'Filename: {dataset.name}')
    out.append(f'Spectra found: {len(dataset.raw_spectra.columns)}')

    if dataset.cycle_time:
        out.append(f'Cycle time (s): {dataset.cycle_time}')

    if dataset.is_processed is True:
        out.append(f'Outliers found: {len(dataset.outliers)}')

        if dataset.trim:
            out.append(f'Removed data before {dataset.trim[0]} and after {dataset.trim[1]} seconds.')

        if dataset.slicing is None:
            out.append(f'Spectra remaining: {len(dataset.processed_spectra.columns)}')

        else:
            out.append(f'Slicing mode: {dataset.slicing["mode"]}')
            if dataset.slicing['mode'] == 'gradient':
                out.append(f'Coefficient: {dataset.slicing["coeff"]}')
                out.append(f'Exponent: {dataset.slicing["expo"]}')

            out.append(f'Slices: {len(dataset.processed_spectra.columns)}')

        if dataset.fit is not None:
            equation = 'f(t) = abs_f + (abs_0 - abs_f) * exp(-kobs * t)'
            out.append(f'Fit function: {equation}')
            out.extend(['', print_fit(dataset.fit)])
            if unable_to_fit := set(dataset.chosen_traces.columns).difference(set(dataset.fit['curves'].columns)):
                out.append(f'\033[31mUnable to fit: {", ".join(map(str, unable_to_fit))} nm.\033[0m')

        if dataset.init_rate is not None:
            out.extend(['', print_init_rate(dataset.init_rate)])

    return '\n'.join(out)


def print_fit(fit: dict) -> None:
    table_width = 61
    table_headings = '│ \033[1m{:^4}   {:^19}   {:^9}   {:^9}   {:^6}\033[22m │'

    out = []
    out.append('┌' + '─' * table_width + '┐')
    out.append(table_headings.format('λ', 'kobs', 'abs_0', 'abs_f', 'r2'))
    out.append('├' + '─' * table_width + '┤')

    for wavelength in fit['params'].columns:
        abs_0 = '{: .2e}'.format(fit['params'][wavelength]['abs_0'])
        abs_f = '{: .2e}'.format(fit['params'][wavelength]['abs_f'])
        kobs = '{:.2e} ± {:.2e}'.format(fit['params'][wavelength]['kobs'], fit['params'][wavelength]['kobs err'])
        r2 = '{:.4f}'.format(fit['params'][wavelength]['r2'])
        out.append('│ {:<4}   {}   {}   {}   {} │'.format(wavelength, kobs, abs_0, abs_f, r2))

    out.append('└' + '─' * table_width + '┘')

    return '\n'.join(out)


def print_init_rate(init_rate: dict) -> None:
    table_width = 61
    table_headings = '│ \033[1m{:^4}   {:^20}   {:^8}   {:^9}   {:^6}\033[22m │'

    out = []
    out.append('┌' + '─' * table_width + '┐')
    out.append(table_headings.format('λ', 'rate', 'Δabs', 'Δt', 'r2'))
    out.append('├' + '─' * table_width + '┤')

    for wavelength in init_rate['params'].columns:
        rate = '{: .2e} ± {:.2e}'.format(init_rate['params'][wavelength]['slope'], init_rate['params'][wavelength]['slope err'])
        delta_abs = '{:.2%}'.format(abs(init_rate['params'][wavelength]['delta_abs_%']))
        delta_t = '{:.1f}'.format(init_rate['params'][wavelength]['delta_t'])
        r2 = '{:.4f}'.format(init_rate['params'][wavelength]['r2'])
        out.append('│ {:<4}   {}   {:>8}   {:>9}   {} │'.format(wavelength, rate, delta_abs, delta_t, r2))

    out.append('└' + '─' * table_width + '┘')

    return '\n'.join(out)


def prompt_user_choice(header: str, options: list[dict]) -> list[str]:
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
    prompt = f'\n{header}\n{"=" * len(header)}\n'
    prompt += '\n'.join([f'({option["key"]}) {option["name"]}' for option in options])
    prompt += '\n\nChoice: '

    valid_choices = [option['key'] for option in options]

    try:
        user_choices = [key for key in input(prompt).strip().split() if key in valid_choices]

        while not user_choices:
            print('\nInvalid selection. Enter one or more of the displayed options or ctrl-c to quit.')
            user_choices = [key for key in input(prompt).strip().split() if key in valid_choices]

        return user_choices

    except (EOFError, KeyboardInterrupt):  # ctrl-c
        return []

def prompt_for_value(title: str, prompt: str, func: callable = None):
    """Prompt the user for some value."""
    print(f'\n{title}')

    try:
        value = input(prompt)
        return func(value) if func else value

    except (ValueError, NameError, SyntaxError):
        print('Invalid entry.')
        return

    except (EOFError, KeyboardInterrupt):
        return

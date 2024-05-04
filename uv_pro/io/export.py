"""
Export data.

Contains functions for exporting UV-vis data to .csv format.

@author: David Hebert
"""
import os


def export_csv(dataset, data, suffix: str = None) -> str:
    """
    Export data to .csv.

    Data is exported to the same directory as the parent \
    .KD file.

    Parameters
    ----------
    dataset : :class:`~uv_pro.process.Dataset`
        The :class:`~uv_pro.process.Dataset` to be exported.
    data : :class:`pandas.DataFrame`
        The data to be exported. A :class:`pandas.DataFrame`
        such as :attr:`~uv_pro.process.Dataset.raw_spectra` or
        :attr:`~uv_pro.process.Dataset.chosen_traces`.

    Returns
    -------
    str
        The name of the exported .csv file.
    """
    output_dir = os.path.dirname(dataset.path)
    base_filename = f'{os.path.splitext(dataset.name)[0]}'

    if suffix:
        base_filename += f' {suffix}'

    filename = _get_unique_filename(output_dir, base_filename)
    data.to_csv(os.path.join(output_dir, f'{filename}.csv'), index=True)

    return f'{filename}.csv'


def _get_unique_filename(output_dir: str, base_filename: str) -> str:
    """If a file named base_filename exists, add a number after."""
    n = 1
    unique_filename = base_filename
    while os.path.exists(f'{os.path.join(output_dir, unique_filename)}.csv'):
        unique_filename = base_filename + f' ({n})'
        n += 1

    return unique_filename


def prompt_for_export(dataset) -> list[str]:
    """
    Prompt the user for data export.

    Parameters
    ----------
    dataset : :class:`~uv_pro.process.Dataset`
        The :class:`~uv_pro.process.Dataset` to be exported.

    Returns
    -------
    files_exported : list[str]
        The names of the exported files.
    """
    options = ['Processed spectra']
    if dataset.chosen_traces is not None:
        options.append('Time traces')

    if dataset.fit is not None:
        options.append('Exponential fit')

    prompt = f'\nExport data?\n{'=' * 12}\n'
    prompt += '\n'.join([f'({i}) {option}' for i, option in enumerate(options, start=1)])
    prompt += '\n(q) Quit\n\nChoice: '

    valid_choices = [str(i) for i in range(1, len(options) + 1)] + ['q']
    user_choice = [char for char in input(prompt).strip().lower() if char in valid_choices]

    while not user_choice:
        print('\nInvalid selection. Enter one or more of the displayed options.')
        user_choice = [char for char in input(prompt).strip().lower() if char in valid_choices]

    files_exported = []
    if '1' in user_choice:
        files_exported.append(export_csv(dataset, dataset.processed_spectra))
    if '2' in user_choice:
        files_exported.append(export_csv(dataset, dataset.chosen_traces, suffix='Traces'))
    if '3' in user_choice:
        files_exported.extend(
            [
                export_csv(dataset, dataset.fit['curves'], suffix='Fit curves'),
                export_csv(dataset, dataset.fit['params'].transpose(), suffix='Fit params')
            ]
        )

    return files_exported

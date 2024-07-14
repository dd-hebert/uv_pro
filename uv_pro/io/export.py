"""
Export data.

Contains functions for exporting UV-vis data to .csv format.

@author: David Hebert
"""
import os
from uv_pro.utils.printing import prompt_user_choice


def export_csv(dataset, data, suffix: str | None = None) -> str:
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
    suffix : str or None
        A suffix to append to the end of the file name \
        (before the file extension).

    Returns
    -------
    str
        The name of the exported .csv file.
    """
    output_dir = os.path.dirname(dataset.path)
    base_filename = os.path.splitext(dataset.name)[0]

    if suffix:
        base_filename += f' {suffix}'

    filename = _get_unique_filename(output_dir, base_filename, 'csv')
    data.to_csv(os.path.join(output_dir, filename), index=True)

    return filename


def export_figure(fig, output_dir: str, filename: str) -> str:
    """Save a figure with `filename` as .png to the `output_dir`."""
    filename = _get_unique_filename(output_dir, filename, 'png')

    fig.savefig(
        fname=os.path.join(output_dir, filename),
        format='png',
        dpi=600
    )

    return filename


def _get_unique_filename(output_dir: str, base_filename: str, ext: str) -> str:
    """If a file named base_filename exists, add a number after."""
    n = 1
    unique_filename = f'{base_filename}.{ext}'
    while os.path.exists(f'{os.path.join(output_dir, unique_filename)}'):
        unique_filename = base_filename + f' ({n}).{ext}'
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
    key = 1
    header = 'Export data?'
    options = [{'key': str(key), 'name': 'Processed spectra'}]
    files_exported = []

    if dataset.chosen_traces is not None:
        key += 1
        traces_key = key
        options.append({'key': str(traces_key), 'name': 'Time traces'})

    if dataset.fit is not None:
        key += 1
        fit_key = key
        options.append({'key': str(fit_key), 'name': 'Exponential fit'})

    if dataset.init_rate is not None:
        key += 1
        init_rate_key = key
        options.append({'key': str(init_rate_key), 'name': 'Initial rates'})

    if user_choices := prompt_user_choice(header=header, options=options):
        if '1' in user_choices:
            files_exported.append(export_csv(dataset, dataset.processed_spectra))
        if str(traces_key) in user_choices:
            files_exported.append(export_csv(dataset, dataset.chosen_traces, suffix='Traces'))

        try:
            if str(fit_key) in user_choices:
                files_exported.extend(
                    [
                        export_csv(dataset, dataset.fit['curves'], suffix='Fit curves'),
                        export_csv(dataset, dataset.fit['params'].transpose(), suffix='Fit params')
                    ]
                )

        except UnboundLocalError:
            pass

        try:
            if str(init_rate_key) in user_choices:
                files_exported.extend(
                    [
                        export_csv(dataset, dataset.init_rate['lines'], suffix='Init rate lines'),
                        export_csv(dataset, dataset.init_rate['params'].transpose(), suffix='Init rate params'),
                    ]
                )

        except UnboundLocalError:
            pass

    return files_exported

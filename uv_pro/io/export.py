"""
Export data.

Contains functions for exporting UV-vis data to .csv format.

@author: David Hebert
"""

import os


def export_csv(dataset, data, suffix: str | None = None) -> str:
    """
    Export data to .csv.

    Data is exported to the same directory as the parent \
    .KD file.

    Parameters
    ----------
    dataset : :class:`~uv_pro.dataset.Dataset`
        The :class:`~uv_pro.dataset.Dataset` to be exported.
    data : :class:`pandas.DataFrame`
        The data to be exported. A :class:`pandas.DataFrame`
        such as :attr:`~uv_pro.dataset.Dataset.raw_spectra` or
        :attr:`~uv_pro.dataset.Dataset.chosen_traces`.
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

    fig.savefig(fname=os.path.join(output_dir, filename), format='png', dpi=600)

    return filename


def _get_unique_filename(output_dir: str, base_filename: str, ext: str) -> str:
    """If a file named base_filename exists, add a number after."""
    n = 1
    unique_filename = f'{base_filename}.{ext}'
    while os.path.exists(f'{os.path.join(output_dir, unique_filename)}'):
        unique_filename = base_filename + f' ({n}).{ext}'
        n += 1

    return unique_filename

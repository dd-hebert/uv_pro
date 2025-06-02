"""
Export data.

Contains functions for exporting UV-vis data to .csv format.

@author: David Hebert
"""

from pathlib import Path

from uv_pro.utils.paths import get_unique_filename

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
    output_dir: Path = dataset.path.parent
    base_filename = Path(dataset.name).stem

    if suffix:
        base_filename += f' {suffix}'

    filename = get_unique_filename(output_dir, base_filename, '.csv')
    data.to_csv(output_dir.joinpath(filename), index=True)
    return filename


def export_figure(fig, output_dir: Path, filename: str) -> str:
    """Save a figure with `filename` as .png to the `output_dir`."""
    filename = get_unique_filename(output_dir, filename, '.png')
    fig.savefig(fname=output_dir.joinpath(filename), format='png', dpi=600)
    return filename

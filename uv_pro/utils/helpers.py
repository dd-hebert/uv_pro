from rich import print
from rich.columns import Columns

from uv_pro.const import CMAPS


def list_colormaps():
    link = 'https://matplotlib.org/stable/tutorials/colors/colormaps.html'
    basic_cmaps, reversible_cmaps = sort_reversible_colormaps(CMAPS.values())
    print(
        '\nBasic Colormaps',
        '\n==============',
        Columns([f'• {name}' for name in basic_cmaps], column_first=True),
        '\nReversible Colormaps',
        '\n====================',
        Columns([f'• {name}' for name in reversible_cmaps], column_first=True),
        '\nReversible colormaps can be reversed by appending "_r" to the name (e.g., "viridis_r").'
        f'\nSee {link} for more info.',
    )


def sort_reversible_colormaps(cmap_list) -> tuple[list, list]:
    basic_cmaps = set()
    reversible_cmaps = set()

    for cmap in cmap_list:
        if cmap.endswith('_r'):
            reversible_cmaps.add(cmap[:-2])
        else:
            basic_cmaps.add(cmap)

    basic = sorted(basic_cmaps - reversible_cmaps, key=str.casefold)
    reversible = sorted(basic_cmaps & reversible_cmaps, key=str.casefold)

    return basic, reversible

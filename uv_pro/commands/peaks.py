"""
Functions for the ``peaks`` command.

@author: David Hebert
"""
import argparse
from rich import print, box
from rich.panel import Panel
from rich.table import Table, Column
from rich.text import Text
from uv_pro.commands import command, argument
from uv_pro.commands.process import _handle_path
from uv_pro.peakfinder import PeakFinder
from uv_pro.plots import plot_peakfinder


HELP = {
    'path': '''A path to a UV-vis data file (.KD format).''',
    'conc': '''The molar concentration of the species in the spectrum. Used for calculating
                molar absorptivity (ε). Default is None.''',
    'dist': '''Set the minimum distance between peaks (in nm). Default is 10.''',
    'max_iter': '''The max number of peak finding iterations. The default is 1000.''',
    'method': '''The peak detection method: either localmax or deriv. Default is localmax.''',
    'num_peaks': '''The number of peaks that should be found. Default is 0 (find all peaks).''',
    'prom': '''Set the minimum peak prominance. Default is 0.''',
    'p_win': '''Set the peak detection window (in nm). Search for peaks within the given
                wavelength range. Default is None (search whole spectrum).''',
    's_win': '''Set the Savitzky-Golay smoothing window. Default is 15.
                See :func:`scipy.signal.savgol_filter`.'''
}
ARGS = [
    argument(
        'path',
        action='store',
        default=None,
        help=HELP['path']
    ),
    argument(
        '-conc',
        '--concentration',
        action='store',
        type=float,
        default=None,
        metavar='',
        help=HELP['conc']
    ),
    argument(
        '-dist',
        '--distance',
        action='store',
        type=int,
        default=10,
        metavar='',
        help=HELP['dist']
    ),
    argument(
        '--max_iter',
        action='store',
        type=int,
        default=1000,
        metavar='',
        help=HELP['max_iter']
    ),
    argument(
        '--method',
        action='store',
        type=str,
        default='localmax',
        choices=['localmax', 'deriv'],
        metavar='',
        help=HELP['method']
    ),
    argument(
        '-num',
        '--num_peaks',
        action='store',
        type=int,
        default=0,
        metavar='',
        help=HELP['num_peaks']
    ),
    argument(
        '-prom',
        '--prominance',
        action='store',
        type=float,
        default=0.0,
        metavar='',
        help=HELP['prom']
    ),
    argument(
        '-pwin',
        '--peak_window',
        action='store',
        type=int,
        nargs=2,
        default=[300, 1100],
        metavar='',
        help=HELP['p_win']
    ),
    argument(
        '-swin',
        '--smooth_window',
        action='store',
        type=int,
        default=15,
        metavar='',
        help=HELP['s_win']
    )
]


@command(args=ARGS)
def peaks(args: argparse.Namespace) -> None:
    """
    Parser Info
    -----------
    *desc : UV-vis spectrum peak detection.
    *help : Find peaks in UV-vis spectra.
    """
    print(
        '',
        Panel(
            Text('Close plot window to continue...', style='bold grey100', justify='center'),
            title=Text('uv_pro Peak Finder', style='table.title'),
            border_style='grey27',
            width=34,
            box=box.SIMPLE
        )
    )

    _handle_path(args)

    pf = PeakFinder(
        path=args.path,
        method=args.method,
        num_peaks=args.num_peaks,
        conc=args.concentration,
        p_win=args.peak_window,
        s_win=args.smooth_window,
        dist=args.distance,
        prom=args.prominance,
        max_iter=args.max_iter
    )

    plot_peakfinder(pf, figsize=args.plot_size)

    if pf.peaks['peaks']:
        print('', _rich_text(args, pf.peaks))


def _rich_text(args: argparse.Namespace, peaks: dict) -> Table:
    has_epsilon = 'epsilon' in peaks['info'].columns
    table = Table(
        Column('λ', justify='center'),
        Column('abs', justify='center'),
        width=30,
        box=box.SIMPLE,
        row_styles=['grey100', 'white'],
    )

    if has_epsilon:
        table.add_column('ε', justify='center')

    for wavelength in peaks['info'].index:
        absorbance = '{:^.3f}'.format(peaks['info']['abs'].loc[wavelength])
        row = [str(wavelength), absorbance]

        if has_epsilon:
            row.append('{:^.3e}'.format(peaks['info']['epsilon'].loc[wavelength]))

        table.add_row(*row)

    return Panel(
        table,
        title=Text('Peak Finder Results', style='grey0 on medium_purple3'),
        subtitle=Text(f'Method: {args.method}', style='table.caption'),
        width=34,
        box=box.ROUNDED
    )

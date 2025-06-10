"""
Setup argparse parsers.

@author: David Hebert
"""

import argparse

from uv_pro.utils.helpers import list_colormaps


class ListColormapsAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        list_colormaps()
        parser.exit()


main_parser = argparse.ArgumentParser(description='Process UV-vis Data Files')
main_parser.add_argument(
    '--list-colormaps',
    nargs=0,
    action=ListColormapsAction,
    help='List available colormaps.',
)

subparsers = main_parser.add_subparsers(help='Commands')

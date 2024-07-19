"""
Functions for the ``test`` command.

@author: David Hebert
"""
import argparse
import os
from uv_pro.commands.process import process


def test(args: argparse.Namespace) -> None:
    r"""Test mode `-qq` only works from inside the repo \...\uv_pro\uv_pro."""
    test_data = os.path.normpath(
        os.path.join(os.path.abspath(os.pardir), 'test data\\test_data1.KD')
    )
    args.path = test_data
    process(args)

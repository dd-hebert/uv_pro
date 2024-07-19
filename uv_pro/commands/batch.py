"""
Functions for the ``batch`` command.

@author: David Hebert
"""
import argparse
from uv_pro.commands.multiview import filter_files
from uv_pro.process import Dataset
from uv_pro.io.export import export_csv


def batch(args: argparse.Namespace) -> None:
    if files := filter_files(args.search_filters):
        files_exported = []

        for file in files:
            dataset = Dataset(
                path=file,
                view_only=True
            )

            files_exported.append(
                export_csv(
                    dataset=dataset,
                    data=dataset.get_chosen_traces(args.wavelengths),
                    suffix='Traces'
                )
            )

        if files_exported:
            print('Files exported:')
            [print(f'\t{file}') for file in files_exported]

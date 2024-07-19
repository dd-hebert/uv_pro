"""
Functions for the ``process`` command.

@author: David Hebert
"""
import os
import argparse
from uv_pro.process import Dataset
from uv_pro.quickfig import QuickFig
from uv_pro.plots import plot_spectra, plot_2x2
from uv_pro.io.export import prompt_for_export


def process(args: argparse.Namespace) -> None:
    """
    Process data.

    Initializes a :class:`~uv_pro.process.Dataset` with the
    given ``args``, plots the result, and prompts the user
    for exporting.
    """
    _handle_path(args)

    if args.view is True:
        dataset = Dataset(args.path, view_only=True)

    else:
        dataset = Dataset(
            args.path,
            trim=args.trim,
            slicing=_handle_slicing(args),
            fit_exp=args.fit_exp,
            fit_init_rate=args.init_rate,
            outlier_threshold=args.outlier_threshold,
            baseline_lambda=args.baseline_lambda,
            baseline_tolerance=args.baseline_tolerance,
            low_signal_window=args.low_signal_window,
            time_trace_window=args.time_trace_window,
            time_trace_interval=args.time_trace_interval,
            wavelengths=args.time_traces
        )

    print(dataset)
    _plot_and_export(args, dataset)


def _handle_path(args: argparse.Namespace) -> None:
    current_dir = os.getcwd()
    path_exists = os.path.exists(os.path.join(current_dir, args.path))

    if path_exists:
        args.path = os.path.join(current_dir, args.path)

    elif args.root_dir is not None and os.path.exists(os.path.join(args.root_dir, args.path)):
        args.path = os.path.join(args.root_dir, args.path)

    else:
        raise FileNotFoundError(f'No such file or directory could be found: "{args.path}"')


def _handle_slicing(args: argparse.Namespace) -> dict | None:
    if args.slice:
        return {'mode': 'equal', 'slices': args.slice}

    elif args.gradient_slice:
        return {
            'mode': 'gradient',
            'coeff': args.gradient_slice[0],
            'expo': args.gradient_slice[1]
        }

    elif args.specific_slice:
        return {
            'mode': 'specific',
            'times': args.specific_slice
        }

    return None


def _plot_and_export(args: argparse.Namespace, dataset: Dataset) -> None:
    """Plot a :class:`~uv_pro.process.Dataset` and prompt the user for export."""
    print('\nPlotting data...')
    if dataset.is_processed:
        files_exported = []

        if args.quick_fig is True:
            try:
                files_exported.append(getattr(QuickFig(dataset), 'exported_figure'))

            except AttributeError:
                pass

        else:
            plot_2x2(dataset, figsize=args.plot_size)

        if args.no_export is False:
            files_exported.extend(prompt_for_export(dataset))

        if files_exported:
            print(f'\nExport location: {os.path.dirname(args.path)}')
            print('Files exported:')
            [print(f'\t{file}') for file in files_exported]

    else:
        plot_spectra(dataset, dataset.raw_spectra)

"""
Path handling helper functions.

@author: David Hebert
"""

import argparse
import os
from pathlib import Path

def cleanup_path(path: Path) -> Path:
    path = Path(str(path).strip())
    path = path.expanduser()
    return path


def ensure_extension(path: Path, ext: str) -> str:
    if not path.suffix:
        return path.with_suffix(ext)
    return path


def resolve_path(path: Path, directories: list[str]) -> str:
    for d in directories:
        candidate = Path(d / path)
        if candidate.exists():
            return candidate.resolve()
    raise FileNotFoundError(f'No such file or directory could be found: "{path}"')


def handle_args_path(args: argparse.Namespace, default_ext: str = '.KD') -> None:
    args.path = cleanup_path(args.path)
    args.path = ensure_extension(args.path, default_ext)

    search_dirs = [os.getcwd()]
    if args.root_directory is not None:
        search_dirs.append(args.root_directory)

    args.path = resolve_path(args.path, search_dirs)


def get_files_in_root_dir(root_dir: Path, ext: str = '.KD'):
    paths = sorted({str(p.relative_to(root_dir)) for p in root_dir.rglob(f'*{ext}')}, key=str.lower)
    return paths


def get_unique_filename(output_dir: Path, base_filename: str, ext: str) -> str:
    """If a file named base_filename exists, add a number after."""
    n = 1
    unique_filename = Path(base_filename).with_suffix(ext)
    while output_dir.joinpath(unique_filename).exists():
        unique_filename = Path(base_filename + f' ({n})').with_suffix(ext)
        n += 1

    return unique_filename

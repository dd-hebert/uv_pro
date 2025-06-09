"""
Path handling helper functions.

@author: David Hebert
"""

import argparse
from pathlib import Path

def cleanup_path(path: str) -> Path:
    path = Path(path.strip()).expanduser()
    return path


def ensure_extension(path: Path, ext: str) -> str:
    if not path.suffix:
        return path.with_suffix(ext)
    return path


def resolve_path(path: Path, directories: list[Path], is_dir: bool = False) -> Path:
    if path.is_absolute():
        if (is_dir and path.is_dir()) or (not is_dir and path.is_file()):
            return path.resolve()

    for base in directories:
        candidate = base / path
        if (is_dir and candidate.is_dir()) or (not is_dir and candidate.is_file()):
            return candidate.resolve()

    kind = "directory" if is_dir else "file"
    raise FileNotFoundError(f'No such {kind} found: "{path}"')


def handle_args_path(args: argparse.Namespace, default_ext: str = '.KD') -> None:
    args.path = ensure_extension(args.path, default_ext)

    search_dirs = [Path.cwd()]
    if args.root_directory is not None:
        search_dirs.append(args.root_directory)

    args.path = resolve_path(args.path, search_dirs)


def handle_args_dir(args: argparse.Namespace) -> None:
    search_dirs = [Path.cwd()]
    if args.root_directory is not None:
        search_dirs.append(args.root_directory)

    args.directory = resolve_path(args.directory, search_dirs, is_dir=True)


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

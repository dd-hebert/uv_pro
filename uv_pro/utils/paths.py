"""
Path handling helper functions.

@author: David Hebert
"""

import argparse
import os

def cleanup_path(path: str) -> str:
    path = path.strip()
    path = os.path.expanduser(path)
    path = os.path.expandvars(path)
    return path


def ensure_extension(path: str, ext: str) -> str:
    if not os.path.splitext(path)[1]:
        return path + ext
    return path


def resolve_path(path: str, directories: list[str]) -> str:
    for d in directories:
        candidate = os.path.join(d, path)
        if os.path.exists(candidate):
            return candidate
    raise FileNotFoundError(f'No such file or directory could be found: "{path}"')


def handle_args_path(args: argparse.Namespace, default_ext: str = '.KD') -> None:
    args.path = cleanup_path(args.path)
    args.path = ensure_extension(args.path, default_ext)

    search_dirs = [os.getcwd()]
    if args.root_directory is not None:
        search_dirs.append(args.root_directory)

    args.path = resolve_path(args.path, search_dirs)

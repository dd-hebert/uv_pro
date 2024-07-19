"""
Default entry point if running the package using ``python -m uv_pro``.

@author: David Hebert
"""
import sys
from uv_pro.cli import CLI


def main():
    """Run uv_pro from cli script entry point."""
    cli = CLI()
    return 0


if __name__ == '__main__':
    sys.exit(main())

"""
Default entry point if running the package using ``python -m uv_pro``.

@author: David Hebert
"""
import sys
import uv_pro.scripts.cli


def main():
    """Run uv_pro from cli script entry point."""
    uv_pro.scripts.cli.CLI()
    return 0


if __name__ == '__main__':
    sys.exit(main())

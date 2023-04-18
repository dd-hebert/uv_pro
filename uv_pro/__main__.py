'''
Default entry point if running the package using::

    python -m uv_pro

'''
import sys
import uv_pro.cli


def main():
    '''Run uv_pro from cli script entry point.'''
    return uv_pro.cli.main()


if __name__ == '__main__':
    sys.exit(main())

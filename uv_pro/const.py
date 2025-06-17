"""
Constants for `uv_pro`.

@author: David Hebert
"""

import matplotlib.pyplot as plt

CMAPS = {
    name.casefold(): name
    for name in sorted(plt.colormaps() + ['default'], key=str.casefold)
}

# -*- coding: utf-8 -*-
"""
Change the current working directory to the ``uvp`` root directory.

@author: David
"""
import os
from uv_pro.utils.config import Config


def main():
    """
    Change the Change the current working directory to the ``uvp`` root directory.

    Returns
    -------
    None.

    """
    cf = Config()
    os.chdir(cf.config['Settings']['root_directory'])

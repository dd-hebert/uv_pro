File Paths
==========

``uv_pro`` is flexible in handling file paths. When you give a path at the terminal, you can provide
a full absolute path::

    uvp p C:\full\path\to\your\data\file.KD


Alternatively, you can open a terminal session inside a directory containing a data file and use a relative path::

    # Current working directory = C:\full\path\to\your\data
    uvp p file.KD

The Root Directory
------------------

``uv_pro`` has a helpful root directory feature ``root`` or ``rt`` which you can use to shorten the file paths you type.
The ``uv_pro`` workflow works best when you keep all of your data files inside a common root folder. If this is
the case, you can set the root directory at the terminal::

    uvp rt -set C:\full\path\to\your\data

With the root directory set, you can now use shorter paths (relative to the root directory) from *anywhere*::

    # From inside any directory
    uvp p file.KD

.. Note::
    You can check the path of the current root directory with ``-get``::

        uvp rt -get

    You can clear the root directory with ``-clear``::

        uvp rt -clear


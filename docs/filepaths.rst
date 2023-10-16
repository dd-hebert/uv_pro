File Paths
==========

``uv_pro`` is flexible in handling file paths. When you give a path at the terminal with ``-p``, you can provide
a full absolute path::

    uvp -p C:\full\path\to\your\data\file.KD


Alternatively, you can open a terminal session inside a folder containing a data file and a relative path::

    # Current working directory = C:\full\path\to\you\data
    uvp -p file.KD

``uv_pro`` has a helpful root directory feature ``-rd`` which you can use to shorten the file paths you type.
The ``uv_pro`` workflow works best when you keep all of your data files inside a common root folder. If this is
the case, you can set the root directory at the terminal::

    uvp -rd C:\full\path\to\your\data

With the root directory set, you can now use shorter relative paths from *anywhere*::

    # From inside any directory
    uvp -p file.KD

.. Note::
    You can check if a root directory is set with ``-grd``::

        uvp -grd
    
    You can delete the root directory with ``-crd``::

        uvp -crd


Installation
============
If you have git installed on your system, you can install ``uv_pro`` directly from the repo using pip::

    pip install git+https://github.com/dd-hebert/uv_pro.git

Otherwise, clone the repo and build the package using ``setuptools``::

    # From inside repo
    python -m build

Then use pip to install the newly created ``.whl`` file::

    # .whl file can be found in /repo/dist/
    pip install uv_pro-x.x.x-py3-none-any.whl


Uninstall
---------
To uninstall ``uv_pro`` run the following commands::

    pip uninstall uv_pro

The ``uv_pro`` configuration files are located ``.config/uv_pro`` which can be found in your home directory.
You can safely delete the ``uv_pro`` folder inside ``.config`` at any time.
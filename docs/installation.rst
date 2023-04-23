Installation
============

``uv_pro`` is not yet available on `The Python Package Index <https://pypi.org/>`_.

To install ``uv_pro``:

- Clone the repo to your machine.
- Start a terminal session from inside the main repo folder ``C:\\...\\uv_pro\\`` where the ``pyproject.toml`` file is located.
- Build the package::

    python -m build

- Use pip to install the newly built .whl file inside the uv_pro\\dist folder::

    cd dist
    pip install uv_pro-0.1.0-py3-none-any.whl

The name of the .whl file above is just an example. Use the actual name of the .whl file in your \\dist\\ folder

Uninstall
---------
You can uninstall ``uv_pro`` at any time with::

    pip uninstall uv_pro

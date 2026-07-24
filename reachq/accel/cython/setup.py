"""Cython extension build configuration for reachq acceleration kernels.

Build::

    cd reachq/accel/cython
    python setup.py build_ext --inplace

After a successful build, ``_cy_bfs*.so`` and ``_cy_dijkstra*.so``
appear next to the ``.pyx`` files. The wrapper modules
``reachq.accel.cython.bfs`` and ``reachq.accel.cython.dijkstra``
will pick them up automatically.

Alternatively, install the wheels built by cibuildwheel from
``reachq[accel]`` distribution on PyPI.
"""

from __future__ import annotations

import os

import numpy as np
from setuptools import Extension, setup


def _numpy_include() -> list[str]:
    """Return numpy include path."""
    return [np.get_include()]


def _pyx_files() -> list[str]:
    here = os.path.dirname(os.path.abspath(__file__))
    return [
        os.path.join(here, name)
        for name in os.listdir(here)
        if name.endswith(".pyx")
    ]


def _module_name_from_path(path: str) -> str:
    base = os.path.splitext(os.path.basename(path))[0]
    # Files named bfs.pyx -> _cy_bfs; dijkstra.pyx -> _cy_dijkstra.
    return f"_cy_{base}"


setup(
    name="reachq_cython_kernels",
    ext_modules=[
        Extension(
            name=_module_name_from_path(path),
            sources=[path],
            include_dirs=_numpy_include(),
            extra_compile_args=["-O3", "-march=native"],
            extra_link_args=["-O3"],
            language="c",
        )
        for path in _pyx_files()
    ],
)
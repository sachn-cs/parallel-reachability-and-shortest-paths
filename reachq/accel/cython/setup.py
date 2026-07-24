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

from setuptools import Extension, setup


def _pyx_files() -> list[str]:
    here = os.path.dirname(os.path.abspath(__file__))
    return [
        os.path.join(here, name)
        for name in os.listdir(here)
        if name.endswith(".pyx")
    ]


setup(
    name="reachq_cython_kernels",
    ext_modules=[
        Extension(
            # Module name derived from the .pyx filename: bfs.pyx ->
            # _cy_bfs, dijkstra.pyx -> _cy_dijkstra.
            name=os.path.splitext(os.path.basename(path))[0]
            if path.endswith(".pyx")
            else path,
            sources=[path],
            extra_compile_args=["-O3", "-march=native"],
            extra_link_args=["-O3"],
            language="c",
        )
        for path in _pyx_files()
    ],
)
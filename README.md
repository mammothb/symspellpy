symspellpy <br>
[![PyPI version](https://badge.fury.io/py/symspellpy.svg)](https://badge.fury.io/py/symspellpy)
[![Tests](https://github.com/mammothb/symspellpy/actions/workflows/tests.yml/badge.svg)](https://github.com/mammothb/symspellpy/actions/workflows/tests.yml)
[![Documentation Status](https://readthedocs.org/projects/symspellpy/badge/?version=latest)](https://symspellpy.readthedocs.io/en/latest/?badge=latest)
[![codecov](https://codecov.io/gh/mammothb/symspellpy/branch/master/graph/badge.svg)](https://codecov.io/gh/mammothb/symspellpy)
========

symspellpy is a Python port of [SymSpell](https://github.com/wolfgarbe/SymSpell) v6.7.1, which provides much higher speed and lower memory consumption. Unit tests
from the original project are implemented to ensure the accuracy of the port.

Please note that the port has not been optimized for speed.

Notable Changes
===============
v6.7.2: Implemented fast distance comparer with [editdistpy](https://github.com/mammothb/editdistpy). Approximately 2x speed up for usage under default settings, benchmarks found [here](https://github.com/mammothb/symspellpy/blob/master/tests/benchmarks.ipynb).

Install
=======
For installation instructions, see the `INSTALL.rst` file or the [install](https://symspellpy.readthedocs.io/en/latest/users/installing.html) documentation.

Usage
=====
Check out the [examples](https://symspellpy.readthedocs.io/en/latest/examples/index.html) provided for sample usage.

# MIT License
#
# Copyright (c) 2022 mmb L (Python port)
# Copyright (c) 2021 Wolf Garbe (Original C# implementation)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

"""
.. module:: verbosity
   :synopsis: Enum for lookup results verbosity.
"""

from enum import Enum


class Verbosity(Enum):
    """Controls the closeness/quantity of returned spelling suggestions.

    Attributes:
        TOP: Top suggestion with the highest term frequency of the suggestions of
            smallest edit distance found.
        CLOSEST: All suggestions of smallest edit distance found, suggestions
            ordered by term frequency.
        ALL: All suggestions within maxEditDistance, suggestions ordered by edit
            distance, then by term frequency (slower, no early termination).
    """

    TOP = 0
    CLOSEST = 1
    ALL = 2

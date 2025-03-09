# MIT License
#
# Copyright (c) 2025 mmb L (Python port)
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
.. module:: compostiion
   :synopsis: Data class for :meth:`symspellpy.symspellpy.word_segmentation`.
"""

from typing import NamedTuple


class Composition(NamedTuple):
    """Used by :meth:`word_segmentation`.

    Attributes:
        segmented_string: The word segmented string.
        corrected_string: The spelling corrected string.
        distance_sum: The sum of edit distance between input string and
            corrected string
        log_prob_sum: The sum of word occurrence probabilities in log
            scale (a measure of how common and probable the corrected
            segmentation is).
    """

    segmented_string: str = ""
    corrected_string: str = ""
    distance_sum: int = 0
    log_prob_sum: float = 0

    @classmethod
    def create(
        cls,
        composition: "Composition",
        segmented_part: str,
        corrected_part: str,
        distance: int,
        log_prob: float,
    ) -> "Composition":
        """Creates a Composition by appending to an existing Composition."""
        return cls(
            composition.segmented_string + segmented_part,
            composition.corrected_string + corrected_part,
            composition.distance_sum + distance,
            composition.log_prob_sum + log_prob,
        )

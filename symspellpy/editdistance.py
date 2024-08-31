# MIT License
#
# Copyright (c) 2024 mmb L (Python port)
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
.. module:: editdistance
   :synopsis: Module for edit distance algorithms.
"""

import warnings
from enum import Enum
from typing import List, Optional

from editdistpy import damerau_osa, levenshtein

from symspellpy import helpers
from symspellpy.abstract_distance_comparer import AbstractDistanceComparer


class DistanceAlgorithm(Enum):
    """Supported edit distance algorithms."""

    LEVENSHTEIN = 0  #: Levenshtein algorithm.
    DAMERAU_OSA = 1  #: Damerau optimal string alignment algorithm
    LEVENSHTEIN_FAST = 2  #: Fast Levenshtein algorithm.
    DAMERAU_OSA_FAST = 3  #: Fast Damerau optimal string alignment algorithm
    USER_PROVIDED = 4  #: User provided custom edit distance algorithm


class EditDistance:
    """Edit distance algorithms.

    Args:
        algorithm: The distance algorithm to use.

    Attributes:
        _algorithm (:class:`DistanceAlgorithm`): The edit distance algorithm to
            use.
        _distance_comparer (:class:`AbstractDistanceComparer`): An object to
            compute the relative distance between two strings. The concrete
            object will be chosen based on the value of :attr:`_algorithm`.

    Raises:
        ValueError: If `algorithm` specifies an invalid distance algorithm.
    """

    def __init__(
        self,
        algorithm: DistanceAlgorithm,
        comparer: Optional[AbstractDistanceComparer] = None,
    ) -> None:
        if algorithm != DistanceAlgorithm.USER_PROVIDED and comparer is not None:
            warnings.warn(
                f"A comparer is passed in but algorithm is not {DistanceAlgorithm.USER_PROVIDED.value}. A built-in comparer will be used."
            )

        self._distance_comparer: AbstractDistanceComparer
        self._algorithm = algorithm
        if algorithm == DistanceAlgorithm.LEVENSHTEIN:
            self._distance_comparer = Levenshtein()
        elif algorithm == DistanceAlgorithm.DAMERAU_OSA:
            self._distance_comparer = DamerauOsa()
        elif algorithm == DistanceAlgorithm.LEVENSHTEIN_FAST:
            self._distance_comparer = LevenshteinFast()
        elif algorithm == DistanceAlgorithm.DAMERAU_OSA_FAST:
            self._distance_comparer = DamerauOsaFast()
        elif algorithm == DistanceAlgorithm.USER_PROVIDED:
            if not isinstance(comparer, AbstractDistanceComparer):
                raise ValueError(
                    f"{algorithm.value} selected but no comparer passed in."
                )
            self._distance_comparer = comparer
        else:
            raise ValueError("unknown distance algorithm")

    def compare(self, string_1: str, string_2: str, max_distance: int) -> int:
        """Compares a string to the base string to determine the edit distance,
        using the previously selected algorithm.

        Args:
            string_1: Base string.
            string_2: The string to compare.
            max_distance: The maximum distance allowed.

        Returns:
            The edit distance (or -1 if `max_distance` exceeded).
        """
        return self._distance_comparer.distance(string_1, string_2, max_distance)


class Levenshtein(AbstractDistanceComparer):
    """Provides Levenshtein algorithm for computing edit distance metric between
    two strings.

    Attributes:
        _base_char_1_costs (List[int]):
    """

    def __init__(self):
        self._base_char_1_costs = []

    def distance(self, string_1: str, string_2: str, max_distance: int) -> int:
        """Computes the Levenshtein edit distance between two strings.

        Args:
            string_1: One of the strings to compare.
            string_2: The other string to compare.
            max_distance: The maximum distance that is of interest.

        Returns:
            -1 if the distance is greater than the max_distance, 0 if the strings
                are equivalent, otherwise a positive number whose magnitude
                increases as difference between the strings increases.
        """
        if string_1 is None or string_2 is None:
            return helpers.null_distance_results(string_1, string_2, max_distance)
        if max_distance <= 0:
            return 0 if string_1 == string_2 else -1
        max_distance = int(min(2**31 - 1, max_distance))
        # if strings of different lengths, ensure shorter string is in string_1.
        # This can result in a little faster speed by spending more time spinning
        # just the inner loop during the main processing.
        if len(string_1) > len(string_2):
            string_2, string_1 = string_1, string_2
        if len(string_2) - len(string_1) > max_distance:
            return -1
        # identify common suffic and/or prefix that can be ignored
        len_1, len_2, start = helpers.prefix_suffix_prep(string_1, string_2)
        if len_1 == 0:
            return len_2 if len_2 <= max_distance else -1

        if len_2 > len(self._base_char_1_costs):
            self._base_char_1_costs = [0 for _ in range(len_2)]
        if max_distance < len_2:
            return self._distance_max(
                string_1,
                string_2,
                len_1,
                len_2,
                start,
                max_distance,
                self._base_char_1_costs,
            )
        return self._distance(
            string_1, string_2, len_1, len_2, start, self._base_char_1_costs
        )

    @staticmethod
    def _distance(
        string_1: str,
        string_2: str,
        len_1: int,
        len_2: int,
        start: int,
        char_1_costs: List[int],
    ) -> int:
        """Internal implementation of the core Levenshtein algorithm.

        **From**: https://github.com/softwx/SoftWx.Match
        """
        char_1_costs = [j + 1 for j in range(len_2)]
        current_cost = 0
        for i in range(len_1):
            left_char_cost = above_char_cost = i
            char_1 = string_1[start + i]
            for j in range(len_2):
                # cost of diagonal (substitution)
                current_cost = left_char_cost
                left_char_cost = char_1_costs[j]
                if string_2[start + j] != char_1:
                    # substitution if neither of the two conditions below
                    if above_char_cost < current_cost:
                        current_cost = above_char_cost
                    if left_char_cost < current_cost:
                        current_cost = left_char_cost
                    current_cost += 1
                char_1_costs[j] = above_char_cost = current_cost
        return current_cost

    @staticmethod
    def _distance_max(
        string_1: str,
        string_2: str,
        len_1: int,
        len_2: int,
        start: int,
        max_distance: int,
        char_1_costs: List[int],
    ) -> int:
        """Internal implementation of the core Levenshtein algorithm that accepts
        a max_distance.

        **From**: https://github.com/softwx/SoftWx.Match
        """
        char_1_costs = [
            j + 1 if j < max_distance else max_distance + 1 for j in range(len_2)
        ]
        len_diff = len_2 - len_1
        j_start_offset = max_distance - len_diff
        j_start = 0
        j_end = max_distance
        current_cost = 0
        for i in range(len_1):
            char_1 = string_1[start + i]
            prev_char_1_cost = above_char_cost = i
            # no need to look beyond window of lower right diagonal -
            # max_distance cells (lower right diag is i - lenDiff) and the upper
            # left diagonal + max_distance cells (upper left is i)
            j_start += 1 if i > j_start_offset else 0
            j_end += 1 if j_end < len_2 else 0
            for j in range(j_start, j_end):
                # cost of diagonal (substitution)
                current_cost = prev_char_1_cost
                prev_char_1_cost = char_1_costs[j]
                if string_2[start + j] != char_1:
                    # substitution if neither of the two conditions below
                    if above_char_cost < current_cost:
                        current_cost = above_char_cost
                    if prev_char_1_cost < current_cost:
                        current_cost = prev_char_1_cost
                    current_cost += 1
                char_1_costs[j] = above_char_cost = current_cost
            if char_1_costs[i + len_diff] > max_distance:
                return -1
        return current_cost if current_cost <= max_distance else -1


class DamerauOsa(AbstractDistanceComparer):
    """Provides optimized methods for computing Damerau-Levenshtein Optimal
    String Alignment (OSA) comparisons between two strings.

    Attributes:
        _base_char_1_costs (List[int]):
        _base_prev_char_1_costs (List[int]):
    """

    def __init__(self) -> None:
        self._base_char_1_costs: List[int] = []
        self._base_prev_char_1_costs: List[int] = []

    def distance(self, string_1: str, string_2: str, max_distance: int) -> int:
        """Computes the Damerau-Levenshtein optimal string alignment edit
        distance between two strings.

        Args:
            string_1: One of the strings to compare.
            string_2: The other string to compare.
            max_distance: The maximum distance that is of interest.

        Returns:
            -1 if the distance is greater than the max_distance, 0 if the strings
                are equivalent, otherwise a positive number whose magnitude
                increases as difference between the strings increases.
        """
        if string_1 is None or string_2 is None:
            return helpers.null_distance_results(string_1, string_2, max_distance)
        if max_distance <= 0:
            return 0 if string_1 == string_2 else -1
        max_distance = int(min(2**31 - 1, max_distance))
        # if strings of different lengths, ensure shorter string is in string_1.
        # This can result in a little faster speed by spending more time spinning
        # just the inner loop during the main processing.
        if len(string_1) > len(string_2):
            string_2, string_1 = string_1, string_2
        if len(string_2) - len(string_1) > max_distance:
            return -1
        # identify common suffix and/or prefix that can be ignored
        len_1, len_2, start = helpers.prefix_suffix_prep(string_1, string_2)
        if len_1 == 0:
            return len_2 if len_2 <= max_distance else -1

        if len_2 > len(self._base_char_1_costs):
            self._base_char_1_costs = [0 for _ in range(len_2)]
            self._base_prev_char_1_costs = [0 for _ in range(len_2)]
        if max_distance < len_2:
            return self._distance_max(
                string_1,
                string_2,
                len_1,
                len_2,
                start,
                max_distance,
                self._base_char_1_costs,
                self._base_prev_char_1_costs,
            )
        return self._distance(
            string_1,
            string_2,
            len_1,
            len_2,
            start,
            self._base_char_1_costs,
            self._base_prev_char_1_costs,
        )

    @staticmethod
    def _distance(
        string_1: str,
        string_2: str,
        len_1: int,
        len_2: int,
        start: int,
        char_1_costs: List[int],
        prev_char_1_costs: List[int],
    ) -> int:
        """Internal implementation of the core Damerau-Levenshtein, optimal
        string alignment algorithm.

        **From**: https://github.com/softwx/SoftWx.Match
        """
        char_1_costs = [j + 1 for j in range(len_2)]
        char_1 = " "
        current_cost = 0
        for i in range(len_1):
            prev_char_1 = char_1
            char_1 = string_1[start + i]
            char_2 = " "
            left_char_cost = above_char_cost = i
            next_trans_cost = 0
            for j in range(len_2):
                this_trans_cost = next_trans_cost
                next_trans_cost = prev_char_1_costs[j]
                # cost of diagonal (substitution)
                prev_char_1_costs[j] = current_cost = left_char_cost
                # left now equals current cost (which will be diagonal
                # at next iteration)
                left_char_cost = char_1_costs[j]
                prev_char_2 = char_2
                char_2 = string_2[start + j]
                if char_1 != char_2:
                    # substitution if neither of two conditions below
                    if above_char_cost < current_cost:
                        current_cost = above_char_cost
                    if left_char_cost < current_cost:
                        current_cost = left_char_cost
                    current_cost += 1
                    if (
                        i != 0
                        and j != 0
                        and char_1 == prev_char_2
                        and prev_char_1 == char_2
                        and this_trans_cost + 1 < current_cost
                    ):
                        # transposition
                        current_cost = this_trans_cost + 1
                char_1_costs[j] = above_char_cost = current_cost
        return current_cost

    @staticmethod
    def _distance_max(
        string_1: str,
        string_2: str,
        len_1: int,
        len_2: int,
        start: int,
        max_distance: int,
        char_1_costs: List[int],
        prev_char_1_costs: List[int],
    ) -> int:
        """Internal implementation of the core Damerau-Levenshtein, optimal
        string alignment algorithm that accepts a max_distance.

        **From**: https://github.com/softwx/SoftWx.Match
        """
        char_1_costs = [
            j + 1 if j < max_distance else max_distance + 1 for j in range(len_2)
        ]
        len_diff = len_2 - len_1
        j_start_offset = max_distance - len_diff
        j_start = 0
        j_end = max_distance
        char_1 = " "
        current_cost = 0
        for i in range(len_1):
            prev_char_1 = char_1
            char_1 = string_1[start + i]
            char_2 = " "
            left_char_cost = above_char_cost = i
            next_trans_cost = 0
            # no need to look beyond window of lower right diagonal -
            # max_distance cells (lower right diag is i - len_diff) and the upper
            # left diagonal + max_distance cells (upper left is i)
            j_start += 1 if i > j_start_offset else 0
            j_end += 1 if j_end < len_2 else 0
            for j in range(j_start, j_end):
                this_trans_cost = next_trans_cost
                next_trans_cost = prev_char_1_costs[j]
                # cost of diagonal (substitution)
                prev_char_1_costs[j] = current_cost = left_char_cost
                # left now equals current cost (which will be diagonal at next
                # iteration)
                left_char_cost = char_1_costs[j]
                prev_char_2 = char_2
                char_2 = string_2[start + j]
                if char_1 != char_2:
                    # substitution if neither of two conditions below
                    if above_char_cost < current_cost:
                        current_cost = above_char_cost
                    if left_char_cost < current_cost:
                        current_cost = left_char_cost
                    current_cost += 1
                    if (
                        i != 0
                        and j != 0
                        and char_1 == prev_char_2
                        and prev_char_1 == char_2
                        and this_trans_cost + 1 < current_cost
                    ):
                        # transposition
                        current_cost = this_trans_cost + 1
                char_1_costs[j] = above_char_cost = current_cost
            if char_1_costs[i + len_diff] > max_distance:
                return -1
        return current_cost if current_cost <= max_distance else -1


class LevenshteinFast(AbstractDistanceComparer):
    """Provides an interface for computing edit distance metric between two
    strings using the fast Levenshtein algorithm.
    """

    def distance(self, string_1: str, string_2: str, max_distance: int) -> int:
        """Computes the Levenshtein edit distance between two strings.

        Args:
            string_1: One of the strings to compare.
            string_2: The other string to compare.
            max_distance: The maximum distance that is of interest.

        Returns:
            -1 if the distance is greater than the max_distance, 0 if the strings
                are equivalent, otherwise a positive number whose magnitude
                increases as difference between the strings increases.
        """
        return levenshtein.distance(string_1, string_2, max_distance)


class DamerauOsaFast(AbstractDistanceComparer):
    """Provides an interface for computing edit distance metric between two
    strings using the fast Damerau-Levenshtein Optimal String Alignment (OSA)
    algorithm.
    """

    def distance(self, string_1: str, string_2: str, max_distance: int) -> int:
        """Computes the Damerau-Levenshtein optimal string alignment edit
        distance between two strings.

        Args:
            string_1: One of the strings to compare.
            string_2: The other string to compare.
            max_distance: The maximum distance that is of interest.

        Returns:
            -1 if the distance is greater than the max_distance, 0 if the strings
                are equivalent, otherwise a positive number whose magnitude
                increases as difference between the strings increases.
        """
        return damerau_osa.distance(string_1, string_2, max_distance)

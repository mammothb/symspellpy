"""
.. module:: editdistance
   :synopsis: Module for edit distance algorithms.
"""
from enum import Enum

import symspellpy.helpers as helpers

class DistanceAlgorithm(Enum):
    """Supported edit distance algorithms"""
    LEVENSHTEIN = 0  #: Levenshtein algorithm.
    DAMERUAUOSA = 1  #: Damerau optimal string alignment algorithm

class EditDistance(object):
    """Edit distance algorithms.

    Parameters
    ----------
    algorithm : :class:`DistanceAlgorithm`
        The distance algorithm to use.

    Attributes
    ----------
    _algorithm : :class:`DistanceAlgorithm`
        The edit distance algorithm to use.
    _distance_comparer : :class:`AbstractDistanceComparer`
        An object to compute the relative distance between two strings.
        The concrete object will be chosen based on the value of
        :attr:`_algorithm`

    Raises
    ------
    ValueError
        If `algorithm` specifies an invalid distance algorithm.
    """
    def __init__(self, algorithm):
        self._algorithm = algorithm
        if algorithm == DistanceAlgorithm.LEVENSHTEIN:
            self._distance_comparer = Levenshtein()
        elif algorithm == DistanceAlgorithm.DAMERUAUOSA:
            self._distance_comparer = DamerauOsa()
        else:
            raise ValueError("Unknown distance algorithm")

    def compare(self, string_1, string_2, max_distance):
        """Compare a string to the base string to determine the edit
        distance, using the previously selected algorithm.

        Parameters
        ----------
        string_1 : str
            Base string.
        string_2 : str
            The string to compare.
        max_distance : int
            The maximum distance allowed.

        Returns
        -------
        int
            The edit distance (or -1 if `max_distance` exceeded).
        """
        return self._distance_comparer.distance(string_1, string_2,
                                                max_distance)

class AbstractDistanceComparer(object):
    """An interface to compute relative distance between two strings"""
    def distance(self, string_1, string_2, max_distance):
        """Return a measure of the distance between two strings.

        Parameters
        ----------
        string_1 : str
            One of the strings to compare.
        string_2 : str
            The other string to compare.
        max_distance : int
            The maximum distance that is of interest.

        Returns
        -------
        int
            -1 if the distance is greater than the max_distance, 0 if
            the strings are equivalent, otherwise a positive number
            whose magnitude increases as difference between the strings
            increases.

        Raises
        ------
        NotImplementedError
            If called from abstract class instead of concrete class
        """
        raise NotImplementedError("Should have implemented this")

class Levenshtein(AbstractDistanceComparer):
    """Class providing Levenshtein algorithm for computing edit
    distance metric between two strings

    Attributes
    ----------
    _base_char_1_costs : numpy.ndarray
    """
    def __init__(self):
        self._base_char_1_costs = []

    def distance(self, string_1, string_2, max_distance):
        """Compute and return the Levenshtein edit distance between two
        strings.

        Parameters
        ----------
        string_1 : str
            One of the strings to compare.
        string_2 : str
            The other string to compare.
        max_distance : int
            The maximum distance that is of interest.

        Returns
        -------
        int
            -1 if the distance is greater than the maxDistance, 0 if
            the strings are equivalent, otherwise a positive number
            whose magnitude increases as difference between the strings
            increases.
        """
        if string_1 is None or string_2 is None:
            return helpers.null_distance_results(string_1, string_2,
                                                 max_distance)
        if max_distance <= 0:
            return 0 if string_1 == string_2 else -1
        max_distance = max_distance = int(min(2 ** 31 - 1, max_distance))
        # if strings of different lengths, ensure shorter string is in
        # string_1. This can result in a little faster speed by
        # spending more time spinning just the inner loop during the
        # main processing.
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
            return self._distance_max(string_1, string_2, len_1, len_2,
                                      start, max_distance,
                                      self._base_char_1_costs)
        return self._distance(string_1, string_2, len_1, len_2, start,
                              self._base_char_1_costs)

    def _distance(self, string_1, string_2, len_1, len_2, start,
                  char_1_costs):
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
                    # substitution if neither of the two conditions
                    # below
                    if above_char_cost < current_cost:
                        current_cost = above_char_cost
                    if left_char_cost < current_cost:
                        current_cost = left_char_cost
                    current_cost += 1
                char_1_costs[j] = above_char_cost = current_cost
        return current_cost

    def _distance_max(self, string_1, string_2, len_1, len_2, start,
                      max_distance, char_1_costs):
        """Internal implementation of the core Levenshtein algorithm
        that accepts a max_distance.

        **From**: https://github.com/softwx/SoftWx.Match
        """
        char_1_costs = [j + 1 if j < max_distance else max_distance + 1
                        for j in range(len_2)]
        len_diff = len_2 - len_1
        j_start_offset = max_distance - len_diff
        j_start = 0
        j_end = max_distance
        current_cost = 0
        for i in range(len_1):
            char_1 = string_1[start + i]
            prev_char_1_cost = above_char_cost = i
            # no need to look beyond window of lower right
            # diagonal - max_distance cells (lower right diag is
            # i - lenDiff) and the upper left diagonal +
            # max_distance cells (upper left is i)
            j_start += 1 if i > j_start_offset else 0
            j_end += 1 if j_end < len_2 else 0
            for j in range(j_start, j_end):
                # cost of diagonal (substitution)
                current_cost = prev_char_1_cost
                prev_char_1_cost = char_1_costs[j]
                if string_2[start + j] != char_1:
                    # substitution if neither of the two conditions
                    # below
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
    """Class providing optimized methods for computing
    Damerau-Levenshtein Optimal String Alignment (OSA) comparisons
    between two strings.

    Attributes
    ----------
    _base_char_1_costs : numpy.ndarray
    _base_prev_char_1_costs : numpy.ndarray

    """
    def __init__(self):
        self._base_char_1_costs = []
        self._base_prev_char_1_costs = []

    def distance(self, string_1, string_2, max_distance):
        """Compute and return the Damerau-Levenshtein optimal string
        alignment edit distance between two strings.

        Parameters
        ----------
        string_1 : str
            One of the strings to compare.
        string_2 : str
            The other string to compare.
        max_distance : int
            The maximum distance that is of interest.

        Returns
        -------
        int
            -1 if the distance is greater than the maxDistance, 0 if
            the strings are equivalent, otherwise a positive number
            whose magnitude increases as difference between the strings
            increases.
        """
        if string_1 is None or string_2 is None:
            return helpers.null_distance_results(string_1, string_2,
                                                 max_distance)
        if max_distance <= 0:
            return 0 if string_1 == string_2 else -1
        max_distance = int(min(2 ** 31 - 1, max_distance))
        # if strings of different lengths, ensure shorter string is in
        # string_1. This can result in a little faster speed by
        # spending more time spinning just the inner loop during the
        # main processing.
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
            return self._distance_max(string_1, string_2, len_1, len_2,
                                      start, max_distance,
                                      self._base_char_1_costs,
                                      self._base_prev_char_1_costs)
        return self._distance(string_1, string_2, len_1, len_2, start,
                              self._base_char_1_costs,
                              self._base_prev_char_1_costs)

    def _distance(self, string_1, string_2, len_1, len_2, start,
                  char_1_costs, prev_char_1_costs):
        """Internal implementation of the core Damerau-Levenshtein,
        optimal string alignment algorithm.

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
                    if (i != 0 and j != 0
                            and char_1 == prev_char_2
                            and prev_char_1 == char_2
                            and this_trans_cost + 1 < current_cost):
                        # transposition
                        current_cost = this_trans_cost + 1
                char_1_costs[j] = above_char_cost = current_cost
        return current_cost

    def _distance_max(self, string_1, string_2, len_1, len_2, start,
                      max_distance, char_1_costs, prev_char_1_costs):
        """Internal implementation of the core Damerau-Levenshtein,
        optimal string alignment algorithm that accepts a max_distance.

        **From**: https://github.com/softwx/SoftWx.Match
        """
        char_1_costs = [j + 1 if j < max_distance else max_distance + 1
                        for j in range(len_2)]
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
            # max_distance cells (lower right diag is i - len_diff) and
            # the upper left diagonal + max_distance cells (upper left
            # is i)
            j_start += 1 if i > j_start_offset else 0
            j_end += 1 if j_end < len_2 else 0
            for j in range(j_start, j_end):
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
                    if (i != 0 and j != 0 and char_1 == prev_char_2
                            and prev_char_1 == char_2
                            and this_trans_cost + 1 < current_cost):
                        # transposition
                        current_cost = this_trans_cost + 1
                char_1_costs[j] = above_char_cost = current_cost
            if char_1_costs[i + len_diff] > max_distance:
                return -1
        return current_cost if current_cost <= max_distance else -1

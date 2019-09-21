from itertools import combinations, permutations
import sys
import unittest

import numpy as np
import pytest

from symspellpy.editdistance import (AbstractDistanceComparer, DamerauOsa,
                                     EditDistance, Levenshtein)

def build_test_strings():
    alphabet = "abcd"
    strings = [""]
    for i in range(1, len(alphabet) + 1):
        for combi in combinations(alphabet, i):
            strings += ["".join(p) for p in permutations(combi)]
    return strings

def get_levenshtein(string_1, string_2, max_distance):
    max_distance = max_distance = int(min(2 ** 31 - 1, max_distance))
    len_1 = len(string_1)
    len_2 = len(string_2)
    d = np.zeros((len_1 + 1, len_2 + 1))
    for i in range(len_1 + 1):
        d[i, 0] = i
    for i in range(len_2 + 1):
        d[0, i] = i
    for j in range(1, len_2 + 1):
        for i in range(1, len_1 + 1):
            if string_1[i - 1] == string_2[j - 1]:
                # no operation
                d[i, j] = d[i - 1, j - 1]
            else:
                d[i, j] = min(min(d[i - 1, j] + 1,
                                  d[i, j - 1] + 1),
                              d[i - 1, j - 1] + 1)
    distance = d[len_1, len_2]
    return distance if distance <= max_distance else -1

def get_damerau_osa(string_1, string_2, max_distance):
    max_distance = max_distance = int(min(2 ** 31 - 1, max_distance))
    len_1 = len(string_1)
    len_2 = len(string_2)
    d = np.zeros((len_1 + 1, len_2 + 1))
    for i in range(len_1 + 1):
        d[i, 0] = i
    for i in range(len_2 + 1):
        d[0, i] = i
    for i in range(1, len_1 + 1):
        for j in range(1, len_2 + 1):
            cost = 0 if string_1[i - 1] == string_2[j - 1] else 1
            d[i, j] = min(min(d[i - 1, j] + 1,
                              d[i, j - 1] + 1),
                          d[i - 1, j - 1] + cost)
            if (i > 1 and j > 1 and string_1[i - 1] == string_2[j - 2]
                    and string_1[i - 2] == string_2[j - 1]):
                d[i, j] = min(d[i, j], d[i - 2, j - 2] + cost)
    distance = d[len_1, len_2]
    return distance if distance <= max_distance else -1

class TestEditDistance(unittest.TestCase):
    test_strings = build_test_strings()

    def test_unknown_distance_algorithm(self):
        with pytest.raises(ValueError) as excinfo:
            __ = EditDistance(2)
        self.assertEqual("Unknown distance algorithm", str(excinfo.value))

    def test_abstract_distance_comparer(self):
        with pytest.raises(NotImplementedError) as excinfo:
            comparer = AbstractDistanceComparer()
            __ = comparer.distance("string_1", "string_2", 10)
        self.assertEqual("Should have implemented this", str(excinfo.value))

    def test_levenshtein_match_ref_max_0(self):
        max_distance = 0

        comparer = Levenshtein()
        for s1 in self.test_strings:
            for s2 in self.test_strings:
                self.assertEqual(get_levenshtein(s1, s2, max_distance),
                                 comparer.distance(s1, s2, max_distance))

    def test_levenshtein_match_ref_max_1(self):
        max_distance = 1

        comparer = Levenshtein()
        for s1 in self.test_strings:
            for s2 in self.test_strings:
                self.assertEqual(get_levenshtein(s1, s2, max_distance),
                                 comparer.distance(s1, s2, max_distance))

    def test_levenshtein_match_ref_max_3(self):
        max_distance = 3

        comparer = Levenshtein()
        for s1 in self.test_strings:
            for s2 in self.test_strings:
                print(s1, s2)
                self.assertEqual(get_levenshtein(s1, s2, max_distance),
                                 comparer.distance(s1, s2, max_distance))

    def test_levenshtein_match_ref_max_huge(self):
        max_distance = sys.maxsize

        comparer = Levenshtein()
        for s1 in self.test_strings:
            for s2 in self.test_strings:
                self.assertEqual(get_levenshtein(s1, s2, max_distance),
                                 comparer.distance(s1, s2, max_distance))

    def test_levenshtein_null_distance(self):
        max_distance = 10
        short_string = "string"
        long_string = "long_string"

        comparer = Levenshtein()
        distance = comparer.distance(short_string, None, max_distance)
        self.assertEqual(len(short_string), distance)

        distance = comparer.distance(long_string, None, max_distance)
        self.assertEqual(-1, distance)

        distance = comparer.distance(None, short_string, max_distance)
        self.assertEqual(len(short_string), distance)

        distance = comparer.distance(None, long_string, max_distance)
        self.assertEqual(-1, distance)

        distance = comparer.distance(None, None, max_distance)
        self.assertEqual(0, distance)

    def test_levenshtein_negative_max_distance(self):
        max_distance_1 = 0
        short_string = "string"
        long_string = "long_string"

        comparer = Levenshtein()
        distance = comparer.distance(short_string, None, max_distance_1)
        self.assertEqual(-1, distance)

        distance = comparer.distance(long_string, None, max_distance_1)
        self.assertEqual(-1, distance)

        distance = comparer.distance(None, short_string, max_distance_1)
        self.assertEqual(-1, distance)

        distance = comparer.distance(None, long_string, max_distance_1)
        self.assertEqual(-1, distance)

        distance = comparer.distance(None, None, max_distance_1)
        self.assertEqual(0, distance)

        distance = comparer.distance(short_string, short_string,
                                     max_distance_1)
        self.assertEqual(0, distance)

        max_distance_2 = -1
        distance = comparer.distance(short_string, None, max_distance_2)
        self.assertEqual(-1, distance)

        distance = comparer.distance(long_string, None, max_distance_2)
        self.assertEqual(-1, distance)

        distance = comparer.distance(None, short_string, max_distance_2)
        self.assertEqual(-1, distance)

        distance = comparer.distance(None, long_string, max_distance_2)
        self.assertEqual(-1, distance)

        distance = comparer.distance(None, None, max_distance_2)
        self.assertEqual(0, distance)

        distance = comparer.distance(short_string, short_string,
                                     max_distance_2)
        self.assertEqual(0, distance)

    def test_levenshtein_very_long_string_2(self):
        max_distance = 5
        short_string = "string"
        very_long_string = "very_long_string"

        comparer = Levenshtein()
        distance = comparer.distance(short_string, very_long_string,
                                     max_distance)
        self.assertEqual(-1, distance)

    def test_damerau_osa_match_ref_max_0(self):
        max_distance = 0

        comparer = DamerauOsa()
        for s1 in self.test_strings:
            for s2 in self.test_strings:
                self.assertEqual(get_damerau_osa(s1, s2, max_distance),
                                 comparer.distance(s1, s2, max_distance))

    def test_damerau_osa_match_ref_max_1(self):
        max_distance = 1

        comparer = DamerauOsa()
        for s1 in self.test_strings:
            for s2 in self.test_strings:
                self.assertEqual(get_damerau_osa(s1, s2, max_distance),
                                 comparer.distance(s1, s2, max_distance))

    def test_damerau_osa_match_ref_max_3(self):
        max_distance = 3

        comparer = DamerauOsa()
        for s1 in self.test_strings:
            for s2 in self.test_strings:
                print(s1, s2)
                self.assertEqual(get_damerau_osa(s1, s2, max_distance),
                                 comparer.distance(s1, s2, max_distance))

    def test_damerau_osa_match_ref_max_huge(self):
        max_distance = sys.maxsize

        comparer = DamerauOsa()
        for s1 in self.test_strings:
            for s2 in self.test_strings:
                self.assertEqual(get_damerau_osa(s1, s2, max_distance),
                                 comparer.distance(s1, s2, max_distance))

    def test_damerau_osa_null_distance(self):
        max_distance = 10
        short_string = "string"
        long_string = "long_string"

        comparer = DamerauOsa()
        distance = comparer.distance(short_string, None, max_distance)
        self.assertEqual(len(short_string), distance)

        distance = comparer.distance(long_string, None, max_distance)
        self.assertEqual(-1, distance)

        distance = comparer.distance(None, short_string, max_distance)
        self.assertEqual(len(short_string), distance)

        distance = comparer.distance(None, long_string, max_distance)
        self.assertEqual(-1, distance)

        distance = comparer.distance(None, None, max_distance)
        self.assertEqual(0, distance)

    def test_damerau_osa_negative_max_distance(self):
        max_distance_1 = 0
        short_string = "string"
        long_string = "long_string"

        comparer = DamerauOsa()
        distance = comparer.distance(short_string, None, max_distance_1)
        self.assertEqual(-1, distance)

        distance = comparer.distance(long_string, None, max_distance_1)
        self.assertEqual(-1, distance)

        distance = comparer.distance(None, short_string, max_distance_1)
        self.assertEqual(-1, distance)

        distance = comparer.distance(None, long_string, max_distance_1)
        self.assertEqual(-1, distance)

        distance = comparer.distance(None, None, max_distance_1)
        self.assertEqual(0, distance)

        distance = comparer.distance(short_string, short_string,
                                     max_distance_1)
        self.assertEqual(0, distance)

        max_distance_2 = -1
        distance = comparer.distance(short_string, None, max_distance_2)
        self.assertEqual(-1, distance)

        distance = comparer.distance(long_string, None, max_distance_2)
        self.assertEqual(-1, distance)

        distance = comparer.distance(None, short_string, max_distance_2)
        self.assertEqual(-1, distance)

        distance = comparer.distance(None, long_string, max_distance_2)
        self.assertEqual(-1, distance)

        distance = comparer.distance(None, None, max_distance_2)
        self.assertEqual(0, distance)

        distance = comparer.distance(short_string, short_string,
                                     max_distance_2)
        self.assertEqual(0, distance)

    def test_damerau_osa_very_long_string_2(self):
        max_distance = 5
        short_string = "string"
        very_long_string = "very_long_string"

        comparer = DamerauOsa()
        distance = comparer.distance(short_string, very_long_string,
                                     max_distance)
        self.assertEqual(-1, distance)

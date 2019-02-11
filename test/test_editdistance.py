import unittest

import pytest

from symspellpy.editdistance import (AbstractDistanceComparer,
                                     DamerauOsa, DistanceAlgorithm,
                                     EditDistance)

class TestEditDistance(unittest.TestCase):
    def test_unknown_distance_algorithm(self):
        with pytest.raises(ValueError) as excinfo:
            __ = EditDistance(DistanceAlgorithm.LEVENSHTEIN)
        self.assertEqual("Unknown distance algorithm", str(excinfo.value))

    def test_abstract_distance_comparer(self):
        with pytest.raises(NotImplementedError) as excinfo:
            comparer = AbstractDistanceComparer()
            __ = comparer.distance("string_1", "string_2", 10)
        self.assertEqual("Should have implemented this", str(excinfo.value))

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

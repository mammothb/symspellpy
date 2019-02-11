import unittest

from symspellpy.helpers import to_similarity

class TestHelpers(unittest.TestCase):
    def test_to_similarity(self):
        distance_1 = 6.0
        length = 20.0

        self.assertAlmostEqual(0.7, to_similarity(distance_1, length))

        distance_2 = -1.0
        self.assertEqual(-1, to_similarity(distance_2, length))

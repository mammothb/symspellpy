import inspect
import unittest

from symspellpy.helpers import to_similarity

class TestHelpers(unittest.TestCase):
    def runTest(self):
        print('\nRunning %s' % self.__class__.__name__)
        self.test_to_similarity()

    def test_to_similarity(self):
        print('  - %s' % inspect.stack()[0][3])
        distance_1 = 6.0
        length = 20.0

        self.assertAlmostEqual(0.7, to_similarity(distance_1, length))

        distance_2 = -1.0
        self.assertEqual(-1, to_similarity(distance_2, length))

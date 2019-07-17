import unittest

from symspellpy.helpers import to_similarity,\
    transfer_casing_for_matching_text, transfer_casing_for_similar_text

class TestHelpers(unittest.TestCase):
    def test_to_similarity(self):
        distance_1 = 6.0
        length = 20.0

        self.assertAlmostEqual(0.7, to_similarity(distance_1, length))

        distance_2 = -1.0
        self.assertEqual(-1, to_similarity(distance_2, length))

    def test_transfer_casing_for_matching_text(self):
        text_w_casing = "Haw is the eeather in New York?"
        text_wo_casing = "how is the weather in new york?"
        # the text_wo_casing text with the casing transferred from
        # the text_w_casing text
        text_wo_casing_transferred = "How is the weather in New York?"

        self.assertEqual(text_wo_casing_transferred,
                         transfer_casing_for_matching_text(text_w_casing=
                                                           text_w_casing,
                                                           text_wo_casing=
                                                           text_wo_casing))

    def test_transfer_casing_for_similar_text(self):
        text_w_casing = "Haaw is the weeather in New York?"
        text_wo_casing = "how is the weather in new york?"
        # the text_wo_casing text with the casing transferred from
        # the text_w_casing text
        text_wo_casing_transferred = "How is the weather in New York?"

        self.assertEqual(text_wo_casing_transferred,
                         transfer_casing_for_similar_text(text_w_casing=
                                                          text_w_casing,
                                                          text_wo_casing=
                                                          text_wo_casing))

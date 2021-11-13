import unittest

import pytest

from symspellpy.helpers import (
    is_acronym,
    to_similarity,
    transfer_casing_for_matching_text,
    transfer_casing_for_similar_text,
)


class TestHelpers(unittest.TestCase):
    def test_to_similarity(self):
        distance_1 = 6.0
        length = 20.0

        self.assertAlmostEqual(0.7, to_similarity(distance_1, length))

        distance_2 = -1.0
        self.assertEqual(-1, to_similarity(distance_2, length))

    def test_is_acronym_default(self):
        self.assertTrue(is_acronym("ABCDE"))
        self.assertTrue(is_acronym("AB12E"))
        self.assertFalse(is_acronym("abcde"))
        self.assertFalse(is_acronym("ABCde"))
        self.assertFalse(is_acronym("abcDE"))
        self.assertFalse(is_acronym("abCDe"))
        self.assertFalse(is_acronym("abc12"))
        self.assertFalse(is_acronym("ab12e"))

    def test_is_acronym_any_terms_with_digits(self):
        self.assertTrue(is_acronym("ABCDE", True))
        self.assertTrue(is_acronym("AB12E", True))
        self.assertFalse(is_acronym("abcde", True))
        self.assertFalse(is_acronym("ABCde", True))
        self.assertFalse(is_acronym("abcDE", True))
        self.assertFalse(is_acronym("abCDe", True))
        self.assertTrue(is_acronym("abc12", True))
        self.assertTrue(is_acronym("ab12e", True))

    def test_transfer_casing_for_matching_text_diff_lengths(self):
        with pytest.raises(ValueError) as excinfo:
            transfer_casing_for_matching_text("abc", "abcd")
        self.assertEqual(
            "The 'text_w_casing' and 'text_wo_casing' "
            "don't have the same length, "
            "so you can't use them with this method, "
            "you should be using the more general "
            "transfer_casing_similar_text() method.",
            str(excinfo.value),
        )

    def test_transfer_casing_for_matching_text(self):
        text_w_casing = "Haw is the eeather in New York?"
        text_wo_casing = "how is the weather in new york?"
        # the text_wo_casing text with the casing transferred from
        # the text_w_casing text
        text_wo_casing_transferred = "How is the weather in New York?"

        self.assertEqual(
            text_wo_casing_transferred,
            transfer_casing_for_matching_text(
                text_w_casing=text_w_casing, text_wo_casing=text_wo_casing
            ),
        )

    def test_transfer_casing_for_similar_text_empty_wo_casing(self):
        text_w_casing = "Haaw is the weeather in New York?"
        text_wo_casing = ""

        self.assertEqual(
            text_wo_casing,
            transfer_casing_for_similar_text(
                text_w_casing=text_w_casing, text_wo_casing=text_wo_casing
            ),
        )

    def test_transfer_casing_for_similar_text_empty_w_casing(self):
        with pytest.raises(ValueError) as excinfo:
            transfer_casing_for_similar_text("", "abcd")
        self.assertEqual(
            "We need 'text_w_casing' to know what " "casing to transfer!",
            str(excinfo.value),
        )

    def test_transfer_casing_for_similar_text(self):
        text_w_casing = "Haaw is the weeather in New York?"
        text_wo_casing = "how is the weather in new york?"
        # the text_wo_casing text with the casing transferred from
        # the text_w_casing text
        text_wo_casing_transferred = "How is the weather in New York?"

        self.assertEqual(
            text_wo_casing_transferred,
            transfer_casing_for_similar_text(
                text_w_casing=text_w_casing, text_wo_casing=text_wo_casing
            ),
        )

        text_w_casing = "Wethr in New Yoork"
        text_wo_casing = "weather in new york"
        text_wo_casing_transferred = "Weather in New York"
        self.assertEqual(
            text_wo_casing_transferred,
            transfer_casing_for_similar_text(
                text_w_casing=text_w_casing, text_wo_casing=text_wo_casing
            ),
        )

        text_w_casing = "Efthr in New Yoork"
        text_wo_casing = "weather in new york"
        text_wo_casing_transferred = "WEather in New York"
        self.assertEqual(
            text_wo_casing_transferred,
            transfer_casing_for_similar_text(
                text_w_casing=text_w_casing, text_wo_casing=text_wo_casing
            ),
        )

        text_w_casing = "efthr in New Yoork"
        text_wo_casing = "weather in new york"
        text_wo_casing_transferred = "weather in New York"
        self.assertEqual(
            text_wo_casing_transferred,
            transfer_casing_for_similar_text(
                text_w_casing=text_w_casing, text_wo_casing=text_wo_casing
            ),
        )

        text_w_casing = "eTr in New Yoork"
        text_wo_casing = "weather in new york"
        text_wo_casing_transferred = "weaTHEr in New York"
        self.assertEqual(
            text_wo_casing_transferred,
            transfer_casing_for_similar_text(
                text_w_casing=text_w_casing, text_wo_casing=text_wo_casing
            ),
        )

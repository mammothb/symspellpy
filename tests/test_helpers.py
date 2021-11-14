import unittest

import pytest
from symspellpy.helpers import (
    is_acronym,
    to_similarity,
    transfer_casing_for_matching_text,
    transfer_casing_for_similar_text,
)


@pytest.fixture
def get_acronyms():
    return [
        ("ABCDE", {"default": True, "digits": True}),
        ("AB12E", {"default": True, "digits": True}),
        ("abcde", {"default": False, "digits": False}),
        ("ABCde", {"default": False, "digits": False}),
        ("abcDE", {"default": False, "digits": False}),
        ("abCDe", {"default": False, "digits": False}),
        ("abc12", {"default": False, "digits": True}),
        ("ab12e", {"default": False, "digits": True}),
    ]


@pytest.fixture
def get_similar_texts():
    return [
        (
            "Haaw is the weeather in New York?",
            "how is the weather in new york?",
            "How is the weather in New York?",
        ),
        ("Wethr in New Yoork", "weather in new york", "Weather in New York"),
        ("Efthr in New Yoork", "weather in new york", "WEather in New York"),
        ("efthr in New Yoork", "weather in new york", "weather in New York"),
        ("eTr in New Yoork", "weather in new york", "weaTHEr in New York"),
    ]


class TestHelpers:
    def test_to_similarity(self):
        length = 20.0

        assert pytest.approx(0.7) == to_similarity(6.0, length)
        assert -1 == to_similarity(-1.0, length)

    def test_is_acronym(self, get_acronyms):
        for word, expected in get_acronyms:
            assert expected["default"] == is_acronym(word)
            assert expected["digits"] == is_acronym(word, True)

    def test_transfer_casing_for_matching_text_diff_lengths(self):
        with pytest.raises(ValueError) as excinfo:
            transfer_casing_for_matching_text("abc", "abcd")
        assert (
            "The 'text_w_casing' and 'text_wo_casing' don't have the same "
            "length, so you can't use them with this method, you should be "
            "using the more general transfer_casing_similar_text() method."
        ) == str(excinfo.value)

    def test_transfer_casing_for_matching_text(self):
        text_w_casing = "Haw is the eeather in New York?"
        text_wo_casing = "how is the weather in new york?"

        # the text_wo_casing text with the casing transferred from
        # the text_w_casing text
        assert "How is the weather in New York?" == transfer_casing_for_matching_text(
            text_w_casing, text_wo_casing
        )

    def test_transfer_casing_for_similar_text_empty_wo_casing(self):
        text_w_casing = "Haw is the eeather in New York?"
        text_wo_casing = ""

        assert text_wo_casing == transfer_casing_for_similar_text(
            text_w_casing, text_wo_casing
        )

    def test_transfer_casing_for_similar_text_empty_w_casing(self):
        with pytest.raises(ValueError) as excinfo:
            transfer_casing_for_similar_text("", "abcd")
        assert "We need 'text_w_casing' to know what casing to transfer!" == str(
            excinfo.value
        )

    def test_transfer_casing_for_similar_text(self, get_similar_texts):
        for text_w_casing, text_wo_casing, expected in get_similar_texts:
            assert expected == transfer_casing_for_similar_text(
                text_w_casing, text_wo_casing
            )

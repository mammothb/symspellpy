import pytest

from symspellpy.helpers import (
    case_transfer_matching,
    case_transfer_similar,
    is_acronym,
    to_similarity,
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
        ("hoW eqr", "Haaaw er", "haaaW er"),
        ("hOW eqr", "Haaaw er", "hAAAW er"),
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

    def test_case_transfer_matching_diff_lengths(self):
        with pytest.raises(ValueError) as excinfo:
            case_transfer_matching("abc", "abcd")
        assert (
            "'cased_text' and 'uncased_text' don't have the same length, use "
            "case_transfer_similar() instead"
        ) == str(excinfo.value)

    def test_case_transfer_matching(self):
        cased_text = "Haw is the eeather in New York?"
        uncased_text = "how is the weather in new york?"

        # the uncased_text text with the casing transferred from
        # the cased_text text
        assert "How is the weather in New York?" == case_transfer_matching(
            cased_text, uncased_text
        )

    def test_case_transfer_similar_empty_wo_casing(self):
        cased_text = "Haw is the eeather in New York?"
        uncased_text = ""

        assert uncased_text == case_transfer_similar(cased_text, uncased_text)

    def test_case_transfer_similar_empty_w_casing(self):
        with pytest.raises(ValueError) as excinfo:
            case_transfer_similar("", "abcd")
        assert "'cased_text' cannot be empty" == str(excinfo.value)

    def test_case_transfer_similar(self, get_similar_texts):
        for cased_text, uncased_text, expected in get_similar_texts:
            assert expected == case_transfer_similar(cased_text, uncased_text)

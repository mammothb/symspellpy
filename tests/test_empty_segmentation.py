import pytest

from symspellpy import SymSpell
from symspellpy.composition import Composition


@pytest.mark.parametrize("phrase", ["", "-", "---", "\uff0d", "\ufe63"])
@pytest.mark.parametrize("word_length", [None, 10])
@pytest.mark.parametrize("with_dictionary", [False, True])
def test_empty_normalized_segmentation(
    phrase: str, word_length: int | None, with_dictionary: bool
):
    sym_spell = SymSpell()
    if with_dictionary:
        sym_spell.create_dictionary_entry("hello", 10)

    assert (
        sym_spell.word_segmentation(phrase, max_segmentation_word_length=word_length)
        == Composition()
    )

    if with_dictionary:
        assert sym_spell.word_segmentation("hello").corrected_string == "hello"

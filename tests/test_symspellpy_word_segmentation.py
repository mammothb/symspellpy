import pytest

from symspellpy import SymSpell


@pytest.fixture
def symspell_edit_distance_load(dictionary_path, request):
    sym_spell = SymSpell(request.param)
    sym_spell.load_dictionary(dictionary_path, 0, 1)
    return sym_spell, request.param


class TestSymSpellPyWordSegmentation:
    @pytest.mark.parametrize("symspell_default_load", ["unigram"], indirect=True)
    def test_word_segmentation_ignore_token(self, symspell_default_load):
        sym_spell, _ = symspell_default_load
        typo = "24th december"
        result = sym_spell.word_segmentation(typo, ignore_token=r"\d{2}\w*\b")
        assert typo == result.corrected_string

    @pytest.mark.parametrize(
        "symspell_edit_distance_load, get_fortests_data, with_arguments, capitalize",
        [
            (0, "word_segmentation_data.json", False, False),
            (0, "word_segmentation_data.json", True, False),
            (0, "word_segmentation_data.json", False, True),
        ],
        indirect=["symspell_edit_distance_load", "get_fortests_data"],
    )
    def test_word_segmentation(
        self,
        symspell_edit_distance_load,
        get_fortests_data,
        with_arguments,
        capitalize,
    ):
        sym_spell, edit_distance = symspell_edit_distance_load
        for entry in get_fortests_data:
            if capitalize:
                typo = entry["typo"].capitalize()
                correction = entry[str(edit_distance)]["term"].capitalize()
            else:
                typo = entry["typo"]
                correction = entry[str(edit_distance)]["term"]
            if with_arguments:
                result = sym_spell.word_segmentation(typo, edit_distance, 11)
            else:
                result = sym_spell.word_segmentation(typo)
            assert correction == result.corrected_string

    @pytest.mark.parametrize("symspell_edit_distance_load", [0], indirect=True)
    def test_word_segmentation_apostrophe(self, symspell_edit_distance_load):
        sym_spell, _ = symspell_edit_distance_load

        typo = "There'resomewords"
        correction = "There' re some words"
        result = sym_spell.word_segmentation(typo)
        assert correction == result[1]

    @pytest.mark.parametrize("symspell_edit_distance_load", [0], indirect=True)
    def test_word_segmentation_ligature(self, symspell_edit_distance_load):
        sym_spell, _ = symspell_edit_distance_load

        typo = "Therearesomescientiﬁcwords"
        correction = "There are some scientific words"
        result = sym_spell.word_segmentation(typo)
        assert correction == result[1]

import pytest

from symspellpy import Verbosity

ENTRIES = ["baked", "ax", "lake", "", "slaked"]


class TestSymSpellPyEdgeCases:
    @pytest.mark.parametrize("symspell_long_entry", [ENTRIES], indirect=True)
    def test_empty_string_has_all_short_deletes(self, symspell_long_entry):
        sym_spell, entries = symspell_long_entry

        assert len(entries[:-1]) == len(sym_spell.deletes[""])
        assert all(entry in sym_spell.deletes[""] for entry in entries[:-1])
        assert "abc" not in sym_spell.deletes[""]

    def test_split_correction_part_of_single_term_correction(self, symspell_default):
        symspell_default.create_dictionary_entry("where", 2)
        symspell_default.create_dictionary_entry("is", 2)
        symspell_default.create_dictionary_entry("whereas", 2)
        symspell_default._bigrams["where is"] = 10

        suggestions = symspell_default.lookup_compound("whereiz", 2)
        assert "where is" == suggestions[0].term
        assert 2 == suggestions[0].distance
        assert 10 == suggestions[0].count

    @pytest.mark.parametrize("symspell_long_entry", [["bank", "bink"]], indirect=True)
    def test_no_common_char_with_phrase(self, symspell_long_entry):
        sym_spell, _ = symspell_long_entry
        results = sym_spell.lookup("knab", Verbosity.ALL, 4)

        assert 2 == len(results)
        assert "bank" == results[0].term
        assert 3 == results[0].distance
        assert "bink" == results[1].term
        assert 4 == results[1].distance

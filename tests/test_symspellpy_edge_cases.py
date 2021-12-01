import pytest

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

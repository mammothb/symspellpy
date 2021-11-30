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

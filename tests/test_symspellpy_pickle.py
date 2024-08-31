import os
import pickle
from unittest import TestCase

import pytest

from symspellpy import SymSpell


class TestSymSpellPyPickle:
    @pytest.mark.parametrize(
        "symspell_default_load, is_compressed",
        [("unigram", True), ("bigram", True), ("unigram", False), ("bigram", False)],
        indirect=["symspell_default_load"],
    )
    def test_pickle(self, pickle_path, symspell_default_load, is_compressed):
        sym_spell, _ = symspell_default_load
        sym_spell.save_pickle(pickle_path, is_compressed)

        sym_spell_2 = SymSpell(123, 456, 789)

        assert sym_spell._count_threshold != sym_spell_2._count_threshold
        assert (
            sym_spell._max_dictionary_edit_distance
            != sym_spell_2._max_dictionary_edit_distance
        )
        assert sym_spell._prefix_length != sym_spell_2._prefix_length

        with TestCase.assertLogs("symspellpy.symspellpy.logger", level="WARNING") as cm:
            sym_spell_2.load_pickle(pickle_path, is_compressed)
        assert (
            "Loading data which was created using different ('count_threshold', "
            "'max_dictionary_edit_distance', 'prefix_length') settings. Overwriting "
            "current SymSpell instance with loaded settings ..."
        ) == cm.records[0].getMessage()
        assert sym_spell.below_threshold_words == sym_spell_2.below_threshold_words
        assert sym_spell.bigrams == sym_spell_2.bigrams
        assert sym_spell.deletes == sym_spell_2.deletes
        assert sym_spell.words == sym_spell_2.words
        assert sym_spell._max_length == sym_spell_2._max_length
        assert sym_spell._count_threshold == sym_spell_2._count_threshold
        assert (
            sym_spell._max_dictionary_edit_distance
            == sym_spell_2._max_dictionary_edit_distance
        )
        assert sym_spell._prefix_length == sym_spell_2._prefix_length
        os.remove(pickle_path)

    @pytest.mark.parametrize(
        "symspell_default_load, is_compressed",
        [("unigram", True), ("bigram", True), ("unigram", False), ("bigram", False)],
        indirect=["symspell_default_load"],
    )
    def test_pickle_same_settings(
        self, pickle_path, symspell_default_load, is_compressed
    ):
        sym_spell, _ = symspell_default_load
        sym_spell.save_pickle(pickle_path, is_compressed)

        sym_spell_2 = SymSpell()
        sym_spell_2.load_pickle(pickle_path, is_compressed)

        assert sym_spell.below_threshold_words == sym_spell_2.below_threshold_words
        assert sym_spell.bigrams == sym_spell_2.bigrams
        assert sym_spell.deletes == sym_spell_2.deletes
        assert sym_spell.words == sym_spell_2.words
        assert sym_spell._max_length == sym_spell_2._max_length
        assert sym_spell._count_threshold == sym_spell_2._count_threshold
        assert (
            sym_spell._max_dictionary_edit_distance
            == sym_spell_2._max_dictionary_edit_distance
        )
        assert sym_spell._prefix_length == sym_spell_2._prefix_length
        os.remove(pickle_path)

    @pytest.mark.parametrize(
        "symspell_default_load", ["unigram", "bigram"], indirect=True
    )
    def test_pickle_bytes(self, symspell_default_load):
        sym_spell, _ = symspell_default_load
        sym_spell_2 = SymSpell(123, 456, 789)

        assert sym_spell._count_threshold != sym_spell_2._count_threshold
        assert (
            sym_spell._max_dictionary_edit_distance
            != sym_spell_2._max_dictionary_edit_distance
        )
        assert sym_spell._prefix_length != sym_spell_2._prefix_length

        with TestCase.assertLogs("symspellpy.symspellpy.logger", level="WARNING") as cm:
            sym_spell_2.load_pickle(
                sym_spell.save_pickle(to_bytes=True), from_bytes=True
            )
        assert (
            "Loading data which was created using different ('count_threshold', "
            "'max_dictionary_edit_distance', 'prefix_length') settings. Overwriting "
            "current SymSpell instance with loaded settings ..."
        ) == cm.records[0].getMessage()
        assert sym_spell.below_threshold_words == sym_spell_2.below_threshold_words
        assert sym_spell.bigrams == sym_spell_2.bigrams
        assert sym_spell.deletes == sym_spell_2.deletes
        assert sym_spell.words == sym_spell_2.words
        assert sym_spell._max_length == sym_spell_2._max_length
        assert sym_spell._count_threshold == sym_spell_2._count_threshold
        assert (
            sym_spell._max_dictionary_edit_distance
            == sym_spell_2._max_dictionary_edit_distance
        )
        assert sym_spell._prefix_length == sym_spell_2._prefix_length

    def test_pickle_invalid(self, pickle_path, symspell_default):
        pickle_data = {"deletes": {}, "words": {}, "max_length": 0, "data_version": -1}
        with open(pickle_path, "wb") as f:
            pickle.dump(pickle_data, f)
        assert not symspell_default.load_pickle(pickle_path, False)
        os.remove(pickle_path)

        pickle_data = {"deletes": {}, "words": {}, "max_length": 0}
        with open(pickle_path, "wb") as f:
            pickle.dump(pickle_data, f)
        assert not symspell_default.load_pickle(pickle_path, False)
        os.remove(pickle_path)

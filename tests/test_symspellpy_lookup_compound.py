import pytest


class TestSymSpellPyLookupCompound:
    @pytest.mark.parametrize(
        "symspell_default_load, get_fortests_data",
        [
            ("bigram", "lookup_compound_data.json"),
            ("unigram", "lookup_compound_data.json"),
        ],
        indirect=True,
    )
    def test_lookup_compound(self, symspell_default_load, get_fortests_data):
        sym_spell, dictionary = symspell_default_load
        for entry in get_fortests_data:
            results = sym_spell.lookup_compound(entry["typo"], 2)
            assert entry[dictionary]["num_results"] == len(results)
            assert entry[dictionary]["term"] == results[0].term
            assert entry[dictionary]["distance"] == results[0].distance
            assert entry[dictionary]["count"] == results[0].count

    @pytest.mark.parametrize(
        "symspell_default_entry", [[("steam", 1), ("machine", 1)]], indirect=True
    )
    def test_lookup_compound_only_combi(self, symspell_default_entry):
        typo = "ste am machie"
        correction = "steam machine"
        results = symspell_default_entry.lookup_compound(typo, 2)
        assert 1 == len(results)
        assert correction == results[0].term

    @pytest.mark.parametrize(
        "symspell_default_entry", [[("steam", 1), ("machine", 1)]], indirect=True
    )
    def test_lookup_compound_no_suggestion(self, symspell_default_entry):
        typo = "qwer erty ytui a"
        results = symspell_default_entry.lookup_compound(typo, 2)
        assert 1 == len(results)
        assert typo == results[0].term

    @pytest.mark.parametrize(
        "symspell_default_load, get_fortests_data",
        [
            ("bigram", "lookup_compound_replaced_words_data.json"),
            ("unigram", "lookup_compound_replaced_words_data.json"),
        ],
        indirect=True,
    )
    def test_lookup_compound_replaced_words(
        self, symspell_default_load, get_fortests_data
    ):
        sym_spell, dictionary = symspell_default_load
        num_replaced_words = 0
        for entry in get_fortests_data:
            num_replaced_words += len(entry[dictionary]["replacement"])
            results = sym_spell.lookup_compound(entry["typo"], 2)
            assert num_replaced_words == len(sym_spell.replaced_words)
            assert entry[dictionary]["term"] == results[0].term
            for k, v in entry[dictionary]["replacement"].items():
                assert v == sym_spell.replaced_words[k].term

    @pytest.mark.parametrize(
        "symspell_default_load, get_fortests_data",
        [
            ("bigram", "lookup_compound_ignore_non_words_data.json"),
            ("unigram", "lookup_compound_ignore_non_words_data.json"),
        ],
        indirect=True,
    )
    def test_lookup_compound_ignore_non_words(
        self, symspell_default_load, get_fortests_data
    ):
        sym_spell, dictionary = symspell_default_load
        for entry in get_fortests_data:
            results = sym_spell.lookup_compound(entry["typo"], 2, True)
            assert 1 == len(results)
            assert entry[dictionary]["term"] == results[0].term

    @pytest.mark.parametrize(
        "symspell_default_load", ["bigram", "unigram"], indirect=True
    )
    def test_lookup_compound_ignore_non_words_ignore_digits(
        self, symspell_default_load
    ):
        sym_spell, _ = symspell_default_load

        typo = "is the officeon 1st floor oepn 24/7"
        correction = "is the office on 1st floor open 24/7"
        results = sym_spell.lookup_compound(
            typo,
            2,
            True,
            split_by_space=True,
            ignore_term_with_digits=True,
        )
        assert 1 == len(results)
        assert correction == results[0].term
        assert 2 == results[0].distance
        assert 0 == results[0].count

    @pytest.mark.parametrize(
        "symspell_default_load, get_fortests_data",
        [
            ("bigram", "lookup_compound_transfer_casing_data.json"),
            ("unigram", "lookup_compound_transfer_casing_data.json"),
        ],
        indirect=True,
    )
    def test_lookup_compound_transfer_casing(
        self, symspell_default_load, get_fortests_data
    ):
        sym_spell, dictionary = symspell_default_load
        for entry in get_fortests_data:
            results = sym_spell.lookup_compound(entry["typo"], 2, transfer_casing=True)
            assert entry[dictionary]["term"] == results[0].term

    @pytest.mark.parametrize(
        "symspell_default_load, get_fortests_data",
        [
            ("bigram", "lookup_compound_transfer_casing_ignore_nonwords_data.json"),
            ("unigram", "lookup_compound_transfer_casing_ignore_nonwords_data.json"),
        ],
        indirect=True,
    )
    def test_lookup_compound_transfer_casing_ignore_nonwords(
        self, symspell_default_load, get_fortests_data
    ):
        sym_spell, dictionary = symspell_default_load
        for entry in get_fortests_data:
            results = sym_spell.lookup_compound(entry["typo"], 2, True, True)
            assert entry[dictionary]["term"] == results[0].term

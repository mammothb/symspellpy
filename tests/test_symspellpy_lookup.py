import sys

import pytest

from symspellpy import SymSpell, Verbosity


@pytest.fixture
def symspell_high_thres():
    return SymSpell(2, 7, 10)


@pytest.fixture
def symspell_high_thres_flame(symspell_high_thres):
    symspell_high_thres.create_dictionary_entry("flame", 20)
    symspell_high_thres.create_dictionary_entry("flam", 1)
    return symspell_high_thres


class TestSymSpellPyLookup:
    @pytest.mark.parametrize(
        "symspell_default_entry",
        [[("steama", 4), ("steamb", 6), ("steamc", 2)]],
        indirect=True,
    )
    def test_deletes(self, symspell_default_entry):
        result = symspell_default_entry.lookup("stream", Verbosity.TOP, 2)
        assert 1 == len(result)
        assert "steamb" == result[0].term
        assert 6 == result[0].count
        assert symspell_default_entry.deletes

    @pytest.mark.parametrize("symspell_short", [None], indirect=True)
    def test_words_with_shared_prefix_should_retain_counts(self, symspell_short):
        symspell_short.create_dictionary_entry("pipe", 5)
        symspell_short.create_dictionary_entry("pips", 10)

        result = symspell_short.lookup("pipe", Verbosity.ALL, 1)
        assert 2 == len(result)
        assert "pipe" == result[0].term
        assert 5 == result[0].count
        assert "pips" == result[1].term
        assert 10 == result[1].count

        result = symspell_short.lookup("pips", Verbosity.ALL, 1)
        assert 2 == len(result)
        assert "pips" == result[0].term
        assert 10 == result[0].count
        assert "pipe" == result[1].term
        assert 5 == result[1].count

        result = symspell_short.lookup("pip", Verbosity.ALL, 1)
        assert 2 == len(result)
        assert "pips" == result[0].term
        assert 10 == result[0].count
        assert "pipe" == result[1].term
        assert 5 == result[1].count

    def test_add_additional_counts_should_not_overflow(
        self, symspell_default, get_same_word_and_count
    ):
        for i, (word, count) in enumerate(get_same_word_and_count):
            symspell_default.create_dictionary_entry(
                word, sys.maxsize - 1 if i == 0 else count
            )
            result = symspell_default.lookup(word, Verbosity.TOP)
            assert (sys.maxsize - 1 if i == 0 else sys.maxsize) == result[0].count

    @pytest.mark.parametrize(
        "verbosity, num_results",
        [(Verbosity.TOP, 1), (Verbosity.CLOSEST, 2), (Verbosity.ALL, 3)],
    )
    def test_verbosity_should_control_lookup_results(
        self, symspell_default, verbosity, num_results
    ):
        symspell_default.create_dictionary_entry("steam", 1)
        symspell_default.create_dictionary_entry("steams", 2)
        symspell_default.create_dictionary_entry("steem", 3)

        result = symspell_default.lookup("steems", verbosity, 2)
        assert num_results == len(result)

    @pytest.mark.parametrize(
        "symspell_default_entry",
        [[("steama", 4), ("steamb", 6), ("steamc", 2)]],
        indirect=True,
    )
    def test_should_return_most_frequent(self, symspell_default_entry):
        result = symspell_default_entry.lookup("stream", Verbosity.TOP, 2)
        assert 1 == len(result)
        assert "steamb" == result[0].term
        assert 6 == result[0].count

    @pytest.mark.parametrize(
        "symspell_default_entry",
        [[("steama", 4), ("steamb", 6), ("steamc", 2)]],
        indirect=True,
    )
    def test_should_find_exact_match(self, symspell_default_entry):
        result = symspell_default_entry.lookup("streama", Verbosity.TOP, 2)
        assert 1 == len(result)
        assert "steama" == result[0].term

    @pytest.mark.parametrize("term", ["paw", "awn"])
    def test_should_not_return_non_word_delete(self, symspell_high_thres, term):
        symspell_high_thres.create_dictionary_entry("pawn", 10)
        result = symspell_high_thres.lookup(term, Verbosity.TOP, 0)
        assert not result

    def test_should_not_return_low_count_word(self, symspell_high_thres):
        symspell_high_thres.create_dictionary_entry("pawn", 1)
        result = symspell_high_thres.lookup("pawn", Verbosity.TOP, 0)
        assert not result

    def test_should_not_return_low_count_word_that_are_also_delete_word(
        self, symspell_high_thres_flame
    ):
        result = symspell_high_thres_flame.lookup("flam", Verbosity.TOP, 0)
        assert not result

    def test_max_edit_distance_too_large(self, symspell_high_thres_flame):
        with pytest.raises(ValueError) as excinfo:
            _ = symspell_high_thres_flame.lookup("flam", Verbosity.TOP, 3)
        assert "distance too large" == str(excinfo.value)

    def test_include_unknown(self, symspell_high_thres_flame):
        result = symspell_high_thres_flame.lookup("flam", Verbosity.TOP, 0, True)
        assert 1 == len(result)
        assert "flam" == result[0].term

    def test_avoid_exact_match_early_exit(self, symspell_high_thres_flame):
        result = symspell_high_thres_flame.lookup(
            "24th", Verbosity.ALL, 2, ignore_token=r"\d{2}\w*\b"
        )
        assert 1 == len(result)
        assert "24th" == result[0].term

    def test_should_replicate_noisy_results(
        self, dictionary_path, query_path, symspell_default
    ):
        symspell_default.load_dictionary(dictionary_path, 0, 1)

        with open(query_path, "r") as infile:
            test_phrases = [
                parts[0]
                for parts in map(lambda x: x.strip().split(), infile.readlines())
                if len(parts) >= 2
            ]

        result_sum = 0
        for phrase in test_phrases:
            result_sum += len(symspell_default.lookup(phrase, Verbosity.CLOSEST, 2))

        assert 4955 == result_sum

    @pytest.mark.parametrize(
        "symspell_default_entry, typo, correction",
        [
            ([("steam", 4)], "Stream", "Steam"),
            ([("steam", 4)], "StreaM", "SteaM"),
            ([("steam", 4)], "STREAM", "STEAM"),
            ([("i", 4)], "I", "I"),
        ],
        indirect=["symspell_default_entry"],
    )
    def test_transfer_casing(self, symspell_default_entry, typo, correction):
        result = symspell_default_entry.lookup(
            typo, Verbosity.TOP, 2, transfer_casing=True
        )
        assert correction == result[0].term

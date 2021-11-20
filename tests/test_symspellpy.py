import json
import os
import pickle
import sys
from pathlib import Path

import pkg_resources
import pytest

from symspellpy import SymSpell, Verbosity
from symspellpy.helpers import DictIO
from symspellpy.symspellpy import SuggestItem

FORTESTS_DIR = Path(__file__).resolve().parent / "fortests"
BAD_DICT_PATH = FORTESTS_DIR / "bad_dict.txt"
BIG_MODIFIED_PATH = FORTESTS_DIR / "big_modified.txt"
BIG_WORDS_PATH = FORTESTS_DIR / "big_words.txt"
NON_EN_DICT_PATH = FORTESTS_DIR / "non_en_dict.txt"
PICKLE_PATH = FORTESTS_DIR / "dictionary.pickle"
QUERY_PATH = FORTESTS_DIR / "noisy_query_en_1000.txt"
SEPARATOR_DICT_PATH = FORTESTS_DIR / "separator_dict.txt"

DICTIONARY_PATH = pkg_resources.resource_filename(
    "symspellpy", "frequency_dictionary_en_82_765.txt"
)
BIGRAM_PATH = pkg_resources.resource_filename(
    "symspellpy", "frequency_bigramdictionary_en_243_342.txt"
)
INVALID_PATH = "invalid/dictionary/path.txt"
SEPARATOR = "$"


@pytest.fixture
def get_dictionary_stream(request):
    dictionary = {
        "the": 23135851162,
        "of": 13151942776,
        "abcs of": 10956800,
        "aaron and": 10721728,
        "and": 12997637966,
    }
    if request.param is None:
        dict_stream = DictIO(dictionary)
    else:
        dict_stream = DictIO(dictionary, request.param)
    yield dict_stream, request.param


@pytest.fixture
def get_lookup_compound_data(request):
    with open(FORTESTS_DIR / request.param) as infile:
        return json.load(infile)["data"]


@pytest.fixture
def get_same_word_and_count():
    word = "hello"
    return [(word, 11), (word, 3)]


@pytest.fixture
def symspell_default():
    return SymSpell()


@pytest.fixture
def symspell_default_entry(symspell_default, request):
    for entry in request.param:
        symspell_default.create_dictionary_entry(entry[0], entry[1])
    return symspell_default


@pytest.fixture
def symspell_default_load(symspell_default, request):
    symspell_default.load_dictionary(DICTIONARY_PATH, 0, 1)
    if request.param == "bigram":
        symspell_default.load_bigram_dictionary(BIGRAM_PATH, 0, 2)
    return symspell_default, request.param


@pytest.fixture
def symspell_edit_distance_load(request):
    sym_spell = SymSpell(request.param)
    sym_spell.load_dictionary(DICTIONARY_PATH, 0, 1)
    return sym_spell, request.param


@pytest.fixture
def symspell_high_thres():
    return SymSpell(2, 7, 10)


@pytest.fixture
def symspell_high_thres_flame(symspell_high_thres):
    symspell_high_thres.create_dictionary_entry("flame", 20)
    symspell_high_thres.create_dictionary_entry("flam", 1)
    return symspell_high_thres


@pytest.fixture
def symspell_short(request):
    if request.param is None:
        return SymSpell(1, 3)
    return SymSpell(1, 3, count_threshold=request.param)


class TestSymSpellPy:
    def test_negative_max_dictionary_edit_distance(self):
        with pytest.raises(ValueError) as excinfo:
            _ = SymSpell(-1, 3)
        assert "max_dictionary_edit_distance cannot be negative" == str(excinfo.value)

    def test_invalid_prefix_length(self):
        # prefix_length < 1
        with pytest.raises(ValueError) as excinfo:
            _ = SymSpell(1, 0)
        assert "prefix_length cannot be less than 1" == str(excinfo.value)

        with pytest.raises(ValueError) as excinfo:
            _ = SymSpell(1, -1)
        assert "prefix_length cannot be less than 1" == str(excinfo.value)

        # prefix_length <= max_dictionary_edit_distance
        with pytest.raises(ValueError) as excinfo:
            _ = SymSpell(2, 2)
        assert "prefix_length must be greater than max_dictionary_edit_distance" == str(
            excinfo.value
        )

    def test_negative_count_threshold(self):
        with pytest.raises(ValueError) as excinfo:
            _ = SymSpell(1, 3, -1)
        assert "count_threshold cannot be negative" == str(excinfo.value)

    @pytest.mark.parametrize("symspell_short", [None, 0], indirect=True)
    def test_create_dictionary_entry_negative_count(self, symspell_short):
        assert (
            symspell_short._count_threshold == 0
        ) == symspell_short.create_dictionary_entry("pipe", 0)
        assert not symspell_short.create_dictionary_entry("pipe", -1)

    @pytest.mark.parametrize("symspell_short", [10], indirect=True)
    def test_create_dictionary_entry_below_threshold(self, symspell_short):
        symspell_short.create_dictionary_entry("pipe", 4)
        assert 1 == len(symspell_short.below_threshold_words)
        assert 4 == symspell_short.below_threshold_words["pipe"]

        symspell_short.create_dictionary_entry("pipe", 4)
        assert 1 == len(symspell_short.below_threshold_words)
        assert 8 == symspell_short.below_threshold_words["pipe"]

        symspell_short.create_dictionary_entry("pipe", 4)
        assert 0 == len(symspell_short.below_threshold_words)

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

    def test_add_additional_counts_should_not_add_word_again(
        self, symspell_default, get_same_word_and_count
    ):
        for word, count in get_same_word_and_count:
            symspell_default.create_dictionary_entry(word, count)
            assert 1 == symspell_default.word_count

    def test_add_additional_counts_should_increase_count(
        self, symspell_default, get_same_word_and_count
    ):
        expected_count = 0
        for word, count in get_same_word_and_count:
            expected_count += count
            symspell_default.create_dictionary_entry(word, count)
            result = symspell_default.lookup(word, Verbosity.TOP)
            assert expected_count == result[0].count

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
    def test_lookup_should_return_most_frequent(self, symspell_default_entry):
        result = symspell_default_entry.lookup("stream", Verbosity.TOP, 2)
        assert 1 == len(result)
        assert "steamb" == result[0].term
        assert 6 == result[0].count

    @pytest.mark.parametrize(
        "symspell_default_entry",
        [[("steama", 4), ("steamb", 6), ("steamc", 2)]],
        indirect=True,
    )
    def test_lookup_should_find_exact_match(self, symspell_default_entry):
        result = symspell_default_entry.lookup("streama", Verbosity.TOP, 2)
        assert 1 == len(result)
        assert "steama" == result[0].term

    @pytest.mark.parametrize("term", ["paw", "awn"])
    def test_lookup_should_not_return_non_word_delete(self, symspell_high_thres, term):
        symspell_high_thres.create_dictionary_entry("pawn", 10)
        result = symspell_high_thres.lookup(term, Verbosity.TOP, 0)
        assert not result

    def test_lookup_should_not_return_low_count_word(self, symspell_high_thres):
        symspell_high_thres.create_dictionary_entry("pawn", 1)
        result = symspell_high_thres.lookup("pawn", Verbosity.TOP, 0)
        assert not result

    def test_lookup_should_not_return_low_count_word_that_are_also_delete_word(
        self, symspell_high_thres_flame
    ):
        result = symspell_high_thres_flame.lookup("flam", Verbosity.TOP, 0)
        assert not result

    def test_lookup_max_edit_distance_too_large(self, symspell_high_thres_flame):
        with pytest.raises(ValueError) as excinfo:
            _ = symspell_high_thres_flame.lookup("flam", Verbosity.TOP, 3)
        assert "Distance too large" == str(excinfo.value)

    def test_lookup_include_unknown(self, symspell_high_thres_flame):
        result = symspell_high_thres_flame.lookup("flam", Verbosity.TOP, 0, True)
        assert 1 == len(result)
        assert "flam" == result[0].term

    def test_lookup_avoid_exact_match_early_exit(self, symspell_high_thres_flame):
        result = symspell_high_thres_flame.lookup(
            "24th", Verbosity.ALL, 2, ignore_token=r"\d{2}\w*\b"
        )
        assert 1 == len(result)
        assert "24th" == result[0].term

    def test_load_bigram_dictionary_invalid_path(self, symspell_default):
        assert not symspell_default.load_bigram_dictionary(INVALID_PATH, 0, 2)

    def test_loading_dictionary_from_fileobject(self, symspell_default):
        with open(BIG_WORDS_PATH, "r", encoding="utf8") as infile:
            assert symspell_default.create_dictionary(infile)

    def test_load_bigram_dictionary_bad_dict(self, symspell_default):
        assert symspell_default.load_bigram_dictionary(BAD_DICT_PATH, 0, 2)
        assert 2 == len(symspell_default.bigrams)
        assert 12 == symspell_default.bigrams["rtyu tyui"]
        assert 13 == symspell_default.bigrams["yuio uiop"]

    def test_load_bigram_dictionary_separator(self, symspell_default):
        assert symspell_default.load_bigram_dictionary(
            SEPARATOR_DICT_PATH, 0, 1, SEPARATOR
        )
        assert 5 == len(symspell_default.bigrams)
        assert 23135851162 == symspell_default.bigrams["the"]
        assert 13151942776 == symspell_default.bigrams["of"]
        assert 10956800 == symspell_default.bigrams["abcs of"]
        assert 10721728, symspell_default.bigrams["aaron and"]
        assert 12997637966 == symspell_default.bigrams["and"]

    @pytest.mark.parametrize("get_dictionary_stream", [None], indirect=True)
    def test_load_bigram_dictionary_stream(
        self, symspell_default, get_dictionary_stream
    ):
        dict_stream, _ = get_dictionary_stream
        assert symspell_default.load_bigram_dictionary_stream(dict_stream, 0, 2)
        assert 2 == len(symspell_default.bigrams)
        assert 10956800 == symspell_default.bigrams["abcs of"]
        assert 10721728 == symspell_default.bigrams["aaron and"]

    @pytest.mark.parametrize("get_dictionary_stream", [SEPARATOR], indirect=True)
    def test_load_bigram_dictionary_stream_separator(
        self, symspell_default, get_dictionary_stream
    ):
        dict_stream, separator = get_dictionary_stream
        assert symspell_default.load_bigram_dictionary_stream(
            dict_stream, 0, 1, separator
        )
        assert 5 == len(symspell_default.bigrams)
        assert 23135851162 == symspell_default.bigrams["the"]
        assert 13151942776 == symspell_default.bigrams["of"]
        assert 10956800 == symspell_default.bigrams["abcs of"]
        assert 10721728 == symspell_default.bigrams["aaron and"]
        assert 12997637966 == symspell_default.bigrams["and"]

    def test_load_dictionary_invalid_path(self, symspell_default):
        assert not symspell_default.load_dictionary(INVALID_PATH, 0, 1)

    def test_load_dictionary_bad_dictionary(self, symspell_default):
        assert symspell_default.load_dictionary(BAD_DICT_PATH, 0, 1)
        assert 2 == symspell_default.word_count
        assert 10 == symspell_default.words["asdf"]
        assert 12 == symspell_default.words["sdfg"]

    def test_load_dictionary_separator(self, symspell_default):
        assert symspell_default.load_dictionary(SEPARATOR_DICT_PATH, 0, 1, SEPARATOR)
        assert 5 == symspell_default.word_count
        assert 23135851162 == symspell_default.words["the"]
        assert 13151942776 == symspell_default.words["of"]
        assert 10956800 == symspell_default.words["abcs of"]
        assert 10721728 == symspell_default.words["aaron and"]
        assert 12997637966 == symspell_default.words["and"]

    @pytest.mark.parametrize("get_dictionary_stream", [None], indirect=True)
    def test_load_dictionary_stream(self, symspell_default, get_dictionary_stream):
        # keys with space in them don't get parsed properly when using
        # the default separator=" "
        dict_stream, _ = get_dictionary_stream
        assert symspell_default.load_dictionary_stream(dict_stream, 0, 1)
        assert 3 == symspell_default.word_count
        assert 23135851162 == symspell_default.words["the"]
        assert 13151942776 == symspell_default.words["of"]
        assert 12997637966 == symspell_default.words["and"]

    @pytest.mark.parametrize("get_dictionary_stream", [SEPARATOR], indirect=True)
    def test_load_dictionary_stream_separator(
        self, symspell_default, get_dictionary_stream
    ):
        dict_stream, separator = get_dictionary_stream
        assert symspell_default.load_dictionary_stream(dict_stream, 0, 1, separator)
        assert 5 == symspell_default.word_count
        assert 23135851162 == symspell_default.words["the"]
        assert 13151942776 == symspell_default.words["of"]
        assert 10956800 == symspell_default.words["abcs of"]
        assert 10721728 == symspell_default.words["aaron and"]
        assert 12997637966 == symspell_default.words["and"]

    def test_lookup_should_replicate_noisy_results(self, symspell_default):
        symspell_default.load_dictionary(DICTIONARY_PATH, 0, 1)

        with open(QUERY_PATH, "r") as infile:
            test_phrases = [
                parts[0]
                for parts in map(lambda x: x.strip().split(), infile.readlines())
                if len(parts) >= 2
            ]

        result_sum = 0
        for phrase in test_phrases:
            result_sum += len(symspell_default.lookup(phrase, Verbosity.CLOSEST, 2))
        assert 4945 == result_sum

    @pytest.mark.parametrize(
        "symspell_default_load, get_lookup_compound_data",
        [
            ("bigram", "lookup_compound_data.json"),
            ("unigram", "lookup_compound_data.json"),
        ],
        indirect=True,
    )
    def test_lookup_compound(self, symspell_default_load, get_lookup_compound_data):
        sym_spell, dictionary = symspell_default_load
        for entry in get_lookup_compound_data:
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
        "symspell_default_load, get_lookup_compound_data",
        [
            ("bigram", "lookup_compound_replaced_words_data.json"),
            ("unigram", "lookup_compound_replaced_words_data.json"),
        ],
        indirect=True,
    )
    def test_lookup_compound_replaced_words(
        self, symspell_default_load, get_lookup_compound_data
    ):
        sym_spell, dictionary = symspell_default_load
        num_replaced_words = 0
        for entry in get_lookup_compound_data:
            num_replaced_words += len(entry[dictionary]["replacement"])
            results = sym_spell.lookup_compound(entry["typo"], 2)
            assert num_replaced_words == len(sym_spell.replaced_words)
            assert entry[dictionary]["term"] == results[0].term
            for k, v in entry[dictionary]["replacement"].items():
                assert v == sym_spell.replaced_words[k].term

    @pytest.mark.parametrize(
        "symspell_default_load, get_lookup_compound_data",
        [
            ("bigram", "lookup_compound_replaced_words_data.json"),
            ("unigram", "lookup_compound_replaced_words_data.json"),
        ],
        indirect=True,
    )
    def test_lookup_compound_ignore_non_words(
        self, symspell_default_load, get_lookup_compound_data
    ):
        sym_spell, dictionary = symspell_default_load
        for entry in get_lookup_compound_data:
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

    def test_load_dictionary_encoding(self, symspell_default):
        symspell_default.load_dictionary(NON_EN_DICT_PATH, 0, 1, encoding="utf-8")

        result = symspell_default.lookup("АБ", Verbosity.TOP, 2)
        assert 1 == len(result)
        assert "АБИ" == result[0].term

    @pytest.mark.parametrize("symspell_default_load", ["unigram"], indirect=True)
    def test_word_segmentation_ignore_token(self, symspell_default_load):
        sym_spell, _ = symspell_default_load
        typo = "24th december"
        result = sym_spell.word_segmentation(typo, ignore_token=r"\d{2}\w*\b")
        assert typo == result.corrected_string

    @pytest.mark.parametrize(
        "symspell_edit_distance_load, get_lookup_compound_data, with_arguments, capitalize",
        [
            (0, "word_segmentation_data.json", False, False),
            (0, "word_segmentation_data.json", True, False),
            (0, "word_segmentation_data.json", False, True),
        ],
        indirect=["symspell_edit_distance_load", "get_lookup_compound_data"],
    )
    def test_word_segmentation(
        self,
        symspell_edit_distance_load,
        get_lookup_compound_data,
        with_arguments,
        capitalize,
    ):
        sym_spell, edit_distance = symspell_edit_distance_load
        for entry in get_lookup_compound_data:
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

    def test_suggest_item(self):
        si_1 = SuggestItem("asdf", 12, 34)
        si_2 = SuggestItem("sdfg", 12, 34)
        si_3 = SuggestItem("dfgh", 56, 78)

        assert si_1 == si_2
        assert si_2 != si_3

        assert "asdf" == si_1.term
        si_1.term = "qwer"
        assert "qwer" == si_1.term

        assert 34 == si_1.count
        si_1.count = 78
        assert 78 == si_1.count

        assert "qwer, 12, 78" == str(si_1)

    def test_create_dictionary_invalid_path(self, symspell_default):
        assert not symspell_default.create_dictionary(INVALID_PATH)

    def test_create_dictionary(self, symspell_default):
        symspell_default.create_dictionary(BIG_MODIFIED_PATH, encoding="utf-8")

        num_lines = 0
        with open(BIG_WORDS_PATH, "r") as infile:
            for line in infile:
                key, count = line.rstrip().split(" ")
                assert int(count) == symspell_default.words[key]
                num_lines += 1
        assert num_lines == symspell_default.word_count

    @pytest.mark.parametrize(
        "symspell_default_load, is_compressed",
        [("unigram", True), ("unigram", False)],
        indirect=["symspell_default_load"],
    )
    def test_pickle(self, symspell_default, symspell_default_load, is_compressed):
        sym_spell, _ = symspell_default_load
        sym_spell.save_pickle(PICKLE_PATH, is_compressed)

        symspell_default.load_pickle(PICKLE_PATH, is_compressed)
        assert sym_spell.deletes == symspell_default.deletes
        assert sym_spell.words == symspell_default.words
        assert sym_spell._max_length == symspell_default._max_length
        os.remove(PICKLE_PATH)

    def test_pickle_invalid(self, symspell_default):
        pickle_data = {"deletes": {}, "words": {}, "max_length": 0, "data_version": -1}
        with open(PICKLE_PATH, "wb") as f:
            pickle.dump(pickle_data, f)
        assert not symspell_default.load_pickle(PICKLE_PATH, False)
        os.remove(PICKLE_PATH)

        pickle_data = {"deletes": {}, "words": {}, "max_length": 0}
        with open(PICKLE_PATH, "wb") as f:
            pickle.dump(pickle_data, f)
        assert not symspell_default.load_pickle(PICKLE_PATH, False)
        os.remove(PICKLE_PATH)

    @pytest.mark.parametrize(
        "symspell_default_entry",
        [[("stea", 1), ("steama", 2), ("steem", 3)]],
        indirect=True,
    )
    def test_delete_dictionary_entry(self, symspell_default_entry):
        result = symspell_default_entry.lookup("steama", Verbosity.TOP, 2)
        assert 1 == len(result)
        assert "steama" == result[0].term
        assert len("steama") == symspell_default_entry._max_length

        assert symspell_default_entry.delete_dictionary_entry("steama")
        assert "steama" not in symspell_default_entry.words
        assert len("steem") == symspell_default_entry._max_length

        result = symspell_default_entry.lookup("steama", Verbosity.TOP, 2)
        assert 1 == len(result)
        assert "steem" == result[0].term

        assert symspell_default_entry.delete_dictionary_entry("stea")
        assert "stea" not in symspell_default_entry.words
        assert len("steem") == symspell_default_entry._max_length

        result = symspell_default_entry.lookup("steama", Verbosity.TOP, 2)
        assert 1 == len(result)
        assert "steem" == result[0].term

    @pytest.mark.parametrize(
        "symspell_default_entry",
        [[("stea", 1), ("steama", 2), ("steem", 3)]],
        indirect=True,
    )
    def test_delete_dictionary_entry_invalid_word(self, symspell_default_entry):
        result = symspell_default_entry.lookup("steama", Verbosity.TOP, 2)
        assert 1 == len(result)
        assert "steama" == result[0].term
        assert len("steama") == symspell_default_entry._max_length

        assert not symspell_default_entry.delete_dictionary_entry("steamab")
        result = symspell_default_entry.lookup("steama", Verbosity.TOP, 2)
        assert 1 == len(result)
        assert "steama" == result[0].term
        assert len("steama") == symspell_default_entry._max_length

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
    def test_lookup_transfer_casing(self, symspell_default_entry, typo, correction):
        result = symspell_default_entry.lookup(
            typo, Verbosity.TOP, 2, transfer_casing=True
        )
        assert correction == result[0].term

    @pytest.mark.parametrize(
        "symspell_default_load, get_lookup_compound_data",
        [
            ("bigram", "lookup_compound_transfer_casing_data.json"),
            ("unigram", "lookup_compound_transfer_casing_data.json"),
        ],
        indirect=True,
    )
    def test_lookup_compound_transfer_casing(
        self, symspell_default_load, get_lookup_compound_data
    ):
        sym_spell, dictionary = symspell_default_load
        for entry in get_lookup_compound_data:
            results = sym_spell.lookup_compound(entry["typo"], 2, transfer_casing=True)
            assert entry[dictionary]["term"] == results[0].term

    @pytest.mark.parametrize(
        "symspell_default_load, get_lookup_compound_data",
        [
            ("bigram", "lookup_compound_transfer_casing_ignore_nonwords_data.json"),
            ("unigram", "lookup_compound_transfer_casing_ignore_nonwords_data.json"),
        ],
        indirect=True,
    )
    def test_lookup_compound_transfer_casing_ignore_nonwords(
        self, symspell_default_load, get_lookup_compound_data
    ):
        sym_spell, dictionary = symspell_default_load
        for entry in get_lookup_compound_data:
            results = sym_spell.lookup_compound(entry["typo"], 2, True, True)
            assert entry[dictionary]["term"] == results[0].term

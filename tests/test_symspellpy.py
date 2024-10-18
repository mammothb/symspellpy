from io import StringIO
from pathlib import Path
from unittest import TestCase

import pytest

from symspellpy import SymSpell, Verbosity
from symspellpy.abstract_distance_comparer import AbstractDistanceComparer
from symspellpy.editdistance import DistanceAlgorithm, EditDistance
from symspellpy.helpers import DictIO

FORTESTS_DIR = Path(__file__).resolve().parent / "fortests"
BAD_DICT_PATH = FORTESTS_DIR / "bad_dict.txt"
BELOW_THRESHOLD_DICT_PATH = FORTESTS_DIR / "below_threshold_dict.txt"
BIG_MODIFIED_PATH = FORTESTS_DIR / "big_modified.txt"
BIG_WORDS_PATH = FORTESTS_DIR / "big_words.txt"
NON_EN_DICT_PATH = FORTESTS_DIR / "non_en_dict.txt"
SEPARATOR_DICT_PATH = FORTESTS_DIR / "separator_dict.txt"

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
        "large count": 92233720368547758081,
    }
    if request.param is None:
        dict_stream = DictIO(dictionary)
    else:
        dict_stream = DictIO(dictionary, request.param)
    yield dict_stream, request.param


class CustomDistanceComparer(AbstractDistanceComparer):
    def distance(self, string_1: str, string_2: str, max_distance: int) -> int:
        return 0


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

    def test_set_distance_comparer(self):
        distance_comparer = EditDistance(
            DistanceAlgorithm.USER_PROVIDED, CustomDistanceComparer()
        )
        sym_spell = SymSpell(distance_comparer=distance_comparer)

        assert distance_comparer == sym_spell.distance_comparer

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

    def test_load_bigram_dictionary_invalid_path(self, symspell_default):
        with TestCase.assertLogs("symspellpy.symspellpy.logger", level="ERROR") as cm:
            assert not symspell_default.load_bigram_dictionary(INVALID_PATH, 0, 2)
        assert (
            f"Bigram dictionary file not found at {Path(INVALID_PATH)}."
            == cm.records[0].getMessage()
        )

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
        assert symspell_default._load_bigram_dictionary_stream(dict_stream, 0, 2)
        assert 2 == len(symspell_default.bigrams)
        assert 10956800 == symspell_default.bigrams["abcs of"]
        assert 10721728 == symspell_default.bigrams["aaron and"]
        assert "large count" not in symspell_default.bigrams

    @pytest.mark.parametrize("get_dictionary_stream", [SEPARATOR], indirect=True)
    def test_load_bigram_dictionary_stream_separator(
        self, symspell_default, get_dictionary_stream
    ):
        dict_stream, separator = get_dictionary_stream
        assert symspell_default._load_bigram_dictionary_stream(
            dict_stream, 0, 1, separator
        )
        assert 5 == len(symspell_default.bigrams)
        assert 23135851162 == symspell_default.bigrams["the"]
        assert 13151942776 == symspell_default.bigrams["of"]
        assert 10956800 == symspell_default.bigrams["abcs of"]
        assert 10721728 == symspell_default.bigrams["aaron and"]
        assert 12997637966 == symspell_default.bigrams["and"]

    def test_load_dictionary_invalid_path(self, symspell_default):
        with TestCase.assertLogs("symspellpy.symspellpy.logger", level="ERROR") as cm:
            assert not symspell_default.load_dictionary(INVALID_PATH, 0, 1)
        assert (
            f"Dictionary file not found at {Path(INVALID_PATH)}."
            == cm.records[0].getMessage()
        )

    def test_load_dictionary_bad_dictionary(self, symspell_default):
        assert symspell_default.load_dictionary(BAD_DICT_PATH, 0, 1)
        assert 2 == symspell_default.word_count
        assert 10 == symspell_default.words["asdf"]
        assert 12 == symspell_default.words["sdfg"]

    def test_load_dictionary_count(self, symspell_default, dictionary_path):
        symspell_default.load_dictionary(dictionary_path, 0, 1)

        assert 82834 == symspell_default.word_count
        assert 676094 == symspell_default.entry_count

    @pytest.mark.parametrize("symspell_short", [10], indirect=True)
    def test_load_dictionary_below_threshold(self, symspell_short):
        symspell_short.load_dictionary(BELOW_THRESHOLD_DICT_PATH, 0, 1)

        assert 1 == len(symspell_short.below_threshold_words)
        assert 8 == symspell_short.below_threshold_words["below"]

        assert 2 == symspell_short.word_count

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
        assert symspell_default._load_dictionary_stream(dict_stream, 0, 1)
        assert 3 == symspell_default.word_count
        assert 23135851162 == symspell_default.words["the"]
        assert 13151942776 == symspell_default.words["of"]
        assert 12997637966 == symspell_default.words["and"]

    @pytest.mark.parametrize("get_dictionary_stream", [SEPARATOR], indirect=True)
    def test_load_dictionary_stream_separator(
        self, symspell_default, get_dictionary_stream
    ):
        dict_stream, separator = get_dictionary_stream
        assert symspell_default._load_dictionary_stream(dict_stream, 0, 1, separator)
        assert 5 == symspell_default.word_count
        assert 23135851162 == symspell_default.words["the"]
        assert 13151942776 == symspell_default.words["of"]
        assert 10956800 == symspell_default.words["abcs of"]
        assert 10721728 == symspell_default.words["aaron and"]
        assert 12997637966 == symspell_default.words["and"]

    def test_load_dictionary_encoding(self, symspell_default):
        symspell_default.load_dictionary(NON_EN_DICT_PATH, 0, 1, encoding="utf-8")

        result = symspell_default.lookup("АБ", Verbosity.TOP, 2)
        assert 1 == len(result)
        assert "АБИ" == result[0].term

    def test_load_dictionary_from_string_io(self, symspell_default, dictionary_path):
        with open(dictionary_path, "r") as f:
            symspell_default.load_dictionary(StringIO(f.read()), 0, 1)
            assert 82834 == symspell_default.word_count
            assert 676094 == symspell_default.entry_count

    def test_load_dictionary_from_text_io_wrapper(self, symspell_default, dictionary_path):
        with open(dictionary_path, "r") as f:
            symspell_default.load_dictionary(f, 0, 1)
            assert 82834 == symspell_default.word_count
            assert 676094 == symspell_default.entry_count

    def test_create_dictionary_invalid_path(self, symspell_default):
        with TestCase.assertLogs("symspellpy.symspellpy.logger", level="ERROR") as cm:
            assert not symspell_default.create_dictionary(INVALID_PATH)
        assert (
            f"Corpus not found at {Path(INVALID_PATH)}." == cm.records[0].getMessage()
        )

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

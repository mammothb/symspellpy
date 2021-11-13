import os.path
import pickle
import sys
import unittest

import pkg_resources
import pytest

from symspellpy import SymSpell, Verbosity
from symspellpy.helpers import DictIO
from symspellpy.symspellpy import SuggestItem

class TestSymSpellPy(unittest.TestCase):
    dictionary_path = pkg_resources.resource_filename(
        "symspellpy", "frequency_dictionary_en_82_765.txt")
    bigram_path = pkg_resources.resource_filename(
        "symspellpy", "frequency_bigramdictionary_en_243_342.txt")
    fortests_path = os.path.join(os.path.dirname(__file__), "fortests")

    def test_negative_max_dictionary_edit_distance(self):
        with pytest.raises(ValueError) as excinfo:
            __ = SymSpell(-1, 3)
        self.assertEqual("max_dictionary_edit_distance cannot be negative",
                         str(excinfo.value))

    def test_invalid_prefix_length(self):
        # prefix_length < 1
        with pytest.raises(ValueError) as excinfo:
            __ = SymSpell(1, 0)
        self.assertEqual("prefix_length cannot be less than 1",
                         str(excinfo.value))

        with pytest.raises(ValueError) as excinfo:
            __ = SymSpell(1, -1)
        self.assertEqual("prefix_length cannot be less than 1",
                         str(excinfo.value))

        # prefix_length <= max_dictionary_edit_distance
        with pytest.raises(ValueError) as excinfo:
            __ = SymSpell(2, 2)
        self.assertEqual("prefix_length must be greater than max_dictionary_edit_distance",
                         str(excinfo.value))

    def test_negative_count_threshold(self):
        with pytest.raises(ValueError) as excinfo:
            __ = SymSpell(1, 3, -1)
        self.assertEqual("count_threshold cannot be negative",
                         str(excinfo.value))

    def test_create_dictionary_entry_negative_count(self):
        sym_spell = SymSpell(1, 3)
        self.assertEqual(False, sym_spell.create_dictionary_entry("pipe", 0))
        self.assertEqual(False,
                         sym_spell.create_dictionary_entry("pipe", -1))

        sym_spell = SymSpell(1, 3, count_threshold=0)
        self.assertEqual(True, sym_spell.create_dictionary_entry("pipe", 0))

    def test_create_dictionary_entry_below_threshold(self):
        sym_spell = SymSpell(1, 3, count_threshold=10)
        sym_spell.create_dictionary_entry("pipe", 4)
        self.assertEqual(1, len(sym_spell.below_threshold_words))
        self.assertEqual(4, sym_spell.below_threshold_words["pipe"])

        sym_spell.create_dictionary_entry("pipe", 4)
        self.assertEqual(1, len(sym_spell.below_threshold_words))
        self.assertEqual(8, sym_spell.below_threshold_words["pipe"])

        sym_spell.create_dictionary_entry("pipe", 4)
        self.assertEqual(0, len(sym_spell.below_threshold_words))

    def test_deletes(self):
        sym_spell = SymSpell()
        sym_spell.create_dictionary_entry("steama", 4)
        sym_spell.create_dictionary_entry("steamb", 6)
        sym_spell.create_dictionary_entry("steamc", 2)
        result = sym_spell.lookup("stream", Verbosity.TOP, 2)
        self.assertEqual(1, len(result))
        self.assertEqual("steamb", result[0].term)
        self.assertEqual(6, result[0].count)
        self.assertTrue(len(sym_spell.deletes))

    def test_words_with_shared_prefix_should_retain_counts(self):
        sym_spell = SymSpell(1, 3)
        sym_spell.create_dictionary_entry("pipe", 5)
        sym_spell.create_dictionary_entry("pips", 10)

        result = sym_spell.lookup("pipe", Verbosity.ALL, 1)
        self.assertEqual(2, len(result))
        self.assertEqual("pipe", result[0].term)
        self.assertEqual(5, result[0].count)
        self.assertEqual("pips", result[1].term)
        self.assertEqual(10, result[1].count)

        result = sym_spell.lookup("pips", Verbosity.ALL, 1)
        self.assertEqual(2, len(result))
        self.assertEqual("pips", result[0].term)
        self.assertEqual(10, result[0].count)
        self.assertEqual("pipe", result[1].term)
        self.assertEqual(5, result[1].count)

        result = sym_spell.lookup("pip", Verbosity.ALL, 1)
        self.assertEqual(2, len(result))
        self.assertEqual("pips", result[0].term)
        self.assertEqual(10, result[0].count)
        self.assertEqual("pipe", result[1].term)
        self.assertEqual(5, result[1].count)

    def test_add_additional_counts_should_not_add_word_again(self):
        sym_spell = SymSpell()
        word = "hello"
        sym_spell.create_dictionary_entry(word, 11)
        self.assertEqual(1, sym_spell.word_count)

        sym_spell.create_dictionary_entry(word, 3)
        self.assertEqual(1, sym_spell.word_count)

    def test_add_additional_counts_should_increase_count(self):
        sym_spell = SymSpell()
        word = "hello"
        sym_spell.create_dictionary_entry(word, 11)
        result = sym_spell.lookup(word, Verbosity.TOP)
        count = result[0].count if len(result) == 1 else 0
        self.assertEqual(11, count)

        sym_spell.create_dictionary_entry(word, 3)
        result = sym_spell.lookup(word, Verbosity.TOP)
        count = result[0].count if len(result) == 1 else 0
        self.assertEqual(11 + 3, count)

    def test_add_additional_counts_should_not_overflow(self):
        sym_spell = SymSpell()
        word = "hello"
        sym_spell.create_dictionary_entry(word, sys.maxsize - 10)
        result = sym_spell.lookup(word, Verbosity.TOP)
        count = result[0].count if len(result) == 1 else 0
        self.assertEqual(sys.maxsize - 10, count)

        sym_spell.create_dictionary_entry(word, 11)
        result = sym_spell.lookup(word, Verbosity.TOP)
        count = result[0].count if len(result) == 1 else 0
        self.assertEqual(sys.maxsize, count)

    def test_verbosity_should_control_lookup_results(self):
        sym_spell = SymSpell()
        sym_spell.create_dictionary_entry("steam", 1)
        sym_spell.create_dictionary_entry("steams", 2)
        sym_spell.create_dictionary_entry("steem", 3)

        result = sym_spell.lookup("steems", Verbosity.TOP, 2)
        self.assertEqual(1, len(result))
        result = sym_spell.lookup("steems", Verbosity.CLOSEST, 2)
        self.assertEqual(2, len(result))
        result = sym_spell.lookup("steems", Verbosity.ALL, 2)
        self.assertEqual(3, len(result))

    def test_lookup_should_return_most_frequent(self):
        sym_spell = SymSpell()
        sym_spell.create_dictionary_entry("steama", 4)
        sym_spell.create_dictionary_entry("steamb", 6)
        sym_spell.create_dictionary_entry("steamc", 2)
        result = sym_spell.lookup("stream", Verbosity.TOP, 2)
        self.assertEqual(1, len(result))
        self.assertEqual("steamb", result[0].term)
        self.assertEqual(6, result[0].count)

    def test_lookup_should_find_exact_match(self):
        sym_spell = SymSpell()
        sym_spell.create_dictionary_entry("steama", 4)
        sym_spell.create_dictionary_entry("steamb", 6)
        sym_spell.create_dictionary_entry("steamc", 2)
        result = sym_spell.lookup("streama", Verbosity.TOP, 2)
        self.assertEqual(1, len(result))
        self.assertEqual("steama", result[0].term)

    def test_lookup_should_not_return_non_word_delete(self):
        sym_spell = SymSpell(2, 7, 10)
        sym_spell.create_dictionary_entry("pawn", 10)
        result = sym_spell.lookup("paw", Verbosity.TOP, 0)
        self.assertEqual(0, len(result))
        result = sym_spell.lookup("awn", Verbosity.TOP, 0)
        self.assertEqual(0, len(result))

    def test_lookup_should_not_return_low_count_word(self):
        sym_spell = SymSpell(2, 7, 10)
        sym_spell.create_dictionary_entry("pawn", 1)
        result = sym_spell.lookup("pawn", Verbosity.TOP, 0)
        self.assertEqual(0, len(result))

    def test_lookup_should_not_return_low_count_word_that_are_also_delete_word(self):
        sym_spell = SymSpell(2, 7, 10)
        sym_spell.create_dictionary_entry("flame", 20)
        sym_spell.create_dictionary_entry("flam", 1)
        result = sym_spell.lookup("flam", Verbosity.TOP, 0)
        self.assertEqual(0, len(result))

    def test_lookup_max_edit_distance_too_large(self):
        sym_spell = SymSpell(2, 7, 10)
        sym_spell.create_dictionary_entry("flame", 20)
        sym_spell.create_dictionary_entry("flam", 1)
        with pytest.raises(ValueError) as excinfo:
            __ = sym_spell.lookup("flam", Verbosity.TOP, 3)
        self.assertEqual("Distance too large", str(excinfo.value))

    def test_lookup_include_unknown(self):
        sym_spell = SymSpell(2, 7, 10)
        sym_spell.create_dictionary_entry("flame", 20)
        sym_spell.create_dictionary_entry("flam", 1)
        result = sym_spell.lookup("flam", Verbosity.TOP, 0, True)
        self.assertEqual(1, len(result))
        self.assertEqual("flam", result[0].term)

    def test_lookup_avoid_exact_match_early_exit(self):
        edit_distance_max = 2
        sym_spell = SymSpell(edit_distance_max, 7, 10)
        sym_spell.create_dictionary_entry("flame", 20)
        sym_spell.create_dictionary_entry("flam", 1)
        result = sym_spell.lookup("24th", Verbosity.ALL, edit_distance_max,
                                  ignore_token=r"\d{2}\w*\b")
        self.assertEqual(1, len(result))
        self.assertEqual("24th", result[0].term)

    def test_load_bigram_dictionary_invalid_path(self):
        edit_distance_max = 2
        prefix_length = 7
        sym_spell = SymSpell(edit_distance_max, prefix_length)
        self.assertEqual(False, sym_spell.load_bigram_dictionary(
            "invalid/dictionary/path.txt", 0, 2))

    def test_loading_dictionary_from_fileobject(self):
        big_words_path = os.path.join(self.fortests_path, "big_words.txt")
        edit_distance_max = 2
        prefix_length = 7
        sym_spell = SymSpell(edit_distance_max, prefix_length)
        with open(big_words_path, 'r', encoding='utf8') as file:
            self.assertEqual(True, sym_spell.create_dictionary(file))

    def test_load_bigram_dictionary_bad_dict(self):
        dictionary_path = os.path.join(self.fortests_path,
                                       "bad_dict.txt")
        edit_distance_max = 2
        prefix_length = 7
        sym_spell = SymSpell(edit_distance_max, prefix_length)
        self.assertEqual(True, sym_spell.load_bigram_dictionary(
            dictionary_path, 0, 2))
        self.assertEqual(2, len(sym_spell.bigrams))
        self.assertEqual(12, sym_spell.bigrams["rtyu tyui"])
        self.assertEqual(13, sym_spell.bigrams["yuio uiop"])

    def test_load_bigram_dictionary_separator(self):
        dictionary_path = os.path.join(self.fortests_path,
                                       "separator_dict.txt")
        edit_distance_max = 2
        prefix_length = 7
        sym_spell = SymSpell(edit_distance_max, prefix_length)
        self.assertEqual(True, sym_spell.load_bigram_dictionary(
            dictionary_path, 0, 1, "$"))
        self.assertEqual(5, len(sym_spell.bigrams))
        self.assertEqual(23135851162, sym_spell.bigrams["the"])
        self.assertEqual(13151942776, sym_spell.bigrams["of"])
        self.assertEqual(10956800, sym_spell.bigrams["abcs of"])
        self.assertEqual(10721728, sym_spell.bigrams["aaron and"])
        self.assertEqual(12997637966, sym_spell.bigrams["and"])

    def test_load_bigram_dictionary_stream(self):
        dictionary = {"the": 23135851162,
                      "of": 13151942776,
                      "abcs of": 10956800,
                      "aaron and": 10721728,
                      "and": 12997637966}
        dict_stream = DictIO(dictionary)
        edit_distance_max = 2
        prefix_length = 7
        sym_spell = SymSpell(edit_distance_max, prefix_length)
        self.assertEqual(True, sym_spell.load_bigram_dictionary_stream(
            dict_stream, 0, 2))
        self.assertEqual(2, len(sym_spell.bigrams))
        self.assertEqual(10956800, sym_spell.bigrams["abcs of"])
        self.assertEqual(10721728, sym_spell.bigrams["aaron and"])

    def test_load_bigram_dictionary_stream_separator(self):
        dictionary = {"the": 23135851162,
                      "of": 13151942776,
                      "abcs of": 10956800,
                      "aaron and": 10721728,
                      "and": 12997637966}
        dict_stream = DictIO(dictionary, "$")
        edit_distance_max = 2
        prefix_length = 7
        sym_spell = SymSpell(edit_distance_max, prefix_length)
        self.assertEqual(True, sym_spell.load_bigram_dictionary_stream(
            dict_stream, 0, 1, "$"))
        self.assertEqual(5, len(sym_spell.bigrams))
        self.assertEqual(23135851162, sym_spell.bigrams["the"])
        self.assertEqual(13151942776, sym_spell.bigrams["of"])
        self.assertEqual(10956800, sym_spell.bigrams["abcs of"])
        self.assertEqual(10721728, sym_spell.bigrams["aaron and"])
        self.assertEqual(12997637966, sym_spell.bigrams["and"])

    def test_load_dictionary_invalid_path(self):
        edit_distance_max = 2
        prefix_length = 7
        sym_spell = SymSpell(edit_distance_max, prefix_length)
        self.assertEqual(False, sym_spell.load_dictionary(
            "invalid/dictionary/path.txt", 0, 1))

    def test_load_dictionary_bad_dictionary(self):
        dictionary_path = os.path.join(self.fortests_path, "bad_dict.txt")
        edit_distance_max = 2
        prefix_length = 7
        sym_spell = SymSpell(edit_distance_max, prefix_length)
        self.assertEqual(True, sym_spell.load_dictionary(
            dictionary_path, 0, 1))
        self.assertEqual(2, sym_spell.word_count)
        self.assertEqual(10, sym_spell.words["asdf"])
        self.assertEqual(12, sym_spell.words["sdfg"])

    def test_load_dictionary_separator(self):
        dictionary_path = os.path.join(self.fortests_path,
                                       "separator_dict.txt")
        edit_distance_max = 2
        prefix_length = 7
        sym_spell = SymSpell(edit_distance_max, prefix_length)
        self.assertEqual(True, sym_spell.load_dictionary(
            dictionary_path, 0, 1, "$"))
        self.assertEqual(5, sym_spell.word_count)
        self.assertEqual(23135851162, sym_spell.words["the"])
        self.assertEqual(13151942776, sym_spell.words["of"])
        self.assertEqual(10956800, sym_spell.words["abcs of"])
        self.assertEqual(10721728, sym_spell.words["aaron and"])
        self.assertEqual(12997637966, sym_spell.words["and"])

    def test_load_dictionary_stream(self):
        # keys with space in them don't get parsed properly when using
        # the default separator=" "
        dictionary = {"the": 23135851162,
                      "of": 13151942776,
                      "abcs of": 10956800,
                      "aaron and": 10721728,
                      "and": 12997637966}
        dict_stream = DictIO(dictionary)
        edit_distance_max = 2
        prefix_length = 7
        sym_spell = SymSpell(edit_distance_max, prefix_length)
        self.assertEqual(True, sym_spell.load_dictionary_stream(
            dict_stream, 0, 1))
        self.assertEqual(3, sym_spell.word_count)
        self.assertEqual(23135851162, sym_spell.words["the"])
        self.assertEqual(13151942776, sym_spell.words["of"])
        self.assertEqual(12997637966, sym_spell.words["and"])

    def test_load_dictionary_stream_separator(self):
        dictionary = {"the": 23135851162,
                      "of": 13151942776,
                      "abcs of": 10956800,
                      "aaron and": 10721728,
                      "and": 12997637966}
        dict_stream = DictIO(dictionary, "$")
        edit_distance_max = 2
        prefix_length = 7
        sym_spell = SymSpell(edit_distance_max, prefix_length)
        self.assertEqual(True, sym_spell.load_dictionary_stream(
            dict_stream, 0, 1, "$"))
        self.assertEqual(5, sym_spell.word_count)
        self.assertEqual(23135851162, sym_spell.words["the"])
        self.assertEqual(13151942776, sym_spell.words["of"])
        self.assertEqual(10956800, sym_spell.words["abcs of"])
        self.assertEqual(10721728, sym_spell.words["aaron and"])
        self.assertEqual(12997637966, sym_spell.words["and"])

    def test_lookup_should_replicate_noisy_results(self):
        query_path = os.path.join(self.fortests_path,
                                  "noisy_query_en_1000.txt")

        edit_distance_max = 2
        prefix_length = 7
        verbosity = Verbosity.CLOSEST
        sym_spell = SymSpell(edit_distance_max, prefix_length)
        sym_spell.load_dictionary(self.dictionary_path, 0, 1)

        test_list = []
        with open(query_path, "r") as infile:
            for line in infile.readlines():
                line_parts = line.rstrip().split(" ")
                if len(line_parts) >= 2:
                    test_list.append(line_parts[0])
        result_sum = 0
        for phrase in test_list:
            result_sum += len(sym_spell.lookup(phrase, verbosity,
                                               edit_distance_max))
        self.assertEqual(4945, result_sum)

    def test_lookup_compound(self):
        edit_distance_max = 2
        prefix_length = 7
        sym_spell = SymSpell(edit_distance_max, prefix_length)
        sym_spell.load_dictionary(self.dictionary_path, 0, 1)
        sym_spell.load_bigram_dictionary(self.bigram_path, 0, 2)

        typo = "whereis th elove"
        correction = "where is the love"
        results = sym_spell.lookup_compound(typo, edit_distance_max)
        self.assertEqual(1, len(results))
        self.assertEqual(correction, results[0].term)
        self.assertEqual(2, results[0].distance)
        self.assertEqual(585, results[0].count)

        typo = "the bigjest playrs"
        correction = "the biggest players"
        results = sym_spell.lookup_compound(typo, edit_distance_max)
        self.assertEqual(1, len(results))
        self.assertEqual(correction, results[0].term)
        self.assertEqual(2, results[0].distance)
        self.assertEqual(34, results[0].count)

        typo = "Can yu readthis"
        correction = "can you read this"
        results = sym_spell.lookup_compound(typo, edit_distance_max)
        self.assertEqual(1, len(results))
        self.assertEqual(correction, results[0].term)
        self.assertEqual(3, results[0].distance)
        self.assertEqual(11440, results[0].count)

        typo = ("whereis th elove hehad dated forImuch of thepast who "
                "couqdn'tread in sixthgrade and ins pired him")
        correction = ("where is the love he had dated for much of the past "
                      "who couldn't read in sixth grade and inspired him")
        results = sym_spell.lookup_compound(typo, edit_distance_max)
        self.assertEqual(1, len(results))
        self.assertEqual(correction, results[0].term)
        self.assertEqual(9, results[0].distance)
        self.assertEqual(0, results[0].count)

        typo = "in te dhird qarter oflast jear he hadlearned ofca sekretplan"
        correction = ("in the third quarter of last year he had learned of a "
                      "secret plan")
        results = sym_spell.lookup_compound(typo, edit_distance_max)
        self.assertEqual(1, len(results))
        self.assertEqual(correction, results[0].term)
        self.assertEqual(9, results[0].distance)
        self.assertEqual(0, results[0].count)

        typo = ("the bigjest playrs in te strogsommer film slatew ith plety "
                "of funn")
        correction = ("the biggest players in the strong summer film slate "
                      "with plenty of fun")
        results = sym_spell.lookup_compound(typo, edit_distance_max)
        self.assertEqual(1, len(results))
        self.assertEqual(correction, results[0].term)
        self.assertEqual(9, results[0].distance)
        self.assertEqual(0, results[0].count)

        typo = ("Can yu readthis messa ge despite thehorible sppelingmsitakes")
        correction = ("can you read this message despite the horrible "
                      "spelling mistakes")
        results = sym_spell.lookup_compound(typo, edit_distance_max)
        self.assertEqual(1, len(results))
        self.assertEqual(correction, results[0].term)
        self.assertEqual(10, results[0].distance)
        self.assertEqual(0, results[0].count)

    def test_lookup_compound_no_bigram(self):
        edit_distance_max = 2
        prefix_length = 7
        sym_spell = SymSpell(edit_distance_max, prefix_length)
        sym_spell.load_dictionary(self.dictionary_path, 0, 1)

        typo = "whereis th elove"
        correction = "whereas the love"
        results = sym_spell.lookup_compound(typo, edit_distance_max)
        self.assertEqual(1, len(results))
        self.assertEqual(correction, results[0].term)
        self.assertEqual(2, results[0].distance)
        self.assertEqual(64, results[0].count)

        typo = "the bigjest playrs"
        correction = "the biggest players"
        results = sym_spell.lookup_compound(typo, edit_distance_max)
        self.assertEqual(1, len(results))
        self.assertEqual(correction, results[0].term)
        self.assertEqual(2, results[0].distance)
        self.assertEqual(34, results[0].count)

        typo = "Can yu readthis"
        correction = "can you read this"
        results = sym_spell.lookup_compound(typo, edit_distance_max)
        self.assertEqual(1, len(results))
        self.assertEqual(correction, results[0].term)
        self.assertEqual(3, results[0].distance)
        self.assertEqual(3, results[0].count)

        typo = ("whereis th elove hehad dated forImuch of thepast who "
                "couqdn'tread in sixthgrade and ins pired him")
        correction = ("whereas the love head dated for much of the past who "
                      "couldn't read in sixth grade and inspired him")
        results = sym_spell.lookup_compound(typo, edit_distance_max)
        self.assertEqual(1, len(results))
        self.assertEqual(correction, results[0].term)
        self.assertEqual(9, results[0].distance)
        self.assertEqual(0, results[0].count)

        typo = "in te dhird qarter oflast jear he hadlearned ofca sekretplan"
        correction = ("in the third quarter of last year he had learned of "
                      "a secret plan")
        results = sym_spell.lookup_compound(typo, edit_distance_max)
        self.assertEqual(1, len(results))
        self.assertEqual(correction, results[0].term)
        self.assertEqual(9, results[0].distance)
        self.assertEqual(0, results[0].count)

        typo = ("the bigjest playrs in te strogsommer film slatew ith plety "
                "of funn")
        correction = ("the biggest players in the strong summer film slate "
                      "with plenty of fun")
        results = sym_spell.lookup_compound(typo, edit_distance_max)
        self.assertEqual(1, len(results))
        self.assertEqual(correction, results[0].term)
        self.assertEqual(9, results[0].distance)
        self.assertEqual(0, results[0].count)

        typo = ("Can yu readthis messa ge despite thehorible sppelingmsitakes")
        correction = ("can you read this message despite the horrible "
                      "spelling mistakes")
        results = sym_spell.lookup_compound(typo, edit_distance_max)
        self.assertEqual(1, len(results))
        self.assertEqual(correction, results[0].term)
        self.assertEqual(10, results[0].distance)
        self.assertEqual(0, results[0].count)

    def test_lookup_compound_only_combi(self):
        edit_distance_max = 2
        prefix_length = 7
        sym_spell = SymSpell(edit_distance_max, prefix_length)
        sym_spell.create_dictionary_entry("steam", 1)
        sym_spell.create_dictionary_entry("machine", 1)

        typo = "ste am machie"
        correction = "steam machine"
        results = sym_spell.lookup_compound(typo, edit_distance_max)
        self.assertEqual(1, len(results))
        self.assertEqual(correction, results[0].term)

    def test_lookup_compound_no_suggestion(self):
        edit_distance_max = 2
        prefix_length = 7
        sym_spell = SymSpell(edit_distance_max, prefix_length)
        sym_spell.create_dictionary_entry("steam", 1)
        sym_spell.create_dictionary_entry("machine", 1)

        typo = "qwer erty ytui a"
        results = sym_spell.lookup_compound(typo, edit_distance_max)
        self.assertEqual(1, len(results))
        self.assertEqual(typo, results[0].term)

    def test_lookup_compound_replaced_words(self):
        edit_distance_max = 2
        prefix_length = 7
        sym_spell = SymSpell(edit_distance_max, prefix_length)
        sym_spell.load_dictionary(self.dictionary_path, 0, 1)
        sym_spell.load_bigram_dictionary(self.bigram_path, 0, 2)

        typo = ("whereis th elove hehad dated forImuch of thepast who "
                "couqdn'tread in sixthgrade and ins pired him")
        correction = ("where is the love he had dated for much of the past "
                      "who couldn't read in sixth grade and inspired him")
        replacement_1 = {
            "whereis": "where is",
            "th": "the",
            "elove": "love",
            "hehad": "he had",
            "forimuch": "for much",
            "thepast": "the past",
            "couqdn'tread": "couldn't read",
            "sixthgrade": "sixth grade",
            "ins": "in"}
        results = sym_spell.lookup_compound(typo, edit_distance_max)
        self.assertEqual(len(replacement_1), len(sym_spell.replaced_words))
        for k, v in replacement_1.items():
            self.assertEqual(v, sym_spell.replaced_words[k].term)

        typo = "in te dhird qarter oflast jear he hadlearned ofca sekretplan"
        correction = ("in the third quarter of last year he had learned of a "
                      "secret plan")
        replacement_2 = {
            "te": "the",
            "dhird": "third",
            "qarter": "quarter",
            "oflast": "of last",
            "jear": "year",
            "hadlearned": "had learned",
            "ofca": "of a",
            "sekretplan": "secret plan"}
        results = sym_spell.lookup_compound(typo, edit_distance_max)
        self.assertEqual(len(replacement_1) + len(replacement_2),
                         len(sym_spell.replaced_words))
        for k, v in replacement_2.items():
            self.assertEqual(v, sym_spell.replaced_words[k].term)

        typo = ("the bigjest playrs in te strogsommer film slatew ith plety "
                "of funn")
        correction = ("the biggest players in the strong summer film slate "
                      "with plenty of fun")
        replacement_3 = {
            "bigjest": "biggest",
            "playrs": "players",
            "strogsommer": "strong summer",
            "slatew": "slate",
            "ith": "with",
            "plety": "plenty",
            "funn": "fun"}
        results = sym_spell.lookup_compound(typo, edit_distance_max)
        self.assertEqual(len(replacement_1) + len(replacement_2) +
                         len(replacement_3), len(sym_spell.replaced_words))
        self.assertEqual(1, len(results))
        self.assertEqual(correction, results[0].term)
        for k, v in replacement_3.items():
            self.assertEqual(v, sym_spell.replaced_words[k].term)

    def test_lookup_compound_replaced_words_no_bigram(self):
        edit_distance_max = 2
        prefix_length = 7
        sym_spell = SymSpell(edit_distance_max, prefix_length)
        sym_spell.load_dictionary(self.dictionary_path, 0, 1)

        typo = ("whereis th elove hehad dated forImuch of thepast who "
                "couqdn'tread in sixthgrade and ins pired him")
        correction = ("whereas the love head dated for much of the past who "
                      "couldn't read in sixth grade and inspired him")
        replacement_1 = {
            "whereis": "whereas",
            "th": "the",
            "elove": "love",
            "hehad": "head",
            "forimuch": "for much",
            "thepast": "the past",
            "couqdn'tread": "couldn't read",
            "sixthgrade": "sixth grade",
            "ins": "in"}
        results = sym_spell.lookup_compound(typo, edit_distance_max)
        self.assertEqual(len(replacement_1), len(sym_spell.replaced_words))
        for k, v in replacement_1.items():
            self.assertEqual(v, sym_spell.replaced_words[k].term)

        typo = "in te dhird qarter oflast jear he hadlearned ofca sekretplan"
        correction = ("in the third quarter of last year he had learned of a "
                      "secret plan")
        replacement_2 = {
            "te": "the",
            "dhird": "third",
            "qarter": "quarter",
            "oflast": "of last",
            "jear": "year",
            "hadlearned": "had learned",
            "ofca": "of a",
            "sekretplan": "secret plan"}
        results = sym_spell.lookup_compound(typo, edit_distance_max)
        self.assertEqual(len(replacement_1) + len(replacement_2),
                         len(sym_spell.replaced_words))
        for k, v in replacement_2.items():
            self.assertEqual(v, sym_spell.replaced_words[k].term)

        typo = ("the bigjest playrs in te strogsommer film slatew ith plety "
                "of funn")
        correction = ("the biggest players in the strong summer film slate "
                      "with plenty of fun")
        replacement_3 = {
            "bigjest": "biggest",
            "playrs": "players",
            "strogsommer": "strong summer",
            "slatew": "slate",
            "ith": "with",
            "plety": "plenty",
            "funn": "fun"}
        results = sym_spell.lookup_compound(typo, edit_distance_max)
        self.assertEqual(len(replacement_1) + len(replacement_2) +
                         len(replacement_3), len(sym_spell.replaced_words))
        self.assertEqual(1, len(results))
        self.assertEqual(correction, results[0].term)
        for k, v in replacement_3.items():
            self.assertEqual(v, sym_spell.replaced_words[k].term)

    def test_lookup_compound_ignore_non_words(self):
        edit_distance_max = 2
        prefix_length = 7
        sym_spell = SymSpell(edit_distance_max, prefix_length)
        sym_spell.load_dictionary(self.dictionary_path, 0, 1)
        sym_spell.load_bigram_dictionary(self.bigram_path, 0, 2)

        typo = ("whereis th elove 123 hehad dated forImuch of THEPAST who "
                "couqdn'tread in SIXTHgrade and ins pired him")
        correction = ("where is the love 123 he had dated for much of THEPAST "
                      "who couldn't read in sixth grade and inspired him")
        results = sym_spell.lookup_compound(typo, edit_distance_max, True)
        self.assertEqual(1, len(results))
        self.assertEqual(correction, results[0].term)

        typo = "in te DHIRD 1 qarter oflast jear he hadlearned ofca sekretplan"
        correction = ("in the DHIRD 1 quarter of last year he had learned "
                      "of a secret plan")
        results = sym_spell.lookup_compound(typo, edit_distance_max, True)
        self.assertEqual(1, len(results))
        self.assertEqual(correction, results[0].term)

        typo = ("the bigjest playrs in te stroGSOmmer film slatew ith PLETY "
                "of 12 funn")
        correction = ("the biggest players in the strong summer film slate "
                      "with PLETY of 12 fun")
        results = sym_spell.lookup_compound(typo, edit_distance_max, True)
        self.assertEqual(1, len(results))
        self.assertEqual(correction, results[0].term)

        typo = ("Can yu readtHIS messa ge despite thehorible 1234 "
                "sppelingmsitakes")
        correction = ("can you read this message despite the horrible 1234 "
                      "spelling mistakes")
        results = sym_spell.lookup_compound(typo, edit_distance_max, True)
        self.assertEqual(1, len(results))
        self.assertEqual(correction, results[0].term)

        typo = ("Can yu readtHIS messa ge despite thehorible AB1234 "
                "sppelingmsitakes")
        correction = ("can you read this message despite the horrible AB1234 "
                      "spelling mistakes")
        results = sym_spell.lookup_compound(typo, edit_distance_max, True)
        self.assertEqual(1, len(results))
        self.assertEqual(correction, results[0].term)

        typo = "PI on leave, arrange Co-I to do screening"
        correction = "PI on leave arrange co i to do screening"
        results = sym_spell.lookup_compound(typo, edit_distance_max, True)
        self.assertEqual(1, len(results))
        self.assertEqual(correction, results[0].term)

        typo = "is the officeon 1st floor oepn 24/7"
        correction = "is the office on 1st floor open 24/7"
        results = sym_spell.lookup_compound(typo, edit_distance_max,
                                            split_phrase_by_space=True, 
                                            ignore_non_words=True,
                                            ignore_term_with_digits=True)
        self.assertEqual(1, len(results))
        self.assertEqual(correction, results[0].term)
        self.assertEqual(2, results[0].distance)
        self.assertEqual(0, results[0].count)

    def test_lookup_compound_ignore_non_words_no_bigram(self):
        edit_distance_max = 2
        prefix_length = 7
        sym_spell = SymSpell(edit_distance_max, prefix_length)
        sym_spell.load_dictionary(self.dictionary_path, 0, 1)

        typo = ("whereis th elove 123 hehad dated forImuch of THEPAST who "
                "couqdn'tread in SIXTHgrade and ins pired him")
        correction = ("whereas the love 123 head dated for much of THEPAST "
                      "who couldn't read in sixth grade and inspired him")
        results = sym_spell.lookup_compound(typo, edit_distance_max, True)
        self.assertEqual(1, len(results))
        self.assertEqual(correction, results[0].term)

        typo = "in te DHIRD 1 qarter oflast jear he hadlearned ofca sekretplan"
        correction = ("in the DHIRD 1 quarter of last year he had learned "
                      "of a secret plan")
        results = sym_spell.lookup_compound(typo, edit_distance_max, True)
        self.assertEqual(1, len(results))
        self.assertEqual(correction, results[0].term)

        typo = ("the bigjest playrs in te stroGSOmmer film slatew ith PLETY "
                "of 12 funn")
        correction = ("the biggest players in the strong summer film slate "
                      "with PLETY of 12 fun")
        results = sym_spell.lookup_compound(typo, edit_distance_max, True)
        self.assertEqual(1, len(results))
        self.assertEqual(correction, results[0].term)

        typo = ("Can yu readtHIS messa ge despite thehorible 1234 "
                "sppelingmsitakes")
        correction = ("can you read this message despite the horrible 1234 "
                      "spelling mistakes")
        results = sym_spell.lookup_compound(typo, edit_distance_max, True)
        self.assertEqual(1, len(results))
        self.assertEqual(correction, results[0].term)

        typo = ("Can yu readtHIS messa ge despite thehorible AB1234 "
                "sppelingmsitakes")
        correction = ("can you read this message despite the horrible AB1234 "
                      "spelling mistakes")
        results = sym_spell.lookup_compound(typo, edit_distance_max, True)
        self.assertEqual(1, len(results))
        self.assertEqual(correction, results[0].term)

        typo = "PI on leave, arrange Co-I to do screening"
        correction = "PI on leave arrange co i to do screening"
        results = sym_spell.lookup_compound(typo, edit_distance_max, True)
        self.assertEqual(1, len(results))
        self.assertEqual(correction, results[0].term)

    def test_load_dictionary_encoding(self):
        dictionary_path = os.path.join(self.fortests_path, "non_en_dict.txt")

        edit_distance_max = 2
        prefix_length = 7
        sym_spell = SymSpell(edit_distance_max, prefix_length)
        sym_spell.load_dictionary(dictionary_path, 0, 1, encoding="utf-8")

        result = sym_spell.lookup("АБ", Verbosity.TOP, 2)
        self.assertEqual(1, len(result))
        self.assertEqual("АБИ", result[0].term)

    def test_word_segmentation(self):
        edit_distance_max = 0
        prefix_length = 7
        sym_spell = SymSpell(edit_distance_max, prefix_length)
        sym_spell.load_dictionary(self.dictionary_path, 0, 1)

        typo = "thequickbrownfoxjumpsoverthelazydog"
        correction = "the quick brown fox jumps over the lazy dog"
        result = sym_spell.word_segmentation(typo)
        self.assertEqual(correction, result.corrected_string)

        typo = "itwasabrightcolddayinaprilandtheclockswerestrikingthirteen"
        correction = ("it was a bright cold day in april and the clocks "
                      "were striking thirteen")
        result = sym_spell.word_segmentation(typo)
        self.assertEqual(correction, result[1])

        typo = ("itwasthebestoftimesitwastheworstoftimesitwastheageofwisdom"
                "itwastheageoffoolishness")
        correction = ("it was the best of times it was the worst of times "
                      "it was the age of wisdom it was the age of foolishness")
        result = sym_spell.word_segmentation(typo)
        self.assertEqual(correction, result[1])

    def test_word_segmentation_ignore_token(self):
        edit_distance_max = 2
        prefix_length = 7
        sym_spell = SymSpell(edit_distance_max, prefix_length)
        sym_spell.load_dictionary(self.dictionary_path, 0, 1)

        typo = "24th december"
        result = sym_spell.word_segmentation(typo, ignore_token=r"\d{2}\w*\b")
        self.assertEqual(typo, result.corrected_string)

    def test_word_segmentation_with_arguments(self):
        edit_distance_max = 0
        prefix_length = 7
        sym_spell = SymSpell(edit_distance_max, prefix_length)
        sym_spell.load_dictionary(self.dictionary_path, 0, 1)

        typo = "thequickbrownfoxjumpsoverthelazydog"
        correction = "the quick brown fox jumps over the lazy dog"
        result = sym_spell.word_segmentation(typo, edit_distance_max, 11)
        self.assertEqual(correction, result.corrected_string)

        typo = "itwasabrightcolddayinaprilandtheclockswerestrikingthirteen"
        correction = ("it was a bright cold day in april and the clocks "
                      "were striking thirteen")
        result = sym_spell.word_segmentation(typo, edit_distance_max, 11)
        self.assertEqual(correction, result.corrected_string)

        typo = (" itwasthebestoftimesitwastheworstoftimesitwastheageofwisdom"
                "itwastheageoffoolishness")
        correction = ("it was the best of times it was the worst of times "
                      "it was the age of wisdom it was the age of foolishness")
        result = sym_spell.word_segmentation(typo, edit_distance_max, 11)
        self.assertEqual(correction, result.corrected_string)

    def test_word_segmentation_capitalize(self):
        edit_distance_max = 0
        prefix_length = 7
        sym_spell = SymSpell(edit_distance_max, prefix_length)
        sym_spell.load_dictionary(self.dictionary_path, 0, 1)

        typo = "Thequickbrownfoxjumpsoverthelazydog"
        correction = "The quick brown fox jumps over the lazy dog"
        result = sym_spell.word_segmentation(typo)
        self.assertEqual(correction, result.corrected_string)

        typo = "Itwasabrightcolddayinaprilandtheclockswerestrikingthirteen"
        correction = ("It was a bright cold day in april and the clocks "
                      "were striking thirteen")
        result = sym_spell.word_segmentation(typo)
        self.assertEqual(correction, result[1])

        typo = ("Itwasthebestoftimesitwastheworstoftimesitwastheageofwisdom"
                "itwastheageoffoolishness")
        correction = ("It was the best of times it was the worst of times "
                      "it was the age of wisdom it was the age of foolishness")
        result = sym_spell.word_segmentation(typo)
        self.assertEqual(correction, result[1])

    def test_word_segmentation_apostrophe(self):
        edit_distance_max = 0
        prefix_length = 7
        sym_spell = SymSpell(edit_distance_max, prefix_length)
        sym_spell.load_dictionary(self.dictionary_path, 0, 1)

        typo = "There'resomewords"
        correction = ("There' re some words")
        result = sym_spell.word_segmentation(typo)
        self.assertEqual(correction, result[1])

    def test_word_segmentation_ligature(self):
        edit_distance_max = 0
        prefix_length = 7
        sym_spell = SymSpell(edit_distance_max, prefix_length)
        sym_spell.load_dictionary(self.dictionary_path, 0, 1)

        typo = "Therearesomescientiﬁcwords"
        correction = ("There are some scientific words")
        result = sym_spell.word_segmentation(typo)
        self.assertEqual(correction, result[1])

    def test_suggest_item(self):
        si_1 = SuggestItem("asdf", 12, 34)
        si_2 = SuggestItem("sdfg", 12, 34)
        si_3 = SuggestItem("dfgh", 56, 78)

        self.assertTrue(si_1 == si_2)
        self.assertFalse(si_2 == si_3)

        self.assertEqual("asdf", si_1.term)
        si_1.term = "qwer"
        self.assertEqual("qwer", si_1.term)

        self.assertEqual(34, si_1.count)
        si_1.count = 78
        self.assertEqual(78, si_1.count)

        self.assertEqual("qwer, 12, 78", str(si_1))

    def test_create_dictionary_invalid_path(self):
        edit_distance_max = 2
        prefix_length = 7
        sym_spell = SymSpell(edit_distance_max, prefix_length)
        self.assertEqual(False, sym_spell.create_dictionary(
            "invalid/dictionary/path.txt"))

    def test_create_dictionary(self):
        corpus_path = os.path.join(self.fortests_path, "big_modified.txt")
        big_words_path = os.path.join(self.fortests_path, "big_words.txt")

        edit_distance_max = 2
        prefix_length = 7
        sym_spell = SymSpell(edit_distance_max, prefix_length)
        sym_spell.create_dictionary(corpus_path, encoding="utf-8")

        num_lines = 0
        with open(big_words_path, "r") as infile:
            for line in infile:
                key, count = line.rstrip().split(" ")
                self.assertEqual(int(count), sym_spell.words[key])
                num_lines += 1
        self.assertEqual(num_lines, sym_spell.word_count)

    def test_pickle_uncompressed(self):
        pickle_path = os.path.join(self.fortests_path, "dictionary.pickle")
        is_compressed = False
        edit_distance_max = 2
        prefix_length = 7
        sym_spell = SymSpell(edit_distance_max, prefix_length)
        sym_spell.load_dictionary(self.dictionary_path, 0, 1)
        sym_spell.save_pickle(pickle_path, is_compressed)

        sym_spell_2 = SymSpell(edit_distance_max, prefix_length)
        sym_spell_2.load_pickle(pickle_path, is_compressed)
        self.assertEqual(sym_spell.deletes, sym_spell_2.deletes)
        self.assertEqual(sym_spell.words, sym_spell_2.words)
        self.assertEqual(sym_spell._max_length, sym_spell_2._max_length)
        os.remove(pickle_path)

    def test_pickle_compressed(self):
        pickle_path = os.path.join(self.fortests_path, "dictionary.pickle")
        edit_distance_max = 2
        prefix_length = 7
        sym_spell = SymSpell(edit_distance_max, prefix_length)
        sym_spell.load_dictionary(self.dictionary_path, 0, 1)
        sym_spell.save_pickle(pickle_path)

        sym_spell_2 = SymSpell(edit_distance_max, prefix_length)
        sym_spell_2.load_pickle(pickle_path)
        self.assertEqual(sym_spell.deletes, sym_spell_2.deletes)
        self.assertEqual(sym_spell.words, sym_spell_2.words)
        self.assertEqual(sym_spell._max_length, sym_spell_2._max_length)
        os.remove(pickle_path)

    def test_pickle_invalid(self):
        pickle_path = os.path.join(self.fortests_path, "dictionary.pickle")
        is_compressed = False
        edit_distance_max = 2
        prefix_length = 7
        sym_spell = SymSpell(edit_distance_max, prefix_length)

        pickle_data = {
            "deletes": {},
            "words": {},
            "max_length": 0,
            "data_version": -1
        }
        with open(pickle_path, "wb") as f:
            pickle.dump(pickle_data, f)
        self.assertFalse(sym_spell.load_pickle(pickle_path, is_compressed))
        os.remove(pickle_path)

        pickle_data = {
            "deletes": {},
            "words": {},
            "max_length": 0
        }
        with open(pickle_path, "wb") as f:
            pickle.dump(pickle_data, f)
        self.assertFalse(sym_spell.load_pickle(pickle_path, is_compressed))
        os.remove(pickle_path)

    def test_delete_dictionary_entry(self):
        sym_spell = SymSpell()
        sym_spell.create_dictionary_entry("stea", 1)
        sym_spell.create_dictionary_entry("steama", 2)
        sym_spell.create_dictionary_entry("steem", 3)

        result = sym_spell.lookup("steama", Verbosity.TOP, 2)
        self.assertEqual(1, len(result))
        self.assertEqual("steama", result[0].term)
        self.assertEqual(len("steama"), sym_spell._max_length)

        self.assertTrue(sym_spell.delete_dictionary_entry("steama"))
        self.assertFalse("steama" in sym_spell.words)
        self.assertEqual(len("steem"), sym_spell._max_length)
        result = sym_spell.lookup("steama", Verbosity.TOP, 2)
        self.assertEqual(1, len(result))
        self.assertEqual("steem", result[0].term)

        self.assertTrue(sym_spell.delete_dictionary_entry("stea"))
        self.assertFalse("stea" in sym_spell.words)
        self.assertEqual(len("steem"), sym_spell._max_length)
        result = sym_spell.lookup("steama", Verbosity.TOP, 2)
        self.assertEqual(1, len(result))
        self.assertEqual("steem", result[0].term)

    def test_delete_dictionary_entry_invalid_word(self):
        sym_spell = SymSpell()
        sym_spell.create_dictionary_entry("stea", 1)
        sym_spell.create_dictionary_entry("steama", 2)
        sym_spell.create_dictionary_entry("steem", 3)

        result = sym_spell.lookup("steama", Verbosity.TOP, 2)
        self.assertEqual(1, len(result))
        self.assertEqual("steama", result[0].term)
        self.assertEqual(len("steama"), sym_spell._max_length)

        self.assertFalse(sym_spell.delete_dictionary_entry("steamab"))
        result = sym_spell.lookup("steama", Verbosity.TOP, 2)
        self.assertEqual(1, len(result))
        self.assertEqual("steama", result[0].term)
        self.assertEqual(len("steama"), sym_spell._max_length)

    def test_lookup_transfer_casing(self):
        sym_spell = SymSpell()
        sym_spell.create_dictionary_entry("steam", 4)
        result = sym_spell.lookup("Stream", Verbosity.TOP, 2,
                                  transfer_casing=True)
        self.assertEqual("Steam", result[0].term)

        sym_spell = SymSpell()
        sym_spell.create_dictionary_entry("steam", 4)
        result = sym_spell.lookup("StreaM", Verbosity.TOP, 2,
                                  transfer_casing=True)
        self.assertEqual("SteaM", result[0].term)

        sym_spell = SymSpell()
        sym_spell.create_dictionary_entry("steam", 4)
        result = sym_spell.lookup("STREAM", Verbosity.TOP, 2,
                                  transfer_casing=True)
        self.assertEqual("STEAM", result[0].term)

        sym_spell = SymSpell()
        sym_spell.create_dictionary_entry("i", 4)
        result = sym_spell.lookup("I", Verbosity.TOP, 2,
                                  transfer_casing=True)
        self.assertEqual("I", result[0].term)

    def test_lookup_compound_transfer_casing(self):
        edit_distance_max = 2
        prefix_length = 7
        sym_spell = SymSpell(edit_distance_max, prefix_length)
        sym_spell.load_dictionary(self.dictionary_path, 0, 1)
        sym_spell.load_bigram_dictionary(self.bigram_path, 0, 2)

        typo = ("Whereis th elove hehaD Dated forImuch of thepast who "
                "couqdn'tread in sixthgrade AND ins pired him")
        correction = ("Where is the love he haD Dated for much of the past "
                      "who couldn't read in sixth grade AND inspired him")

        results = sym_spell.lookup_compound(typo, edit_distance_max,
                                            transfer_casing=True)
        self.assertEqual(correction, results[0].term)

    def test_lookup_compound_transfer_casing_no_bigram(self):
        edit_distance_max = 2
        prefix_length = 7
        sym_spell = SymSpell(edit_distance_max, prefix_length)
        sym_spell.load_dictionary(self.dictionary_path, 0, 1)

        typo = ("Whereis th elove hehaD Dated forImuch of thepast who "
                "couqdn'tread in sixthgrade AND ins pired him")
        correction = ("Whereas the love heaD Dated for much of the past "
                      "who couldn't read in sixth grade AND inspired him")

        results = sym_spell.lookup_compound(typo, edit_distance_max,
                                            transfer_casing=True)
        self.assertEqual(correction, results[0].term)

    def test_lookup_compound_transfer_casing_ignore_nonwords(self):
        edit_distance_max = 2
        prefix_length = 7
        sym_spell = SymSpell(edit_distance_max, prefix_length)
        sym_spell.load_dictionary(self.dictionary_path, 0, 1)
        sym_spell.load_bigram_dictionary(self.bigram_path, 0, 2)

        typo = ("Whereis th elove hehaD Dated FOREEVER forImuch of thepast who"
                " couqdn'tread in sixthgrade AND ins pired him")
        correction = ("Where is the love he haD Dated FOREEVER for much of the"
                      " past who couldn't read in sixth grade AND inspired "
                      "him")

        results = sym_spell.lookup_compound(typo, edit_distance_max,
                                            ignore_non_words=True,
                                            transfer_casing=True)
        self.assertEqual(correction, results[0].term)

    def test_lookup_compound_transfer_casing_ignore_nonwords_no_bigram(self):
        edit_distance_max = 2
        prefix_length = 7
        sym_spell = SymSpell(edit_distance_max, prefix_length)
        sym_spell.load_dictionary(self.dictionary_path, 0, 1)

        typo = ("Whereis th elove hehaD Dated FOREEVER forImuch of thepast who"
                " couqdn'tread in sixthgrade AND ins pired him")
        correction = ("Whereas the love heaD Dated FOREEVER for much of the"
                      " past who couldn't read in sixth grade AND inspired "
                      "him")

        results = sym_spell.lookup_compound(typo, edit_distance_max,
                                            ignore_non_words=True,
                                            transfer_casing=True)
        self.assertEqual(correction, results[0].term)

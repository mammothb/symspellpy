import inspect
from os import pardir
import os.path
import sys
import unittest

import pytest

from symspellpy import SymSpell, Verbosity
from symspellpy.symspellpy import SuggestItem

class TestSymSpellPy(unittest.TestCase):
    def runTest(self):
        print('\nRunning %s' % self.__class__.__name__)
        self.test_negative_initial_capacity()
        self.test_negative_max_dictionary_edit_distance()
        self.test_invalid_prefix_length()
        self.test_negative_count_threshold()
        self.test_invalide_compact_level()
        self.test_create_dictionary_entry_negative_count()
        self.test_create_dictionary_entry_below_threshold()
        self.test_words_with_shared_prefix_should_retain_counts()
        self.test_add_additional_counts_should_not_add_word_again()
        self.test_add_additional_counts_should_increase_count()
        self.test_add_additional_counts_should_not_overflow()
        self.test_verbosity_should_control_lookup_results()
        self.test_lookup_should_return_most_frequent()
        self.test_lookup_should_find_exact_match()
        self.test_lookup_should_not_return_non_word_delete()
        self.test_lookup_should_not_return_low_count_word()
        self.test_lookup_should_not_return_low_count_word_that_are_also_delete_word()
        self.test_lookup_max_edit_distance_too_large()
        self.test_lookup_include_unknown()
        self.test_load_dictionary_invalid_path()
        self.test_load_dictionary_bad_dictionary()
        self.test_lookup_should_replicate_noisy_results()
        self.test_lookup_compound()
        self.test_lookup_compound_only_combi()
        self.test_lookup_compound_replaced_words()
        self.test_lookup_compound_ignore_non_words()
        self.test_load_dictionary_encoding()
        self.test_word_segmentation()
        self.test_word_segmentation_ignore_token()
        self.test_word_segmentation_with_arguments()

    def test_negative_initial_capacity(self):
        print('  - %s' % inspect.stack()[0][3])
        with pytest.raises(ValueError) as excinfo:
            __ = SymSpell(-16, 1, 3)
        self.assertEqual("initial_capacity cannot be negative",
                         str(excinfo.value))

    def test_negative_max_dictionary_edit_distance(self):
        print('  - %s' % inspect.stack()[0][3])
        with pytest.raises(ValueError) as excinfo:
            __ = SymSpell(16, -1, 3)
        self.assertEqual("max_dictionary_edit_distance cannot be negative",
                         str(excinfo.value))

    def test_invalid_prefix_length(self):
        print('  - %s' % inspect.stack()[0][3])
        # prefix_length < 1
        with pytest.raises(ValueError) as excinfo:
            __ = SymSpell(16, 1, 0)
        self.assertEqual("prefix_length cannot be less than 1 or "
                         "smaller than max_dictionary_edit_distance",
                         str(excinfo.value))

        with pytest.raises(ValueError) as excinfo:
            __ = SymSpell(16, 1, -1)
        self.assertEqual("prefix_length cannot be less than 1 or "
                         "smaller than max_dictionary_edit_distance",
                         str(excinfo.value))

        # prefix_length <= max_dictionary_edit_distance
        with pytest.raises(ValueError) as excinfo:
            __ = SymSpell(16, 2, 2)
        self.assertEqual("prefix_length cannot be less than 1 or "
                         "smaller than max_dictionary_edit_distance",
                         str(excinfo.value))

    def test_negative_count_threshold(self):
        print('  - %s' % inspect.stack()[0][3])
        with pytest.raises(ValueError) as excinfo:
            __ = SymSpell(16, 1, 3, -1)
        self.assertEqual("count_threshold cannot be negative",
                         str(excinfo.value))

    def test_invalide_compact_level(self):
        print('  - %s' % inspect.stack()[0][3])
        # compact_level < 0
        with pytest.raises(ValueError) as excinfo:
            __ = SymSpell(16, 1, 3, 1, -1)
        self.assertEqual("compact_level must be between 0 and 16",
                         str(excinfo.value))

        # compact_level < 0
        with pytest.raises(ValueError) as excinfo:
            __ = SymSpell(16, 1, 3, 1, 17)
        self.assertEqual("compact_level must be between 0 and 16",
                         str(excinfo.value))

    def test_create_dictionary_entry_negative_count(self):
        print('  - %s' % inspect.stack()[0][3])
        sym_spell = SymSpell(16, 1, 3)
        self.assertEqual(False, sym_spell.create_dictionary_entry("pipe", 0))
        self.assertEqual(False,
                         sym_spell.create_dictionary_entry("pipe", -1))

        sym_spell = SymSpell(16, 1, 3, count_threshold=0)
        self.assertEqual(True, sym_spell.create_dictionary_entry("pipe", 0))

    def test_create_dictionary_entry_below_threshold(self):
        print('  - %s' % inspect.stack()[0][3])
        sym_spell = SymSpell(16, 1, 3, count_threshold=10)
        sym_spell.create_dictionary_entry("pipe", 4)
        self.assertEqual(1, len(sym_spell.below_threshold_words))
        self.assertEqual(4, sym_spell.below_threshold_words["pipe"])

        sym_spell.create_dictionary_entry("pipe", 4)
        self.assertEqual(1, len(sym_spell.below_threshold_words))
        self.assertEqual(8, sym_spell.below_threshold_words["pipe"])

        sym_spell.create_dictionary_entry("pipe", 4)
        self.assertEqual(0, len(sym_spell.below_threshold_words))

    def test_deletes(self):
        print('  - %s' % inspect.stack()[0][3])
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
        print('  - %s' % inspect.stack()[0][3])
        sym_spell = SymSpell(16, 1, 3)
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
        print('  - %s' % inspect.stack()[0][3])
        sym_spell = SymSpell()
        word = "hello"
        sym_spell.create_dictionary_entry(word, 11)
        self.assertEqual(1, sym_spell.word_count)

        sym_spell.create_dictionary_entry(word, 3)
        self.assertEqual(1, sym_spell.word_count)

    def test_add_additional_counts_should_increase_count(self):
        print('  - %s' % inspect.stack()[0][3])
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
        print('  - %s' % inspect.stack()[0][3])
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
        print('  - %s' % inspect.stack()[0][3])
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
        print('  - %s' % inspect.stack()[0][3])
        sym_spell = SymSpell()
        sym_spell.create_dictionary_entry("steama", 4)
        sym_spell.create_dictionary_entry("steamb", 6)
        sym_spell.create_dictionary_entry("steamc", 2)
        result = sym_spell.lookup("stream", Verbosity.TOP, 2)
        self.assertEqual(1, len(result))
        self.assertEqual("steamb", result[0].term)
        self.assertEqual(6, result[0].count)

    def test_lookup_should_find_exact_match(self):
        print('  - %s' % inspect.stack()[0][3])
        sym_spell = SymSpell()
        sym_spell.create_dictionary_entry("steama", 4)
        sym_spell.create_dictionary_entry("steamb", 6)
        sym_spell.create_dictionary_entry("steamc", 2)
        result = sym_spell.lookup("streama", Verbosity.TOP, 2)
        self.assertEqual(1, len(result))
        self.assertEqual("steama", result[0].term)

    def test_lookup_should_not_return_non_word_delete(self):
        print('  - %s' % inspect.stack()[0][3])
        sym_spell = SymSpell(16, 2, 7, 10)
        sym_spell.create_dictionary_entry("pawn", 10)
        result = sym_spell.lookup("paw", Verbosity.TOP, 0)
        self.assertEqual(0, len(result))
        result = sym_spell.lookup("awn", Verbosity.TOP, 0)
        self.assertEqual(0, len(result))

    def test_lookup_should_not_return_low_count_word(self):
        print('  - %s' % inspect.stack()[0][3])
        sym_spell = SymSpell(16, 2, 7, 10)
        sym_spell.create_dictionary_entry("pawn", 1)
        result = sym_spell.lookup("pawn", Verbosity.TOP, 0)
        self.assertEqual(0, len(result))

    def test_lookup_should_not_return_low_count_word_that_are_also_delete_word(self):
        print('  - %s' % inspect.stack()[0][3])
        sym_spell = SymSpell(16, 2, 7, 10)
        sym_spell.create_dictionary_entry("flame", 20)
        sym_spell.create_dictionary_entry("flam", 1)
        result = sym_spell.lookup("flam", Verbosity.TOP, 0)
        self.assertEqual(0, len(result))

    def test_lookup_max_edit_distance_too_large(self):
        print('  - %s' % inspect.stack()[0][3])
        sym_spell = SymSpell(16, 2, 7, 10)
        sym_spell.create_dictionary_entry("flame", 20)
        sym_spell.create_dictionary_entry("flam", 1)
        with pytest.raises(ValueError) as excinfo:
            __ = sym_spell.lookup("flam", Verbosity.TOP, 3)
        self.assertEqual("Distance too large", str(excinfo.value))

    def test_lookup_include_unknown(self):
        print('  - %s' % inspect.stack()[0][3])
        sym_spell = SymSpell(16, 2, 7, 10)
        sym_spell.create_dictionary_entry("flame", 20)
        sym_spell.create_dictionary_entry("flam", 1)
        result = sym_spell.lookup("qwer", Verbosity.TOP, 0, True)
        self.assertEqual(1, len(result))
        self.assertEqual("qwer", result[0].term)

    def test_load_dictionary_invalid_path(self):
        print('  - %s' % inspect.stack()[0][3])
        edit_distance_max = 2
        prefix_length = 7
        sym_spell = SymSpell(83000, edit_distance_max, prefix_length)
        self.assertEqual(False, sym_spell.load_dictionary(
            "invalid/dictionary/path.txt", 0, 1))

    def test_load_dictionary_bad_dictionary(self):
        print('  - %s' % inspect.stack()[0][3])
        cwd = os.path.realpath(os.path.dirname(__file__))
        dictionary_path = os.path.join(cwd, "fortests", "bad_dict.txt")
        edit_distance_max = 2
        prefix_length = 7
        sym_spell = SymSpell(83000, edit_distance_max, prefix_length)
        self.assertEqual(True, sym_spell.load_dictionary(
            dictionary_path, 0, 1))
        self.assertEqual(2, sym_spell.word_count)
        self.assertEqual(10, sym_spell.words["asdf"])
        self.assertEqual(12, sym_spell.words["sdfg"])

    def test_lookup_should_replicate_noisy_results(self):
        print('  - %s' % inspect.stack()[0][3])
        cwd = os.path.realpath(os.path.dirname(__file__))
        dictionary_path = os.path.realpath(os.path.join(
            cwd, pardir, "symspellpy", "frequency_dictionary_en_82_765.txt"))
        query_path = os.path.join(cwd, "fortests", "noisy_query_en_1000.txt")

        edit_distance_max = 2
        prefix_length = 7
        verbosity = Verbosity.CLOSEST
        sym_spell = SymSpell(83000, edit_distance_max, prefix_length)
        sym_spell.load_dictionary(dictionary_path, 0, 1)

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
        print('  - %s' % inspect.stack()[0][3])
        cwd = os.path.realpath(os.path.dirname(__file__))
        dictionary_path = os.path.realpath(os.path.join(
            cwd, pardir, "symspellpy", "frequency_dictionary_en_82_765.txt"))

        edit_distance_max = 2
        prefix_length = 7
        sym_spell = SymSpell(83000, edit_distance_max, prefix_length)
        sym_spell.load_dictionary(dictionary_path, 0, 1)

        typo = ("whereis th elove hehad dated forImuch of thepast who "
                "couqdn'tread in sixthgrade and ins pired him")
        correction = ("where is the love he had dated for much of the past "
                      "who couldn't read in sixth grade and inspired him")
        results = sym_spell.lookup_compound(typo, edit_distance_max)
        self.assertEqual(1, len(results))
        self.assertEqual(correction, results[0].term)
        self.assertEqual(9, results[0].distance)
        self.assertEqual(300000, results[0].count)

        typo = "in te dhird qarter oflast jear he hadlearned ofca sekretplan"
        correction = ("in the third quarter of last year he had learned of a "
                      "secret plan")
        results = sym_spell.lookup_compound(typo, edit_distance_max)
        self.assertEqual(1, len(results))
        self.assertEqual(correction, results[0].term)
        self.assertEqual(9, results[0].distance)
        self.assertEqual(23121323, results[0].count)

        typo = ("the bigjest playrs in te strogsommer film slatew ith plety "
                "of funn")
        correction = ("the biggest players in the strong summer film slate "
                      "with plenty of fun")
        results = sym_spell.lookup_compound(typo, edit_distance_max)
        self.assertEqual(1, len(results))
        self.assertEqual(correction, results[0].term)
        self.assertEqual(9, results[0].distance)
        self.assertEqual(3813904, results[0].count)

        typo = ("Can yu readthis messa ge despite thehorible sppelingmsitakes")
        correction = ("can you read this message despite the horrible "
                      "spelling mistakes")
        results = sym_spell.lookup_compound(typo, edit_distance_max)
        self.assertEqual(1, len(results))
        self.assertEqual(correction, results[0].term)
        self.assertEqual(10, results[0].distance)
        self.assertEqual(6218089, results[0].count)

    def test_lookup_compound_only_combi(self):
        print('  - %s' % inspect.stack()[0][3])
        edit_distance_max = 2
        prefix_length = 7
        sym_spell = SymSpell(16, edit_distance_max, prefix_length)
        sym_spell.create_dictionary_entry("steam", 1)
        sym_spell.create_dictionary_entry("machine", 1)

        typo = "ste am machie"
        correction = "steam machine"
        results = sym_spell.lookup_compound(typo, edit_distance_max)
        self.assertEqual(1, len(results))
        self.assertEqual(correction, results[0].term)

    def test_lookup_compound_no_suggestion(self):
        print('  - %s' % inspect.stack()[0][3])
        edit_distance_max = 2
        prefix_length = 7
        sym_spell = SymSpell(16, edit_distance_max, prefix_length)
        sym_spell.create_dictionary_entry("steam", 1)
        sym_spell.create_dictionary_entry("machine", 1)

        typo = "qwer erty ytui a"
        results = sym_spell.lookup_compound(typo, edit_distance_max)
        self.assertEqual(1, len(results))
        self.assertEqual(typo, results[0].term)

    def test_lookup_compound_replaced_words(self):
        print('  - %s' % inspect.stack()[0][3])
        cwd = os.path.realpath(os.path.dirname(__file__))
        dictionary_path = os.path.realpath(os.path.join(
            cwd, pardir, "symspellpy", "frequency_dictionary_en_82_765.txt"))

        edit_distance_max = 2
        prefix_length = 7
        sym_spell = SymSpell(83000, edit_distance_max, prefix_length)
        sym_spell.load_dictionary(dictionary_path, 0, 1)

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

    def test_lookup_compound_ignore_non_words(self):
        print('  - %s' % inspect.stack()[0][3])
        cwd = os.path.realpath(os.path.dirname(__file__))
        dictionary_path = os.path.realpath(os.path.join(
            cwd, pardir, "symspellpy", "frequency_dictionary_en_82_765.txt"))

        edit_distance_max = 2
        prefix_length = 7
        sym_spell = SymSpell(83000, edit_distance_max, prefix_length)
        sym_spell.load_dictionary(dictionary_path, 0, 1)

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

    def test_load_dictionary_encoding(self):
        print('  - %s' % inspect.stack()[0][3])
        cwd = os.path.realpath(os.path.dirname(__file__))
        dictionary_path = os.path.realpath(os.path.join(
            cwd, "fortests", "non_en_dict.txt"))

        edit_distance_max = 2
        prefix_length = 7
        sym_spell = SymSpell(83000, edit_distance_max, prefix_length)
        sym_spell.load_dictionary(dictionary_path, 0, 1, encoding="utf-8")

        result = sym_spell.lookup("АБ", Verbosity.TOP, 2)
        self.assertEqual(1, len(result))
        self.assertEqual("АБИ", result[0].term)

    def test_word_segmentation(self):
        print('  - %s' % inspect.stack()[0][3])
        cwd = os.path.realpath(os.path.dirname(__file__))
        dictionary_path = os.path.realpath(os.path.join(
            cwd, pardir, "symspellpy", "frequency_dictionary_en_82_765.txt"))

        edit_distance_max = 0
        prefix_length = 7
        sym_spell = SymSpell(83000, edit_distance_max, prefix_length)
        sym_spell.load_dictionary(dictionary_path, 0, 1)

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
        print('  - %s' % inspect.stack()[0][3])
        cwd = os.path.realpath(os.path.dirname(__file__))
        dictionary_path = os.path.realpath(os.path.join(
            cwd, pardir, "symspellpy", "frequency_dictionary_en_82_765.txt"))

        edit_distance_max = 2
        prefix_length = 7
        sym_spell = SymSpell(83000, edit_distance_max, prefix_length)
        sym_spell.load_dictionary(dictionary_path, 0, 1)

        typo = "24th december"
        result = sym_spell.word_segmentation(typo, ignore_token=r"\d{2}\w*\b")
        self.assertEqual(typo, result.corrected_string)

    def test_word_segmentation_with_arguments(self):
        print('  - %s' % inspect.stack()[0][3])
        cwd = os.path.realpath(os.path.dirname(__file__))
        dictionary_path = os.path.realpath(os.path.join(
            cwd, pardir, "symspellpy", "frequency_dictionary_en_82_765.txt"))

        edit_distance_max = 0
        prefix_length = 7
        sym_spell = SymSpell(83000, edit_distance_max, prefix_length)
        sym_spell.load_dictionary(dictionary_path, 0, 1)

        typo = "thequickbrownfoxjumpsoverthelazydog"
        correction = "the quick brown fox jumps over the lazy dog"
        result = sym_spell.word_segmentation(typo, edit_distance_max, 11)
        self.assertEqual(correction, result.corrected_string)

        typo = "itwasabrightcolddayinaprilandtheclockswerestrikingthirteen"
        correction = ("it was a bright cold day in april and the clocks "
                      "were striking thirteen")
        result = sym_spell.word_segmentation(typo, edit_distance_max, 11)
        self.assertEqual(correction, result[1])

        typo = (" itwasthebestoftimesitwastheworstoftimesitwastheageofwisdom"
                "itwastheageoffoolishness")
        correction = ("it was the best of times it was the worst of times "
                      "it was the age of wisdom it was the age of foolishness")
        result = sym_spell.word_segmentation(typo, edit_distance_max, 11)
        self.assertEqual(correction, result[1])

    def test_suggest_item(self):
        print('  - %s' % inspect.stack()[0][3])
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

if __name__ == "__main__":
    runner = unittest.TextTestRunner()
    suite = unittest.TestSuite()
    suite.addTest(TestSymSpellPy())
    runner.run(suite)

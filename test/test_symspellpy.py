import inspect
from os import pardir, path
import sys
import unittest

sys.path.append(path.realpath(path.join(__file__, *(path.pardir,) * 2)))
from symspellpy.symspellpy import SymSpell, Verbosity

class TestSymSpellPy(unittest.TestCase):
    def runTest(self):
        print('\nRunning %s' % self.__class__.__name__)
        # self.test_words_with_shared_prefix_should_retain_counts()
        # self.test_add_additional_counts_should_not_add_word_again()
        # self.test_add_additional_counts_should_increase_count()
        # self.test_add_additional_counts_should_not_overflow()
        # self.test_verbosity_should_control_lookup_results()
        # self.test_lookup_should_return_most_frequent()
        # self.test_lookup_should_find_exact_match()
        # self.test_lookup_should_not_return_non_word_delete()
        # self.test_lookup_should_not_return_low_count_word()
        # self.test_lookup_should_not_return_low_count_word_that_are_also_delete_word()
        self.test_lookup_should_replicate_noisy_results()

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

    def test_lookup_should_replicate_noisy_results(self):
        print('  - %s' % inspect.stack()[0][3])
        cwd = path.realpath(path.dirname(__file__))
        dictionary_path = path.realpath(path.join(
            cwd, pardir, "symspellpy", "frequency_dictionary_en_82_765.txt"))
        query_path = path.join(cwd, "fortests", "noisy_query_en_1000.txt")

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

if __name__ == "__main__":
    runner = unittest.TextTestRunner()
    suite = unittest.TestSuite()
    suite.addTest(TestSymSpellPy())
    runner.run(suite)

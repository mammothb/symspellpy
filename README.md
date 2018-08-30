symspellpy <br>
[![Build Status](https://travis-ci.com/mammothb/symspellpy.svg?branch=master)](https://travis-ci.com/mammothb/symspellpy)
[![codecov](https://codecov.io/gh/mammothb/symspellpy/branch/master/graph/badge.svg)](https://codecov.io/gh/mammothb/symspellpy)
========

symspellpy is a Python port of [SymSpell](https://github.com/wolfgarbe/SymSpell) v6.3, which provides much higher speed and lower memory consumption. Unit tests
from the original project are implemented to ensure the accuracy of the port.

Please note that the port has not been optimized for speed.

Usage
========
### Installing the  ``symspellpy`` module
```pip install -U symspellpy```

### Copying the frequency dictionary to your project
Copy ``frequency_dictionary_en_82_765.txt`` (found in the inner ``symspellpy`` directory) to your project directory so you end up with the following layout:
```
project_dir
  +-frequency_dictionary_en_82_765.txt
  \-project.py
```

### Sample usage
Using ``project.py`` (code is more verbose than required to allow explanation of method arguments)
```python
import os

from symspellpy.symspellpy import SymSpell, Verbosity  # import the module

def main():
    # create object
    initial_capacity = 83000
    # maximum edit distance per dictionary precalculation
    max_edit_distance_dictionary = 2
    prefix_length = 7
    sym_spell = SymSpell(initial_capacity, max_edit_distance_dictionary,
                         prefix_length)
    # load dictionary
    dictionary_path = os.path.join(os.path.dirname(__file__),
                                   "frequency_dictionary_en_82_765.txt")
    term_index = 0  # column of the term in the dictionary text file
    count_index = 1  # column of the term frequency in the dictionary text file
    if not sym_spell.load_dictionary(dictionary_path, term_index, count_index):
        print("Dictionary file not found")
        return

    # lookup suggestions for single-word input strings
    input_term = "memebers"  # misspelling of "members"
    # max edit distance per lookup
    # (max_edit_distance_lookup <= max_edit_distance_dictionary)
    max_edit_distance_lookup = 2
    suggestion_verbosity = Verbosity.CLOSEST  # TOP, CLOSEST, ALL
    suggestions = sym_spell.lookup(input_term, suggestion_verbosity,
                                   max_edit_distance_lookup)
    # display suggestion term, term frequency, and edit distance
    for suggestion in suggestions:
        print("{}, {}, {}".format(suggestion.term, suggestion.count,
                                  suggestion.distance))

    # lookup suggestions for multi-word input strings (supports compound
    # splitting & merging)
    input_term = ("whereis th elove hehad dated forImuch of thepast who "
                  "couqdn'tread in sixtgrade and ins pired him")
    # max edit distance per lookup (per single word, not per whole input string)
    max_edit_distance_lookup = 2
    suggestions = sym_spell.lookup_compound(input_term,
                                            max_edit_distance_lookup)
    # display suggestion term, edit distance, and term frequency
    for suggestion in suggestions:
        print("{}, {}, {}".format(suggestion.term, suggestion.count,
                                  suggestion.distance))

if __name__ == "__main__":
    main()
```
##### Expected output:
``members, 226656153, 1``<br><br>
``where is the love he had dated for much of the past who couldn't read in six grade and inspired him, 300000, 10``

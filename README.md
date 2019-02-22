symspellpy <br>
[![Build Status](https://travis-ci.com/mammothb/symspellpy.svg?branch=master)](https://travis-ci.com/mammothb/symspellpy)
[![Documentation Status](https://readthedocs.org/projects/symspellpy/badge/?version=latest)](https://symspellpy.readthedocs.io/en/latest/?badge=latest)
[![codecov](https://codecov.io/gh/mammothb/symspellpy/branch/master/graph/badge.svg)](https://codecov.io/gh/mammothb/symspellpy)
========

symspellpy is a Python port of [SymSpell](https://github.com/wolfgarbe/SymSpell) v6.3, which provides much higher speed and lower memory consumption. Unit tests
from the original project are implemented to ensure the accuracy of the port.

Please note that the port has not been optimized for speed.

Usage
========
### Installing the `symspellpy` module
```pip install -U symspellpy```

### Copying the frequency dictionary to your project
Copy `frequency_dictionary_en_82_765.txt` (found in the inner `symspellpy`
directory) to your project directory so you end up with the following layout:
```
project_dir
  +-frequency_dictionary_en_82_765.txt
  \-project.py
```

### Adding new terms
  - Use `load_dictionary(corpus=<path/to/dictionary.txt>, <term_index>,<count_index>)`. `dictionary.txt` should contain:
```
<term> <count>
<term> <count>
...
<term> <count>
```
with `term_index` indicating the column number of terms and `count_index` indicating the column number of counts/frequency.
  - Append `<term> <count>` to the provided `frequency_dictionary_en_82_765.txt`
  - Use the method `create_dictionary_entry(key=<term>, count=<count>)`

### Sample usage (`create_dictionary`)
```python
import os

from symspellpy.symspellpy import SymSpell  # import the module

def main():
    # maximum edit distance per dictionary precalculation
    max_edit_distance_dictionary = 2
    prefix_length = 7
    # create object
    sym_spell = SymSpell(max_edit_distance_dictionary, prefix_length)
    
    # create dictionary using corpus.txt
    if not sym_spell.create_dictionary(<path/to/corpus.txt>):
        print("Corpus file not found")
        return

    for key, count in sym_spell.words.items():
        print("{} {}".format(key, count))

if __name__ == "__main__":
    main()
```
`corpus.txt` should contain:
```
abc abc-def abc_def abc'def abc qwe qwe1 1qwe q1we 1234 1234
```
Expected output:
```
abc 4
def 2
abc'def 1
qwe 1
qwe1 1
1qwe 1
q1we 1
1234 2
```

### Sample usage (`lookup` and `lookup_compound`)
Using `project.py` (code is more verbose than required to allow explanation of method arguments)
```python
import os

from symspellpy.symspellpy import SymSpell, Verbosity  # import the module

def main():
    # maximum edit distance per dictionary precalculation
    max_edit_distance_dictionary = 2
    prefix_length = 7
    # create object
    sym_spell = SymSpell(max_edit_distance_dictionary, prefix_length)
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
        print("{}, {}, {}".format(suggestion.term, suggestion.distance,
                                  suggestion.count))

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
        print("{}, {}, {}".format(suggestion.term, suggestion.distance,
                                  suggestion.count))

if __name__ == "__main__":
    main()
```
##### Expected output:
`members, 1, 226656153`<br><br>
`where is the love he had dated for much of the past who couldn't read in six grade and inspired him, 9, 300000`

### Sample usage (`word_segmentation`)
Using `project.py` (code is more verbose than required to allow explanation of
method arguments)
```python
import os

from symspellpy.symspellpy import SymSpell  # import the module

def main():
    # maximum edit distance per dictionary precalculation
    max_edit_distance_dictionary = 0
    prefix_length = 7
    # create object
    sym_spell = SymSpell(max_edit_distance_dictionary, prefix_length)
    # load dictionary
    dictionary_path = os.path.join(os.path.dirname(__file__),
                                   "frequency_dictionary_en_82_765.txt")
    term_index = 0  # column of the term in the dictionary text file
    count_index = 1  # column of the term frequency in the dictionary text file
    if not sym_spell.load_dictionary(dictionary_path, term_index, count_index):
        print("Dictionary file not found")
        return

    # a sentence without any spaces
    input_term = "thequickbrownfoxjumpsoverthelazydog"
    
    result = sym_spell.word_segmentation(input_term)
    # display suggestion term, term frequency, and edit distance
    print("{}, {}, {}".format(result.corrected_string, result.distance_sum,
                              result.log_prob_sum))

if __name__ == "__main__":
    main()
```
##### Expected output:
`the quick brown fox jumps over the lazy dog 8 -34.491167981910635`

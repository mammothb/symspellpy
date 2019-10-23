CHANGELOG <br>
==============

## 6.5.2 (2019-10-23)
---------------------
- Modified `load_bigram_dictionary` to allow dictionary entries to be split
into only 2 parts when using a custom separator
- Added dictionary files to wheels so `pkg_resources` could be used to access
them

## 6.5.1 (2019-10-08)
---------------------
- Added `separator` argument to allow user to choose custom separator for `load_dictionary`

## 6.5.0 (2019-09-21)
---------------------
- Added `load_bigram_dictionary` and bigram dictionary `frequency_bigramdictionary_en_243_342.txt`
- Updated `lookup_compound` algorithm
- Added `Levenshtein` to compute edit distance
- Added `save_pickle_stream` and `load_pickle_stream` to save/load SymSpell data alongside other structure (contribution by [marcoffee](https://github.com/marcoffee))

## 6.3.9 (2019-08-06)
---------------------
- Added `transfer_casing` to `lookup` and `lookup_compound`
- Fixed prefix length check in `_edits_prefix`

## 6.3.8 (2019-03-21)
---------------------
- Implemented `delete_dictionary_entry`
- Improved performance by using python builtin hashing
- Added versioning of the pickle

## 6.3.7 (2019-02-18)
---------------------
- Fixed `include_unknown` in `lookup`
- Removed unused `initial_capacity` argument
- Improved `_get_str_hash` performance
- Implemented `save_pickle` and `load_pickle` to avoid having to create the
dictionary every time

## 6.3.6 (2019-02-11)
---------------------
- Added `create_dictionary()` feature

## 6.3.5 (2019-01-14)
---------------------
- Fixed `lookup_compound()` to return the correct `distance`

## 6.3.4 (2019-01-04)
---------------------
- Added `<self._replaced_words = dict()>` to track number of misspelled words
- Added `ignore_token` to `word_segmentation()` to ignore words with regular expression

## 6.3.3 (2018-12-05)
---------------------
- Added `word_segmentation()` feature

## 6.3.2 (2018-10-23)
---------------------
- Added `encoding` option to `load_dictionary()`

## 6.3.1 (2018-08-30)
---------------------
- Create a package for `symspellpy`

## 6.3.0 (2018-08-13)
---------------------
- Ported [SymSpell](https://github.com/wolfgarbe/SymSpell) v6.3
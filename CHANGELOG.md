CHANGELOG <br>
==============

## 6.7.8 (2024-08-31)
- Handle encoding errors [#149](https://github.com/mammothb/symspellpy/pull/149)
- Bump supported Python version to 3.8 - 3.12 [#151](https://github.com/mammothb/symspellpy/pull/151)
- Remove numpy dependency [#156](https://github.com/mammothb/symspellpy/pull/156)
- Feature: distance comparer interface [#159](https://github.com/mammothb/symspellpy/pull/159)

## 6.7.7 (2022-10-24)
- Remove support for Python 3.6
- Use compiled regex expression in `create_dictionary()` ([#129](https://github.com/mammothb/symspellpy/pull/129))
- Configure module logger instead of modifying root logger ([#132](https://github.com/mammothb/symspellpy/pull/132), [#133](https://github.com/mammothb/symspellpy/pull/133))

## 6.7.6 (2021-12-19)
- Fix suggestion `count` in `lookup_compound` when `ignore_words=True` ([#108](https://github.com/mammothb/symspellpy/pull/108))
- Log error message when loading dictionary fails ([#109](https://github.com/mammothb/symspellpy/pull/109))

## 6.7.5 (2021-12-02)
- Fix `replaced_words` not being updated when best match is a combi (closes [#103](https://github.com/mammothb/symspellpy/issues/103))
- Implement a way to change the edit distance comparer algorightm via `distance_algorithm` property. Available values are found in [`DistanceAlgorithm`](https://symspellpy.readthedocs.io/en/latest/api/editdistance.html#symspellpy.editdistance.DistanceAlgorithm)

## 6.7.4 (2021-11-29)
- Update `editdistpy` dependency version
- Update `LevenshteinFast` and `DamerauOsaFast` to match the functionality of the `editdistpy` library

## 6.7.3 (2021-11-27)
- Update `editdistpy` dependency version

## 6.7.2 (2021-11-25)
- Fix typo of Dameruau to Damerau in various places. Can potentially break some setups that explicitly `_distance_algorithm`
- Implement fast distance comparers with [editdistpy](https://github.com/mammothb/editdistpy)
- Set `DamerauOsaFast` as the default distance comparer

## 6.7.1 (2021-11-21)
- Updated `frequency_dictionary_en_82_765.txt` dictionary with common contractions
- Added `_below_threshold_words`, `_bigrams`, `_count_threshold`, `_max_dictionary_edit_distance`, and `_prefix_length` when saving to pickle. (closes [#93](https://github.com/mammothb/symspellpy/issues/93))
- Implemented `to_bytes` and `from_bytes` options to save and load pickle with bytes string
- Updated data_version to 3
- Removed Python 3.4 and Python 3.5 support

## 6.7.0 (2020-08-28)
- Removed numpy dependency
- `word_segmentation` now retains/preserves case.
- `word_segmentation` now keeps punctuation or apostrophe adjacent to previous
word.
- `word_segmentation` now normalizes ligatures: "scientiﬁc" -> "scientific".
- `word_segmentation` now removes hyphens prior to word segmentation
(untested).
- American English word forms added to dictionary in addition to British
English e.g. favourable & favorable.

## 6.5.2 (2019-10-23)
- Modified `load_bigram_dictionary` to allow dictionary entries to be split
into only 2 parts when using a custom separator
- Added dictionary files to wheels so `pkg_resources` could be used to access
them

## 6.5.1 (2019-10-08)
- Added `separator` argument to allow user to choose custom separator for `load_dictionary`

## 6.5.0 (2019-09-21)
- Added `load_bigram_dictionary` and bigram dictionary `frequency_bigramdictionary_en_243_342.txt`
- Updated `lookup_compound` algorithm
- Added `Levenshtein` to compute edit distance
- Added `save_pickle_stream` and `load_pickle_stream` to save/load SymSpell data alongside other structure (contribution by [marcoffee](https://github.com/marcoffee))

## 6.3.9 (2019-08-06)
- Added `transfer_casing` to `lookup` and `lookup_compound`
- Fixed prefix length check in `_edits_prefix`

## 6.3.8 (2019-03-21)
- Implemented `delete_dictionary_entry`
- Improved performance by using python builtin hashing
- Added versioning of the pickle

## 6.3.7 (2019-02-18)
- Fixed `include_unknown` in `lookup`
- Removed unused `initial_capacity` argument
- Improved `_get_str_hash` performance
- Implemented `save_pickle` and `load_pickle` to avoid having to create the
dictionary every time

## 6.3.6 (2019-02-11)
- Added `create_dictionary()` feature

## 6.3.5 (2019-01-14)
- Fixed `lookup_compound()` to return the correct `distance`

## 6.3.4 (2019-01-04)
- Added `<self._replaced_words = dict()>` to track number of misspelled words
- Added `ignore_token` to `word_segmentation()` to ignore words with regular expression

## 6.3.3 (2018-12-05)
- Added `word_segmentation()` feature

## 6.3.2 (2018-10-23)
- Added `encoding` option to `load_dictionary()`

## 6.3.1 (2018-08-30)
- Create a package for `symspellpy`

## 6.3.0 (2018-08-13)
- Ported [SymSpell](https://github.com/wolfgarbe/SymSpell) v6.3

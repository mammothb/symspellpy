======
lookup
======

Basic usage
===========

.. code-block:: python
   :emphasize-lines: 15,16

   import pkg_resources
   from symspellpy import SymSpell, Verbosity

   sym_spell = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)
   dictionary_path = pkg_resources.resource_filename(
       "symspellpy", "frequency_dictionary_en_82_765.txt")
   # term_index is the column of the term and count_index is the
   # column of the term frequency
   sym_spell.load_dictionary(dictionary_path, term_index=0, count_index=1)

   # lookup suggestions for single-word input strings
   input_term = "memebers"  # misspelling of "members"
   # max edit distance per lookup
   # (max_edit_distance_lookup <= max_dictionary_edit_distance)
   suggestions = sym_spell.lookup(input_term, Verbosity.CLOSEST,
                                  max_edit_distance=2)
   # display suggestion term, term frequency, and edit distance
   for suggestion in suggestions:
       print(suggestion)

Output::

  members, 1, 226656153

Return original word if no correction within edit distance is found
===================================================================

.. code-block:: python
   :emphasize-lines: 15,16

   import pkg_resources
   from symspellpy import SymSpell, Verbosity

   sym_spell = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)
   dictionary_path = pkg_resources.resource_filename(
       "symspellpy", "frequency_dictionary_en_82_765.txt")
   # term_index is the column of the term and count_index is the
   # column of the term frequency
   sym_spell.load_dictionary(dictionary_path, term_index=0, count_index=1)

   # lookup suggestions for single-word input strings
   input_term = "apastraphee"  # misspelling of "apostrophe"
   # max edit distance per lookup
   # (max_edit_distance_lookup <= max_dictionary_edit_distance)
   suggestions = sym_spell.lookup(input_term, Verbosity.CLOSEST,
                                  max_edit_distance=2, include_unknown=True)
   # display suggestion term, term frequency, and edit distance
   for suggestion in suggestions:
       print(suggestion)

Output::

  apastraphee, 3, 0

Note that `suggestions` would have been empty if `include_unknown` was
`False`.

Avoid correcting phrases matching regex
=======================================

.. code-block:: python
   :emphasize-lines: 15,16

   import pkg_resources
   from symspellpy import SymSpell, Verbosity

   sym_spell = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)
   dictionary_path = pkg_resources.resource_filename(
       "symspellpy", "frequency_dictionary_en_82_765.txt")
   # term_index is the column of the term and count_index is the
   # column of the term frequency
   sym_spell.load_dictionary(dictionary_path, term_index=0, count_index=1)

   # lookup suggestions for single-word input strings
   input_term = "members1"
   # max edit distance per lookup
   # (max_edit_distance_lookup <= max_dictionary_edit_distance)
   suggestions = sym_spell.lookup(input_term, Verbosity.CLOSEST,
                                  max_edit_distance=2, ignore_token=r"\w+\d")
   # display suggestion term, term frequency, and edit distance
   for suggestion in suggestions:
       print(suggestion)

Output::

  members1, 0, 1

Note that `members, 1, 226656153` would be returned if `ignore_token` wasn't
specified.

Keep original casing
====================

.. code-block:: python
   :emphasize-lines: 15,16

   import pkg_resources
   from symspellpy import SymSpell, Verbosity

   sym_spell = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)
   dictionary_path = pkg_resources.resource_filename(
       "symspellpy", "frequency_dictionary_en_82_765.txt")
   # term_index is the column of the term and count_index is the
   # column of the term frequency
   sym_spell.load_dictionary(dictionary_path, term_index=0, count_index=1)

   # lookup suggestions for single-word input strings
   input_term = "mEmEbers"
   # max edit distance per lookup
   # (max_edit_distance_lookup <= max_dictionary_edit_distance)
   suggestions = sym_spell.lookup(input_term, Verbosity.CLOSEST,
                                  max_edit_distance=2, transfer_casing=True)
   # display suggestion term, term frequency, and edit distance
   for suggestion in suggestions:
       print(suggestion)

Output::

  mEmbers, 1, 226656153

Note that the uppercase of the second "E" was not passed on to "b" in the
corrected word.

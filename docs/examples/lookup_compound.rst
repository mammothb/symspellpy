===============
lookup_compound
===============

Basic usage
===========

.. code-block:: python
   :emphasize-lines: 19

   import pkg_resources
   from symspellpy import SymSpell, Verbosity

   sym_spell = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)
   dictionary_path = pkg_resources.resource_filename(
       "symspellpy", "frequency_dictionary_en_82_765.txt")
   bigram_path = pkg_resources.resource_filename(
       "symspellpy", "frequency_bigramdictionary_en_243_342.txt")
   # term_index is the column of the term and count_index is the
   # column of the term frequency
   sym_spell.load_dictionary(dictionary_path, term_index=0, count_index=1)
   sym_spell.load_bigram_dictionary(bigram_path, term_index=0, count_index=2)

   # lookup suggestions for multi-word input strings (supports compound
   # splitting & merging)
   input_term = ("whereis th elove hehad dated forImuch of thepast who "
                 "couqdn'tread in sixtgrade and ins pired him")
   # max edit distance per lookup (per single word, not per whole input string)
   suggestions = sym_spell.lookup_compound(input_term, max_edit_distance=2)
   # display suggestion term, edit distance, and term frequency
   for suggestion in suggestions:
       print(suggestion)

Output::

  where is the love he had dated for much of the past who couldn't read in six grade and inspired him, 9, 0

Keep original casing
====================

.. code-block:: python
   :emphasize-lines: 19,20

   import pkg_resources
   from symspellpy import SymSpell, Verbosity

   sym_spell = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)
   dictionary_path = pkg_resources.resource_filename(
       "symspellpy", "frequency_dictionary_en_82_765.txt")
   bigram_path = pkg_resources.resource_filename(
       "symspellpy", "frequency_bigramdictionary_en_243_342.txt")
   # term_index is the column of the term and count_index is the
   # column of the term frequency
   sym_spell.load_dictionary(dictionary_path, term_index=0, count_index=1)
   sym_spell.load_bigram_dictionary(bigram_path, term_index=0, count_index=2)

   # lookup suggestions for multi-word input strings (supports compound
   # splitting & merging)
   input_term = ("whereis th elove heHAd dated forImuch of thEPast who "
                 "couqdn'tread in sixtgrade and ins pired him")
   # max edit distance per lookup (per single word, not per whole input string)
   suggestions = sym_spell.lookup_compound(input_term, max_edit_distance=2,
                                           transfer_casing=True)
   # display suggestion term, edit distance, and term frequency
   for suggestion in suggestions:
       print(suggestion)

Output::

  where is the love he HAd dated for much of thE Past who couldn't read in six grade and inspired him, 9, 0

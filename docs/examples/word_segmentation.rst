=================
word_segmentation
=================

Basic usage
===========

.. code-block:: python
   :emphasize-lines: 14

   import pkg_resources
   from symspellpy.symspellpy import SymSpell

   # Set max_dictionary_edit_distance to avoid spelling correction
   sym_spell = SymSpell(max_dictionary_edit_distance=0, prefix_length=7)
   dictionary_path = pkg_resources.resource_filename(
       "symspellpy", "frequency_dictionary_en_82_765.txt")
   # term_index is the column of the term and count_index is the
   # column of the term frequency
   sym_spell.load_dictionary(dictionary_path, term_index=0, count_index=1)

   # a sentence without any spaces
   input_term = "thequickbrownfoxjumpsoverthelazydog"
   result = sym_spell.word_segmentation(input_term)
   print("{}, {}, {}".format(result.corrected_string, result.distance_sum,
                             result.log_prob_sum))


Output::

  the quick brown fox jumps over the lazy dog, 8, -34.491167981910635

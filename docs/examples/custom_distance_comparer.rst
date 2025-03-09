************************
Custom distance comparer
************************

Basic usage
===========

Create a comparer class which satisfies the interface specified by
:class:`~symspellpy.abstract_distance_comparer.AbstractDistanceComparer`:

.. code-block:: python

   import importlib.resources
   from itertools import islice

   from symspellpy import SymSpell
   from symspellpy.abstract_distance_comparer import AbstractDistanceComparer
   from symspellpy.editdistance import DistanceAlgorithm, EditDistance

   class CustomComparer(AbstractDistanceComparer):
       def distance(self, string1, string_2, max_distance):
           # Compare distance between string_1 and string_2
           return -1 if distance > max_distance else distance

   custom_comparer = Editdistance(DistanceAlgorithm.USER_PROVIDED, CustomComparer())
   sym_spell = SymSpell(distance_comparer=custom_comparer)
   dictionary_path = importlib.resources.files("symspellpy") / "frequency_bigramdictionary_en_243_342.txt"
   sym_spell.load_bigram_dictionary(dictionary_path, 0, 2)

   # Print out first 5 elements to demonstrate that dictionary is
   # successfully loaded
   print(list(islice(sym_spell.bigrams.items(), 5)))

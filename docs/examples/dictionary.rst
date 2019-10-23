==========
Dictionary
==========

Load frequency dictionary
=========================

`load_dictionary`
-----------------

Given a dictionary file like::

  <term> <count>
  <term> <count>
  ...
  <term> <count>

We can use :meth:`~symspellpy.symspellpy.SymSpell.load_dictionary`:

.. code-block:: python
   :emphasize-lines: 8

   from itertools import islice
   import pkg_resources
   from symspellpy import SymSpell

   sym_spell = SymSpell()
   dictionary_path = pkg_resources.resource_filename(
       "symspellpy", "frequency_dictionary_en_82_765.txt")
   sym_spell.load_dictionary(dictionary_path, 0, 1)

   # Print out first 5 elements to demonstrate that dictionary is
   # successfully loaded
   print(list(islice(sym_spell.words.items(), 5)))

Output::

  [('the', 23135851162), ('of', 13151942776), ('and', 12997637966), ('to', 12136980858), ('a', 9081174698)]

`load_bigram_dictionary`
------------------------

Given a bigram dictionary file like::

  <term_part_1> <term_part_2> <count>
  <term_part_1> <term_part_2> <count>
  ...
  <term_part_1> <term_part_2> <count>

We can use :meth:`~symspellpy.symspellpy.SymSpell.load_bigram_dictionary`:

.. code-block:: python
   :emphasize-lines: 8

   from itertools import islice
   import pkg_resources
   from symspellpy import SymSpell

   sym_spell = SymSpell()
   dictionary_path = pkg_resources.resource_filename(
       "symspellpy", "frequency_dictionary_en_82_765.txt")
   sym_spell.load_bigram_dictionary(dictionary_path, 0, 2)

   # Print out first 5 elements to demonstrate that dictionary is
   # successfully loaded
   print(list(islice(sym_spell.bigrams.items(), 5)))

Output::

  [('abcs of', 10956800), ('aaron and', 10721728), ('abbott and', 7861376), ('abbreviations and', 13518272), ('aberdeen and', 7347776)]

Load frequency dictionary with custom separator
===============================================

`load_dictionary`
-----------------

It is also possible to specific a custom `separator` so that dictionaries can
contain space separated terms. For example, given a dictionary file like::

  the$23135851162
  abcs of$10956800
  of$13151942776
  aaron and$10721728
  abbott and$7861376
  abbreviations and$13518272
  aberdeen and$7347776

We can specify "$" as the custom `separator` in
:meth:`~symspellpy.symspellpy.SymSpell.load_dictionary` like:

.. code-block:: python
   :emphasize-lines: 7

   from itertools import islice
   import pkg_resources
   from symspellpy import SymSpell

   sym_spell = SymSpell()
   dictionary_path = <path/to/dictionary>
   sym_spell.load_dictionary(dictionary_path, 0, 1, separator="$")

   # Print out first 5 elements to demonstrate that dictionary is
   # successfully loaded
   print(list(islice(sym_spell.words.items(), 5)))

Output::

  [('the', 23135851162), ('abcs of', 10956800), ('of', 13151942776), ('aaron and', 10721728), ('abbott and', 7861376)]

Note that space separated terms such as "abcs of", "aaron and", and
"abbott and" can now be found in `words` instead of `bigrams`.

`load_bigram_dictionary`
------------------------

We can also specify "$" as the custom `separator` in
:meth:`~symspellpy.symspellpy.SymSpell.load_bigram_dictionary` like
(note that we changed `count_index` from 2 to 1):

.. code-block:: python
   :emphasize-lines: 7

   from itertools import islice
   import pkg_resources
   from symspellpy import SymSpell

   sym_spell = SymSpell()
   dictionary_path = <path/to/dictionary>
   sym_spell.load_bigram_dictionary(dictionary_path, 0, 1, separator="$")

   # Print out first 5 elements to demonstrate that dictionary is
   # successfully loaded
   print(list(islice(sym_spell.bigrams.items(), 5)))

Output::

  [('the', 23135851162), ('abcs of', 10956800), ('of', 13151942776), ('aaron and', 10721728), ('abbott and', 7861376)]

Note that `bigrams` now **erroneously** contains monograms. Precautions
should taken when creating bigram dictionary with custom separator.

Create dictionary from plain text file
======================================

Given a plain text file like::

  abc abc-def abc_def abc'def abc qwe qwe1 1qwe q1we 1234 1234

We can create a dictionary from the file using
:meth:`~symspellpy.symspellpy.SymSpell.create_dictionary` like:

.. code-block:: python
   :emphasize-lines: 5

   from symspellpy import SymSpell

   sym_spell = SymSpell()
   corpus_path = <path/to/plain/text/file>
   sym_spell.create_dictionary(corpus_path)

   print(sym_spell.words)

Output::

  {'abc': 4, 'def': 2, "abc'def": 1, 'qwe': 1, 'qwe1': 1, '1qwe': 1, 'q1we': 1, '1234': 2}

Note that :meth:`~symspellpy.symspellpy.SymSpell.create_dictionary` did not
split words at apostrophes and did not check if the words contained numbers.

**********
symspellpy
**********

Enum class
==========

.. autoclass:: symspellpy.verbosity.Verbosity
   :members:

Data class
==========

.. autoclass:: symspellpy.suggest_item.SuggestItem
   :members:
   :special-members: __eq__, __lt__, __str__

.. autoclass:: symspellpy.composition.Composition
   :members:
   :exclude-members: corrected_string, distance_sum, log_prob_sum, segmented_string

Utility class
=============

.. autoclass:: symspellpy.pickle_mixin.PickleMixin
   :members:
   :private-members:

SymSpell
========

.. autoclass:: symspellpy.symspellpy.SymSpell
   :members:
   :private-members:

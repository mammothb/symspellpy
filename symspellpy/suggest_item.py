# MIT License
#
# Copyright (c) 2025 mmb L (Python port)
# Copyright (c) 2021 Wolf Garbe (Original C# implementation)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

"""
.. module:: suggest_item
   :synopsis: Data class for :meth:`symspellpy.symspellpy.lookup`.
"""


class SuggestItem:
    """Spelling suggestion returned from :meth:`lookup`.

    Args:
        term: The suggested word.
        distance: Edit distance from search word.
        count: Frequency of suggestion in dictionary or Naive Bayes probability
            of the individual suggestion parts.
    """

    def __init__(self, term: str, distance: int, count: int) -> None:
        self._term = term
        self._distance = distance
        self._count = count

    def __eq__(self, other: object) -> bool:
        """
        Returns:
            ``True`` if both distance and frequency count are the same.
        """
        if not isinstance(other, SuggestItem):
            return NotImplemented
        if self._distance == other.distance:
            return self._count == other.count
        return self._distance == other.distance

    def __lt__(self, other: object) -> bool:
        """
        Returns:
            Order by distance ascending, then by frequency count descending.
        """
        if not isinstance(other, SuggestItem):
            return NotImplemented
        if self._distance == other.distance:
            return self._count > other.count
        return self._distance < other.distance

    def __str__(self) -> str:
        """
        Returns:
            Displays attributes as "term, distance, count".
        """
        return f"{self._term}, {self._distance}, {self._count}"

    @property
    def count(self) -> int:
        """Frequency of suggestion in the dictionary (a measure of how common the
        word is) or Naive Bayes probability of the individual suggestion parts in
        :meth:`lookup_compound`.
        """
        return self._count

    @count.setter
    def count(self, count: int) -> None:
        self._count = count

    @property
    def distance(self) -> int:
        """Edit distance between searched for word and suggestion."""
        return self._distance

    @distance.setter
    def distance(self, distance: int) -> None:
        self._distance = distance

    @property
    def term(self) -> str:
        """The suggested correctly spelled word."""
        return self._term

    @term.setter
    def term(self, term: str) -> None:
        self._term = term

    @classmethod
    def create_with_probability(cls, term: str, distance: int) -> "SuggestItem":
        """Creates a SuggestItem with Naive Bayes probability as the count."""
        return cls(term, distance, 10 // 10 ** len(term))

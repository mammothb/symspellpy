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
.. module:: helpers
   :synopsis: Helper functions
"""

import re
import sys
import warnings
from difflib import SequenceMatcher
from typing import Optional


def _rename_args(kwargs_map: dict[str, str], version: str):
    def decorator(func):
        def wrapped(*args, **kwargs):
            new_kwargs = {}
            for k, v in kwargs.items():
                if k in kwargs_map:
                    warnings.warn(
                        f"Keyword argument '{k}' is deprecated and will be removed in {version}. Use '{kwargs_map[k]}' instead.",
                        DeprecationWarning,
                    )
                new_kwargs[kwargs_map.get(k, k)] = v
            return func(*args, **new_kwargs)

        return wrapped

    return decorator


def case_transfer_matching(cased_text: str, uncased_text: str) -> str:
    """Transfers the casing from one text to another - assuming that they are
    'matching' texts, alias they have the same length.

    Args:
        cased_text: Text with varied casing.
        uncased_text: Text that is in lowercase only.

    Returns:
        Text with the content of `uncased_text` and the casing of `cased_text`.

    Raises:
        ValueError: If the input texts have different lengths.
    """
    if len(cased_text) != len(uncased_text):
        raise ValueError(
            "'cased_text' and 'uncased_text' don't have the same length, use case_transfer_similar() instead"
        )

    return "".join(
        [
            y.upper() if x.isupper() else y.lower()
            for x, y in zip(cased_text, uncased_text)
        ]
    )


def case_transfer_similar(cased_text: str, uncased_text: str) -> str:
    """Transfers the casing from one text to another - for similar (not matching)
    text.

    Use `difflib.SequenceMatcher` to identify the different type of changes
    needed to turn `cased_text` into `uncased_text`.

    - For inserted sections: transfer the casing from the prior character. If no
      character before or the character before is the space, transfer the casing
      from the following character.
    - For deleted sections: no case transfer is required.
    - For equal sections: swap out the text with the original, the cased one, a
      otherwise the two are the same.
    - For replaced sections: transfer the casing using
      :meth:`case_transfer_matching` if the two has the same length, otherwise
      transfer character-by-character and carry the last casing over to any
      additional characters.

    Args:
        cased_text: Text with varied casing.
        uncased_text: Text in lowercase.

    Returns:
        Text with the content of `uncased_text` but the casing of `cased_text`.

    Raises:
        ValueError: If `cased_text` is empty.
    """
    if not uncased_text:
        return uncased_text

    if not cased_text:
        raise ValueError("'cased_text' cannot be empty")

    matcher = SequenceMatcher(a=cased_text.lower(), b=uncased_text)
    result = ""

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "delete":
            continue
        if tag == "insert":
            # For the first character or space on the left, take the casing from
            # the following character. Else take case the prior character
            ia_ref = i1 if i1 == 0 or cased_text[i1 - 1] == " " else i1 - 1
            if cased_text[ia_ref].isupper():
                result += uncased_text[j1:j2].upper()
            else:
                result += uncased_text[j1:j2].lower()
        elif tag == "equal":
            # Transfer the text from the cased_text, as anyhow they are equal
            # (without the casing)
            result += cased_text[i1:i2]
        else:
            cased_seq = cased_text[i1:i2]
            uncased_seq = uncased_text[j1:j2]

            if len(cased_seq) == len(uncased_seq):
                result += case_transfer_matching(cased_seq, uncased_seq)
            else:
                # transfer the casing character-by-character and using the last
                # casing to continue if we run out of the sequence
                for cased, uncased in zip(cased_seq, uncased_seq):
                    result += uncased.upper() if cased.isupper() else uncased.lower()
                # Apply casing from the last character of cased_seq to the rest
                # of the uncased_seq
                if len(cased_seq) < len(uncased_seq):
                    upper = cased_seq[-1].isupper()
                    idx = len(cased_seq)
                    result += "".join(
                        map(str.upper if upper else str.lower, uncased_seq[idx:])
                    )
    return result


def increment_count(count: int, count_previous: int) -> int:
    """Increments count up to ``sys.maxsize``."""
    return (
        count_previous + count if sys.maxsize - count_previous > count else sys.maxsize
    )


def is_acronym(word: str, contain_digits: bool = False) -> bool:
    """Checks if the word is all caps (acronym) and/or contain numbers.

    Args:
        word: The word to check
        contain_digits: A flag to determine whether any term with digits can be
            considered as acronym

    Returns:
        True if the word is all caps and/or contain numbers, e.g., ABCDE, AB12C,
            abc12, ab12c. False if the word contains lower case letters, e.g.,
            abcde, ABCde, abcDE, abCDe.
    """
    return re.match(r"\b[A-Z0-9]{2,}\b", word) is not None or (
        contain_digits and any(i.isdigit() for i in word)
    )


@_rename_args({"string1": "string_1", "string2": "string_2"}, "v7.0.0")
def null_distance_results(
    string_1: Optional[str], string_2: Optional[str], max_distance: int
) -> int:
    """Determines the proper return value of an edit distance function when one
    or both strings are null.

    Args:
        string_1: Base string.
        string_2: The string to compare.
        max_distance: The maximum distance allowed.

    Returns:
        -1 if the distance is greater than the max_distance, 0 if the strings are
            equivalent (both are None), otherwise a positive number whose
            magnitude is the length of the string which is not None.
    """
    if string_1 is None:
        if string_2 is None:
            return 0
        return len(string_2) if len(string_2) <= max_distance else -1
    return len(string_1) if len(string_1) <= max_distance else -1


def parse_words(
    phrase: str, preserve_case: bool = False, split_by_space: bool = False
) -> list[str]:
    """Creates a non-unique wordlist from sample text. Language independent
    (e.g. works with Chinese characters)

    Args:
        phrase: Sample text that could contain one or more words.
        preserve_case: A flag to determine if we can to preserve the cases or
            convert all to lowercase.
        split_by_space: Splits the phrase into words simply based on space.

    Returns:
        A list of words
    """
    if split_by_space:
        if preserve_case:
            return phrase.split()
        return phrase.lower().split()
    # \W non-words, use negated set to ignore non-words and "_" (underscore).
    # Compatible with non-latin characters, does not split words at apostrophes
    if preserve_case:
        return re.findall(r"([^\W_]+['’]*[^\W_]*)", phrase)
    return re.findall(r"([^\W_]+['’]*[^\W_]*)", phrase.lower())


@_rename_args({"string1": "string_1", "string2": "string_2"}, "v7.0.0")
def prefix_suffix_prep(string_1: str, string_2: str) -> tuple[int, int, int]:
    """Calculates starting position and lengths of two strings such that common
    prefix and suffix substrings are excluded.
    Expects len(string_1) <= len(string_2).

    Args:
        string_1: Base string.
        string_2: The string to compare.

    Returns:
        A tuple of lengths of the part excluding common prefix and suffix, and
            the starting position.
    """
    # this is also the minimun length of the two strings
    len_1 = len(string_1)
    len_2 = len(string_2)
    # suffix common to both strings can be ignored
    while len_1 != 0 and string_1[len_1 - 1] == string_2[len_2 - 1]:
        len_1 -= 1
        len_2 -= 1
    # prefix common to both strings can be ignored
    start = 0
    while start != len_1 and string_1[start] == string_2[start]:
        start += 1
    if start != 0:
        len_1 -= start
        # length of the part excluding common prefix and suffix
        len_2 -= start
    return len_1, len_2, start


def to_similarity(distance: int, length: int) -> float:
    """Calculates a similarity measure from an edit distance.

    Args:
        distance: The edit distance between two strings.
        length: The length of the longer of the two strings the edit distance is
            from.

    Returns:
        A similarity value from 0 to 1.0 (1 - (length / distance)), -1 if
            distance is negative
    """
    return -1 if distance < 0 else 1.0 - distance / length


def try_parse_int64(string: str) -> Optional[int]:
    """Converts the string representation of a number to its 64-bit signed
    integer equivalent.

    Args:
        string: String representation of a number.

    Returns:
        The 64-bit signed integer equivalent, or None if conversion failed or if
            the number is less than the min value or greater than the max value
            of a 64-bit signed integer.
    """
    try:
        ret = int(string)
    except ValueError:
        return None
    return ret if -(2**63) <= ret <= 2**63 - 1 else None


class DictIO:
    """An iterator wrapper for python dictionary to format the output as required
    by :meth:`load_dictionary_stream` and :meth:`load_dictionary_bigram_stream`.

    Args:
        dictionary: dictionary with words as keys and frequency count as values.
        separator: Separator characters between term(s) and count.

    Attributes:
        iteritems: An iterator object of dictionary.items().
        separator: Separator characters between term(s) and count.
    """

    def __init__(self, dictionary: dict[str, int], separator: str = " ") -> None:
        self.iteritems = iter(dictionary.items())
        self.separator = separator

    def __iter__(self) -> "DictIO":
        return self

    def __next__(self) -> str:
        return self.separator.join(map(str, next(self.iteritems)))

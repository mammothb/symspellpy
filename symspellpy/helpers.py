"""
.. module:: helpers
   :synopsis: Helper functions
"""
import re

def null_distance_results(string1, string2, max_distance):
    """Determines the proper return value of an edit distance function
    when one or both strings are null.

    **Args**:

    * string_1 (str): Base string.
    * string_2 (str): The string to compare.
    * max_distance (int): The maximum distance allowed.

    **Returns**:
    -1 if the distance is greater than the max_distance, 0 if the\
        strings are equivalent (both are None), otherwise a positive number\
        whose magnitude is the length of the string which is not None.
    """
    if string1 is None:
        if string2 is None:
            return 0
        else:
            return len(string2) if len(string2) <= max_distance else -1
    return len(string1) if len(string1) <= max_distance else -1

def prefix_suffix_prep(string1, string2):
    """Calculates starting position and lengths of two strings such
    that common prefix and suffix substrings are excluded.
    Expects len(string1) <= len(string2)

    **Args**:

    * string_1 (str): Base string.
    * string_2 (str): The string to compare.

    **Returns**:
    Lengths of the part excluding common prefix and suffix, and the\
        starting position
    """
    # this is also the minimun length of the two strings
    len1 = len(string1)
    len2 = len(string2)
    # suffix common to both strings can be ignored
    while len1 != 0 and string1[len1 - 1] == string2[len2 - 1]:
        len1 -= 1
        len2 -= 1
    # prefix common to both strings can be ignored
    start = 0
    while start != len1 and string1[start] == string2[start]:
        start += 1
    if start != 0:
        len1 -= start
        # length of the part excluding common prefix and suffix
        len2 -= start
    return len1, len2, start

def to_similarity(distance, length):
    """Calculate a similarity measure from an edit distance.

    **Args**:

    * distance (int): The edit distance between two strings.
    * length (int): The length of the longer of the two strings the\
        edit distance is from.

    **Returns**:
    A similarity value from 0 to 1.0 (1 - (length / distance)), -1 if\
        distance is negative
    """
    return -1 if distance < 0 else 1.0 - distance / length

def try_parse_int64(string):
    """Converts the string representation of a number to its 64-bit
    signed integer equivalent.

    **Args**:

    * string (str): string representation of a number

    **Returns**:
    The 64-bit signed integer equivalent, or None if conversion failed\
        or if the number is less than the min value or greater than\
        the max value of a 64-bit signed integer.
    """
    try:
        ret = int(string)
    except ValueError:
        return None
    return None if ret < -2 ** 64 or ret >= 2 ** 64 else ret

def parse_words(phrase, preserve_case=False):
    """Create a non-unique wordlist from sample text. Language
    independent (e.g. works with Chinese characters)

    **Args**:

    * phrase (str): Sample text that could contain one or more words
    * preserve_case (bool): A flag to determine if we can to preserve\
        the cases or convert all to lowercase

    **Returns**:
    A list of words
    """
    # \W non-words, use negated set to ignore non-words and "_"
    # (underscore). Compatible with non-latin characters, does not
    # split words at apostrophes
    if preserve_case:
        return re.findall(r"([^\W_]+['’]*[^\W_]*)", phrase)
    else:
        return re.findall(r"([^\W_]+['’]*[^\W_]*)", phrase.lower())

def is_acronym(word):
    """Checks is the word is all caps (acronym) and/or contain numbers

    **Args**:

    word (str): The word to check

    **Returns**:
    True if the word is all caps and/or contain numbers, e.g., ABCDE,\
        AB12C. False if the word contains lower case letters, e.g.,\
            abcde, ABCde, abcDE, abCDe, abc12, ab12c
    """
    return re.match(r"\b[A-Z0-9]{2,}\b", word) is not None

import re

def null_distance_results(string1, string2, max_distance):
    """Determines the proper return value of an edit distance function when
    one or both strings are null.
    """
    if string1 is None:
        if string2 is None:
            return 0
        else:
            return len(string2) if len(string2) <= max_distance else -1
    return len(string1) if len(string1) <= max_distance else -1

def prefix_suffix_prep(string1, string2):
    """Calculates starting position and lengths of two strings such that
    common prefix and suffix substrings are excluded.
    Expects len(string1) <= len(string2)
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
    return -1 if distance < 0 else 1.0 - distance / length

def try_parse_int64(string):
    try:
        ret = int(string)
    except ValueError:
        return None
    return None if ret < -2 ** 64 or ret >= 2 ** 64 else ret

def parse_words(phrase, preserve_case=False):
    """create a non-unique wordlist from sample text
    language independent (e.g. works with Chinese characters)
    """
    # \W non-words, use negated set to ignore non-words and "_" (underscore)
    # Compatible with non-latin characters, does not split words at
    # apostrophes
    if preserve_case:
        return re.findall(r"([^\W_]+['’]*[^\W_]*)", phrase)
    else:
        return re.findall(r"([^\W_]+['’]*[^\W_]*)", phrase.lower())

def is_acronym(word):
    """Checks is the word is all caps (acronym)

    Return:
    True if the word is all caps, e.g., ABCDE
    False if the word contains lower case letters, e.g., abcde, ABCde, abcDE,
        abCDe
    """
    return re.match(r"\b[A-Z]{2,}\b", word) is not None

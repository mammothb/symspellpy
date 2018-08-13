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

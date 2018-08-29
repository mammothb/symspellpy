import sys
from collections import defaultdict
from enum import Enum
from os import path

import spellchecker.helpers as helpers
from spellchecker.editdistance import DistanceAlgorithm, EditDistance


class Verbosity(Enum):
    """Controls the closeness/quantity of returned spelling suggestions."""
    # Top suggestion with the highest term frequency of the suggestions of
    # smallest edit distance found.
    TOP = 0
    # All suggestions of smallest edit distance found, suggestions ordered by
    # term frequency.
    CLOSEST = 1
    # All suggestions within maxEditDistance, suggestions ordered by edit
    # distance, then by term frequency (slower, no early termination).
    ALL = 2


class SymSpell(object):
    def __init__(self, initial_capacity=16, max_dictionary_edit_distance=2,
                 prefix_length=7, count_threshold=1, compact_level=5):
        """Create a new instance of SymSpell.
        Specifying an accurate initial_capacity is not essential, but it can
        help speed up processing by aleviating the need for data
        restructuring as the size grows.

        Keyword arguments:
        initial_capacity -- The expected number of words in
            dictionary. (default 16)
        max_dictionary_edit_distance -- Maximum edit distance for doing
            lookups. (default 2)
        prefix_length -- The length of word prefixes used for spell
            checking. (default 7)
        count_threshold -- The minimum frequency count for dictionary words
                to be considered correct spellings. (default 1)
        compact_level -- Degree of favoring lower memory use over speed
            (0=fastest,most memory, 16=slowest,least memory). (default 5)
        """
        if initial_capacity < 0:
            raise ValueError("initial_capacity cannot be negative")
        if max_dictionary_edit_distance < 0:
            raise ValueError("max_dictionary_edit_distance cannot be negative")
        if prefix_length < 1 or prefix_length <= max_dictionary_edit_distance:
            raise ValueError("prefix_length cannot be less than 1 or "
                             "smaller than max_dictionary_edit_distance")
        if count_threshold < 0:
            raise ValueError("count_threshold cannot be negative")
        if compact_level < 0 or compact_level > 16:
            raise ValueError("compact_level must be between 0 and 16")
        self._initial_capacity = initial_capacity
        self._words = dict()
        self._below_threshold_words = dict()
        self._deletes = defaultdict(list)
        self._max_dictionary_edit_distance = max_dictionary_edit_distance
        self._prefix_length = prefix_length
        self._count_threshold = count_threshold
        self._compact_mask = (0xFFFFFFFF >> (3 + min(compact_level, 16))) << 2
        self._distance_algorithm = DistanceAlgorithm.DAMERUAUOSA
        self._max_length = 0

    def create_dictionary_entry(self, key, count):
        """Create/Update an entry in the dictionary.
        For every word there are deletes with an edit distance of
        1..max_edit_distance created and added to the dictionary. Every delete
        entry has a suggestions list, which points to the original term(s) it
        was created from. The dictionary may be dynamically updated (word
        frequency and new words) at any time by calling
        create_dictionary_entry

        Keyword arguments:
        key -- The word to add to dictionary.
        count -- The frequency count for word.

        Return:
        True if the word was added as a new correctly spelled word, or
        False if the word is added as a below threshold word, or updates an
        existing correctly spelled word.
        """
        if count <= 0:
            # no point doing anything if count is zero, as it can't change
            # anything
            if self._count_threshold > 0:
                return False
            count = 0

        # look first in below threshold words, update count, and allow
        # promotion to correct spelling word if count reaches threshold
        # threshold must be >1 for there to be the possibility of low threshold
        # words
        if self._count_threshold > 1 and key in self._below_threshold_words:
            count_previous = self._below_threshold_words[key]
            # calculate new count for below threshold word
            count = (count_previous + count
                     if sys.maxsize - count_previous > count
                     else sys.maxsize)
            # has reached threshold - remove from below threshold collection
            # (it will be added to correct words below)
            if count >= self._count_threshold:
                self._below_threshold_words.pop(key)
            else:
                self._below_threshold_words[key] = count
                return False
        elif key in self._words:
            count_previous = self._words[key]
            # just update count if it's an already added above threshold word
            count = (count_previous + count
                     if sys.maxsize - count_previous > count
                     else sys.maxsize)
            self._words[key] = count
            return False
        elif count < self._count_threshold:
            # new or existing below threshold word
            self._below_threshold_words[key] = count
            return False

        # what we have at this point is a new, above threshold word
        self._words[key] = count

        # edits/suggestions are created only once, no matter how often word
        # occurs. edits/suggestions are created as soon as the word occurs
        # in the corpus, even if the same term existed before in the
        # dictionary as an edit from another word
        if len(key) > self._max_length:
            self._max_length = len(key)

        # create deletes
        edits = self.edits_prefix(key)
        for delete in edits:
            delete_hash = self.get_str_hash(delete)
            if delete_hash in self._deletes:
                self._deletes[delete_hash].append(key)
            else:
                self._deletes[delete_hash] = [key]
        return True

    def load_dictionary(self, corpus, term_index, count_index):
        """Load multiple dictionary entries from a file of word/frequency
        count pairs. Merges with any dictionary data already loaded.

        Keyword arguments:
        corpus -- The path+filename of the file.
        term_index -- The column position of the word.
        count_index -- The column position of the frequency count.

        Return:
        True if file loaded, or False if file not found.
        """
        if not path.exists(corpus):
            return False
        with open(corpus, "r") as infile:
            for line in infile:
                line_parts = line.rstrip().split(" ")
                if len(line_parts) >= 2:
                    key = line_parts[term_index]
                    count = helpers.try_parse_int64(line_parts[count_index])
                    if count is not None:
                        self.create_dictionary_entry(key, count)
        return True

    def lookup(self, phrase, verbosity, max_edit_distance=None,
               include_unknown=False):
        """Find suggested spellings for a given phrase word.

        Keyword arguments:
        phrase -- The word being spell checked.
        verbosity -- The value controlling the quantity/closeness of the
            returned suggestions.
        max_edit_distance -- The maximum edit distance between phrase and
            suggested words.
        include_unknown -- Include phrase word in suggestions, if no words
            within edit distance found.

        Return:
        A list of SuggestItem object representing suggested correct spellings
        for the phrase word, sorted by edit distance, and secondarily by count
        frequency.
        """
        if max_edit_distance is None:
            max_edit_distance = self._max_dictionary_edit_distance
        if max_edit_distance > self._max_dictionary_edit_distance:
            raise ValueError("Distance too large")
        suggestions = list()
        phrase_len = len(phrase)

        def early_exit():
            if include_unknown and not suggestions:
                suggestions.append(SuggestItem(phrase, max_edit_distance + 1,
                                               0))
            return suggestions

        # early exit - word is too big to possibly match any words
        if phrase_len - max_edit_distance > self._max_length:
            return early_exit()

        # quick look for exact match
        suggestion_count = 0
        if phrase in self._words:
            suggestion_count = self._words[phrase]
            suggestions.append(SuggestItem(phrase, 0, suggestion_count))
            # early exit - return exact match, unless caller wants all matches
            if verbosity != Verbosity.ALL:
                return early_exit()

        # early termination, if we only want to check if word in dictionary or
        # get its frequency e.g. for word segmentation
        if max_edit_distance == 0:
            return early_exit()

        considered_deletes = set()
        considered_suggestions = set()
        # we considered the phrase already in the 'phrase in self._words' above
        considered_suggestions.add(phrase)

        max_edit_distance_2 = max_edit_distance
        candidate_pointer = 0
        candidates = list()

        # add original prefix
        phrase_prefix_len = phrase_len
        if phrase_prefix_len > self._prefix_length:
            phrase_prefix_len = self._prefix_length
            candidates.append(phrase[: phrase_prefix_len])
        else:
            candidates.append(phrase)
        distance_comparer = EditDistance(self._distance_algorithm)
        while candidate_pointer < len(candidates):
            candidate = candidates[candidate_pointer]
            candidate_pointer += 1
            candidate_len = len(candidate)
            len_diff = phrase_prefix_len - candidate_len

            # early termination: if candidate distance is already higher than
            # suggestion distance, than there are no better suggestions to be
            # expected
            if len_diff > max_edit_distance_2:
                # skip to next candidate if Verbosity.ALL, look no
                # further if Verbosity.TOP or CLOSEST (candidates are
                # ordered by delete distance, so none are closer than current)
                if verbosity == Verbosity.ALL:
                    continue
                break

            if self.get_str_hash(candidate) in self._deletes:
                dict_suggestions = self._deletes[self.get_str_hash(candidate)]
                for suggestion in dict_suggestions:
                    if suggestion == phrase:
                        continue
                    suggestion_len = len(suggestion)
                    # phrase and suggestion lengths diff > allowed/current best
                    # distance
                    if (abs(suggestion_len - phrase_len) > max_edit_distance_2
                            # suggestion must be for a different delete string,
                            # in same bin only because of hash collision
                            or suggestion_len < candidate_len
                            # if suggestion len = delete len, then it either
                            # equals delete or is in same bin only because of
                            # hash collision
                            or (suggestion_len == candidate_len
                                and suggestion != candidate)):
                        continue
                    suggestion_prefix_len = min(suggestion_len,
                                                self._prefix_length)
                    if (suggestion_prefix_len > phrase_prefix_len
                            and suggestion_prefix_len - candidate_len > max_edit_distance_2):
                        continue
                    # True Damerau-Levenshtein Edit Distance: adjust distance,
                    # if both distances>0
                    # We allow simultaneous edits (deletes) of max_edit_distance
                    # on on both the dictionary and the phrase term.
                    # For replaces and adjacent transposes the resulting edit
                    # distance stays <= max_edit_distance.
                    # For inserts and deletes the resulting edit distance might
                    # exceed max_edit_distance.
                    # To prevent suggestions of a higher edit distance, we need
                    # to calculate the resulting edit distance, if there are
                    # simultaneous edits on both sides.
                    # Example: (bank==bnak and bank==bink, but bank!=kanb and
                    # bank!=xban and bank!=baxn for max_edit_distance=1)
                    # Two deletes on each side of a pair makes them all equal,
                    # but the first two pairs have edit distance=1, the others
                    # edit distance=2.
                    distance = 0
                    min_distance = 0
                    if candidate_len == 0:
                        # suggestions which have no common chars with phrase
                        # (phrase_len<=max_edit_distance &&
                        # suggestion_len<=max_edit_distance)
                        distance = max(phrase_len, suggestion_len)
                        if (distance > max_edit_distance_2
                                or suggestion in considered_suggestions):
                            continue
                    elif suggestion_len == 1:
                        distance = (phrase_len
                                    if phrase.index(suggestion[0]) < 0
                                    else phrase_len - 1)
                        if (distance > max_edit_distance_2
                                or suggestion in considered_suggestions):
                            continue
                    # number of edits in prefix ==maxediddistance AND no
                    # identical suffix, then editdistance>max_edit_distance and
                    # no need for Levenshtein calculation
                    # (phraseLen >= prefixLength) &&
                    # (suggestionLen >= prefixLength)
                    else:
                        # handles the shortcircuit of min_distance assignment
                        # when first boolean expression evaluates to False
                        if self._prefix_length - max_edit_distance == candidate_len:
                            min_distance = (min(phrase_len, suggestion_len) -
                                            self._prefix_length)
                        else:
                            min_distance = 0
                        # pylint: disable=C0301,R0916
                        if (self._prefix_length - max_edit_distance == candidate_len
                                and (min_distance > 1
                                     and phrase[phrase_len + 1 - min_distance:] !=
                                     suggestion[suggestion_len + 1 - min_distance:])
                                or (min_distance > 0
                                    and phrase[phrase_len - min_distance] !=
                                    suggestion[suggestion_len - min_distance]
                                    and (phrase[phrase_len - min_distance - 1] !=
                                         suggestion[suggestion_len - min_distance]
                                         or phrase[phrase_len - min_distance] !=
                                         suggestion[suggestion_len - min_distance - 1]))):
                            continue
                        else:
                            # delete_in_suggestion_prefix is somewhat expensive,
                            # and only pays off when verbosity is TOP or CLOSEST
                            if ((verbosity != Verbosity.ALL
                                 and not self.delete_in_suggestion_prefix(
                                     candidate, candidate_len, suggestion,
                                     suggestion_len))
                                    or suggestion in considered_suggestions):
                                continue
                            considered_suggestions.add(suggestion)
                            distance = distance_comparer.compare(
                                phrase, suggestion, max_edit_distance_2)
                            if distance < 0:
                                continue
                    # do not process higher distances than those already found,
                    # if verbosity<ALL (note: max_edit_distance_2 will always
                    # equal max_edit_distance when Verbosity.ALL)
                    if distance <= max_edit_distance_2:
                        suggestion_count = self._words[suggestion]
                        si = SuggestItem(suggestion, distance, suggestion_count)
                        if suggestions:
                            if verbosity == Verbosity.CLOSEST:
                                # we will calculate DamLev distance only to the
                                # smallest found distance so far
                                if distance < max_edit_distance_2:
                                    suggestions = list()
                            elif verbosity == Verbosity.TOP:
                                if (distance < max_edit_distance_2
                                        or suggestion_count > suggestions[0].count):
                                    max_edit_distance_2 = distance
                                    suggestions[0] = si
                                continue
                        if verbosity != Verbosity.ALL:
                            max_edit_distance_2 = distance
                        suggestions.append(si)
            # add edits: derive edits (deletes) from candidate (phrase) and
            # add them to candidates list. this is a recursive process until
            # the maximum edit distance has been reached
            if (len_diff < max_edit_distance
                    and candidate_len <= self._prefix_length):
                # do not create edits with edit distance smaller than
                # suggestions already found
                if (verbosity != Verbosity.ALL
                        and len_diff >= max_edit_distance_2):
                    continue
                for i in range(candidate_len):
                    delete = candidate[: i] + candidate[i + 1:]
                    if delete not in considered_deletes:
                        considered_deletes.add(delete)
                        candidates.append(delete)
        if len(suggestions) > 1:
            suggestions.sort()
        return suggestions

    def lookup_compound(self, phrase, max_edit_distance,
                        ignore_non_words=False):
        """lookup_compound supports compound aware automatic spelling
        correction of multi-word input strings with three cases:
        1. mistakenly inserted space into a correct word led to two incorrect
           terms
        2. mistakenly omitted space between two correct words led to one
           incorrect combined term
        3. multiple independent input terms with/without spelling errors

        Find suggested spellings for a multi-word input string (supports word
        splitting/merging).

        Keyword arguments:
        phrase -- The string being spell checked.
        max_edit_distance -- The maximum edit distance between input and
            suggested words.

        Return:
        A List of SuggestItem object representing suggested correct spellings
        for the input string.
        """
        # Parse input string into single terms
        term_list_1 = helpers.parse_words(phrase)
        # Second list of single terms with preserved cases so we can ignore
        # acronyms (all cap words)
        if ignore_non_words:
            term_list_2 = helpers.parse_words(phrase, True)
        suggestions = list()
        suggestion_parts = list()
        distance_comparer = EditDistance(self._distance_algorithm)

        # translate every item to its best suggestion, otherwise it remains
        # unchanged
        is_last_combi = False
        for i, __ in enumerate(term_list_1):
            if ignore_non_words:
                if helpers.try_parse_int64(term_list_1[i]) is not None:
                    suggestion_parts.append(SuggestItem(term_list_1[i], 0, 0))
                    continue
                # if re.match(r"\b[A-Z]{2,}\b", term_list_2[i]):
                if helpers.is_acronym(term_list_2[i]):
                    suggestion_parts.append(SuggestItem(term_list_2[i], 0, 0))
                    continue
            suggestions = self.lookup(term_list_1[i], Verbosity.TOP,
                                      max_edit_distance)
            # combi check, always before split
            if i > 0 and not is_last_combi:
                suggestions_combi = self.lookup(
                    term_list_1[i - 1] + term_list_1[i], Verbosity.TOP,
                    max_edit_distance)
                if suggestions_combi:
                    best_1 = suggestion_parts[-1]
                    if suggestions:
                        best_2 = suggestions[0]
                    else:
                        best_2 = SuggestItem(term_list_1[i],
                                             max_edit_distance + 1, 0)
                    # make sure we're comparing with the lowercase form of the
                    # previous word
                    distance_1 = distance_comparer.compare(
                        term_list_1[i - 1] + " " + term_list_1[i],
                        best_1.term.lower() + " " + best_2.term,
                        max_edit_distance)
                    if (distance_1 >= 0
                            and suggestions_combi[0].distance + 1 < distance_1):
                        suggestions_combi[0].distance += 1
                        suggestion_parts[-1] = suggestions_combi[0]
                        is_last_combi = True
                        continue
            is_last_combi = False

            # alway split terms without suggestion / never split terms with
            # suggestion ed=0 / never split single char terms
            if (suggestions and (suggestions[0].distance == 0
                                 or len(term_list_1[i]) == 1)):
                # choose best suggestion
                suggestion_parts.append(suggestions[0])
            else:
                # if no perfect suggestion, split word into pairs
                suggestions_split = list()
                # add original term
                if suggestions:
                    suggestions_split.append(suggestions[0])
                if len(term_list_1[i]) > 1:
                    for j in range(1, len(term_list_1[i])):
                        part_1 = term_list_1[i][: j]
                        part_2 = term_list_1[i][j:]
                        suggestions_1 = self.lookup(part_1, Verbosity.TOP,
                                                    max_edit_distance)
                        if suggestions_1:
                            # if split correction1 == einzelwort correction
                            if (suggestions
                                    and suggestions[0].term == suggestions_1[0].term):
                                break
                            suggestions_2 = self.lookup(part_2, Verbosity.TOP,
                                                        max_edit_distance)
                            if suggestions_2:
                                # if split correction1 == einzelwort correction
                                if (suggestions
                                        and suggestions[0].term == suggestions_2[0].term):
                                    break
                                # select best suggestion for split pair
                                tmp_term = (suggestions_1[0].term + " " +
                                            suggestions_2[0].term)
                                tmp_distance = distance_comparer.compare(
                                    term_list_1[i], tmp_term,
                                    max_edit_distance)
                                if tmp_distance < 0:
                                    tmp_distance = max_edit_distance + 1
                                tmp_count = min(suggestions_1[0].count,
                                                suggestions_2[0].count)
                                suggestion_split = SuggestItem(
                                    tmp_term, tmp_distance, tmp_count)
                                suggestions_split.append(suggestion_split)
                                # early termination of split
                                if suggestion_split.distance == 1:
                                    break

                    if suggestions_split:
                        # select best suggestion for split pair
                        suggestions_split.sort()
                        suggestion_parts.append(suggestions_split[0])
                    else:
                        si = SuggestItem(term_list_1[i],
                                         max_edit_distance + 1, 0)
                        suggestion_parts.append(si)
                else:
                    si = SuggestItem(term_list_1[i], max_edit_distance + 1, 0)
                    suggestion_parts.append(si)
        joined_term = ""
        joined_count = sys.maxsize
        for si in suggestion_parts:
            joined_term += si.term + " "
            joined_count = min(joined_count, si.count)
        suggestion = SuggestItem(joined_term.rstrip(),
                                 distance_comparer.compare(
                                     phrase, joined_term, 2 ** 31 - 1),
                                 joined_count)
        suggestions_line = list()
        suggestions_line.append(suggestion)
        return suggestions_line

    def delete_in_suggestion_prefix(self, delete, delete_len, suggestion,
                                    suggestion_len):
        """check whether all delete chars are present in the suggestion
        prefix in correct order, otherwise this is just a hash collision
        """
        if delete_len == 0:
            return True
        if self._prefix_length < suggestion_len:
            suggestion_len = self._prefix_length
        j = 0
        for i in range(delete_len):
            del_char = delete[i]
            while j < suggestion_len and del_char != suggestion[j]:
                j += 1
            if j == suggestion_len:
                return False
        return True

    def edits(self, word, edit_distance, delete_words):
        """inexpensive and language independent: only deletes,
        no transposes + replaces + inserts replaces and inserts are expensive
        and language dependent
        """
        edit_distance += 1
        if len(word) > 1:
            for i in range(len(word)):
                delete = word[:i] + word[i + 1:]
                if delete not in delete_words:
                    delete_words.add(delete)
                    # recursion, if maximum edit distance not yet reached
                    if edit_distance < self._max_dictionary_edit_distance:
                        self.edits(delete, edit_distance, delete_words)
        return delete_words

    def edits_prefix(self, key):
        hash_set = set()
        if len(key) <= self._max_dictionary_edit_distance:
            hash_set.add("")
        if len(key) > self._max_dictionary_edit_distance:
            key = key[: self._prefix_length]
        hash_set.add(key)
        return self.edits(key, 0, hash_set)

    def get_str_hash(self, s):
        s_len = len(s)
        mask_len = min(s_len, 3)

        hash_s = 2166136261
        for i in range(s_len):
            hash_s ^= ord(s[i])
            hash_s *= 16777619
        hash_s &= self._compact_mask
        hash_s |= mask_len
        return hash_s

    @property
    def deletes(self):
        return self._deletes

    @property
    def words(self):
        return self._words

    @property
    def word_count(self):
        return len(self._words)


class SuggestItem(object):
    """Spelling suggestion returned from Lookup."""
    def __init__(self, term, distance, count):
        """Create a new instance of SuggestItem.

        Keyword arguments:
        term -- The suggested word.
        distance -- Edit distance from search word.
        count -- Frequency of suggestion in dictionary.
        """
        self._term = term
        self._distance = distance
        self._count = count

    def __eq__(self, other):
        """order by distance ascending, then by frequency count
        descending
        """
        if self._distance == other.distance:
            return self._count == other.count
        else:
            return self._distance == other.distance

    def __lt__(self, other):
        if self._distance == other.distance:
            return self._count > other.count
        else:
            return self._distance < other.distance

    def __str__(self):
        return "{}, {}, {}".format(self._term, self._distance, self._count)

    @property
    def term(self):
        return self._term

    @term.setter
    def term(self, term):
        self._term = term

    @property
    def distance(self):
        return self._distance

    @distance.setter
    def distance(self, distance):
        self._distance = distance

    @property
    def count(self):
        return self._count

    @count.setter
    def count(self, count):
        self._count = count

"""
.. module:: symspellpy
   :synopsis: Module for Symmetric Delete spelling correction algorithm.
"""
from collections import defaultdict, namedtuple
from enum import Enum
import gzip
from itertools import cycle
import math
import os.path
import pickle
import re
import sys

from symspellpy.editdistance import DistanceAlgorithm, EditDistance
import symspellpy.helpers as helpers

class Verbosity(Enum):
    """Controls the closeness/quantity of returned spelling
    suggestions.
    """
    TOP = 0  #: Top suggestion with the highest term frequency of the suggestions of smallest edit distance found.
    CLOSEST = 1  #: All suggestions of smallest edit distance found, suggestions ordered by term frequency.
    ALL = 2  #: All suggestions within maxEditDistance, suggestions ordered by edit distance, then by term frequency (slower, no early termination).

class SymSpell(object):
    """Symmetric Delete spelling correction algorithm.
    `initial_capacity` from the original code is omitted since python
    cannot preallocate memory. `compact_mask` from the original code is
    omitted since we're not mapping suggested corrections to hash
    codes.

    Parameters
    ----------
    max_dictionary_edit_distance : int, optional
        Maximum edit distance for doing lookups.
    prefix_length : int, optional
        The length of word prefixes used for spell checking.
    count_threshold : int
        The minimum frequency count for dictionary words to be
        considered correct spellings.

    Attributes
    ----------
    _words : dict
        Dictionary of unique correct spelling words, and the frequency
        count for each word.
    _below_threshold_words : dict
        Dictionary of unique words that are below the count threshold
        for being considered correct spellings.
    _deletes : dict
        Dictionary that contains a mapping of lists of suggested
        correction words to the original words and the deletes derived
        from them. A list of suggestions might have a single
        suggestion, or multiple suggestions.
    _max_dictionary_edit_distance : int
        Maximum dictionary term length.
    _prefix_length : int
        The length of word prefixes used for spell checking.
    _count_threshold : int
        A threshold may be specified, when a term occurs so frequently
        in the corpus that it is considered a valid word for spelling
        correction.
    _distance_algorithm : :class:`.editdistance.DistanceAlgorithm`
        Edit distance algorithms
    _max_length : int
        Length of longest word in the dictionary.
    _replaced_words : dict
        Dictionary corrected/modified words

    Raises
    ------
    ValueError
        If `max_dictionary_edit_distance` is negative.
    ValueError
        If `prefix_length` is less than 1 or smaller than
        `max_dictionary_edit_distance`.
    ValueError
        If `count_threshold` is negative.
    """
    data_version = 2
    # number of all words in the corpus used to generate the
    # frequency dictionary. This is used to calculate the word
    # occurrence probability p from word counts c : p=c/N. N equals
    # the sum of all counts c in the dictionary only if the
    # dictionary is complete, but not if the dictionary is
    # truncated or filtered
    N = 1024908267229
    bigram_count_min = sys.maxsize
    def __init__(self, max_dictionary_edit_distance=2, prefix_length=7,
                 count_threshold=1):
        if max_dictionary_edit_distance < 0:
            raise ValueError("max_dictionary_edit_distance cannot be "
                             "negative")
        if (prefix_length < 1
                or prefix_length <= max_dictionary_edit_distance):
            raise ValueError("prefix_length cannot be less than 1 or "
                             "smaller than max_dictionary_edit_distance")
        if count_threshold < 0:
            raise ValueError("count_threshold cannot be negative")
        self._words = dict()
        self._below_threshold_words = dict()
        self._bigrams = dict()
        self._deletes = defaultdict(list)
        self._max_dictionary_edit_distance = max_dictionary_edit_distance
        self._prefix_length = prefix_length
        self._count_threshold = count_threshold
        self._distance_algorithm = DistanceAlgorithm.DAMERUAUOSA
        self._max_length = 0
        self._replaced_words = dict()

    def create_dictionary_entry(self, key, count):
        """Create/Update an entry in the dictionary. For every word
        there are deletes with an edit distance of 1..max_edit_distance
        created and added to the dictionary. Every delete entry has a
        suggestions list, which points to the original term(s) it was
        created from. The dictionary may be dynamically updated (word
        frequency and new words) at any time by calling
        create_dictionary_entry

        Parameters
        ----------
        key : str
            The word to add to dictionary.
        count : int
            The frequency count for word.

        Returns
        -------
        bool
            True if the word was added as a new correctly spelled
            word, or False if the word is added as a below threshold
            word, or updates an existing correctly spelled word.
        """
        if count <= 0:
            # no point doing anything if count is zero, as it can't
            # change anything
            if self._count_threshold > 0:
                return False
            count = 0

        # look first in below threshold words, update count, and allow
        # promotion to correct spelling word if count reaches threshold
        # threshold must be >1 for there to be the possibility of low
        # threshold words
        if self._count_threshold > 1 and key in self._below_threshold_words:
            count_previous = self._below_threshold_words[key]
            # calculate new count for below threshold word
            count = (count_previous + count
                     if sys.maxsize - count_previous > count
                     else sys.maxsize)
            # has reached threshold - remove from below threshold
            # collection (it will be added to correct words below)
            if count >= self._count_threshold:
                self._below_threshold_words.pop(key)
            else:
                self._below_threshold_words[key] = count
                return False
        elif key in self._words:
            count_previous = self._words[key]
            # just update count if it's an already added above
            # threshold word
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

        # edits/suggestions are created only once, no matter how often
        # word occurs. edits/suggestions are created as soon as the
        # word occurs in the corpus, even if the same term existed
        # before in the dictionary as an edit from another word
        if len(key) > self._max_length:
            self._max_length = len(key)

        # create deletes
        edits = self._edits_prefix(key)
        for delete in edits:
            self._deletes[delete].append(key)
        return True

    def delete_dictionary_entry(self, key):
        """Delete an entry in the dictionary. If the deleted entry is
        the longest word, update :attr:`_max_length` with the next
        longest word

        Parameters
        ----------
        key : str
            The word to add to dictionary.

        Returns
        -------
        bool
            True if the word is successfully deleted, or False if the
            word is not found.
        """
        if key not in self._words:
            return False
        del self._words[key]
        # look for the next longest word if we just deleted the
        # longest word
        if len(key) == self._max_length:
            self._max_length = max(map(len, self._words.keys()))

        # create deletes
        edits = self._edits_prefix(key)
        for delete in edits:
            self._deletes[delete].remove(key)
        return True

    def load_bigram_dictionary(self, corpus, term_index, count_index,
                               separator=None, encoding=None):
        """Load multiple dictionary entries from a file of
        word/frequency count pairs

        **NOTE**: Merges with any dictionary data already loaded.

        Parameters
        ----------
        corpus : str
            The path+filename of the file.
        term_index : int
            The column position of the word.
        count_index : int
            The column position of the frequency count.
        separator : str, optional
            Separator characters between term(s) and count.
        encoding : str, optional
            Text encoding of the dictionary file

        Returns
        -------
        bool
            True if file loaded, or False if file not found.
        """
        if not os.path.exists(corpus):
            return False
        with open(corpus, "r", encoding=encoding) as infile:
            for line in infile:
                line_parts = line.rstrip().split(separator)
                key = count = None
                if len(line_parts) >= 3 and separator is None:
                    key = "{} {}".format(line_parts[term_index],
                                         line_parts[term_index + 1])
                elif len(line_parts) >= 2 and separator is not None:
                    key = line_parts[term_index]
                if key is not None:
                    count = helpers.try_parse_int64(line_parts[count_index])
                if count is not None:
                    self._bigrams[key] = count
                    if count < self.bigram_count_min:
                        self.bigram_count_min = count
        return True

    def load_dictionary(self, corpus, term_index, count_index,
                        separator=" ", encoding=None):
        """Load multiple dictionary entries from a file of
        word/frequency count pairs.

        **NOTE**: Merges with any dictionary data already loaded.

        Parameters
        ----------
        corpus : str
            The path+filename of the file.
        term_index : int
            The column position of the word.
        count_index : int
            The column position of the frequency count.
        separator : str, optional
            Separator characters between term(s) and count.
        encoding : str, optional
            Text encoding of the dictionary file

        Returns
        -------
        bool
            True if file loaded, or False if file not found.
        """
        if not os.path.exists(corpus):
            return False
        with open(corpus, "r", encoding=encoding) as infile:
            for line in infile:
                line_parts = line.rstrip().split(separator)
                if len(line_parts) >= 2:
                    key = line_parts[term_index]
                    count = helpers.try_parse_int64(line_parts[count_index])
                    if count is not None:
                        self.create_dictionary_entry(key, count)
        return True

    def create_dictionary(self, corpus, encoding=None):
        """Load multiple dictionary words from a file containing plain
        text.

        **NOTE**: Merges with any dictionary data already loaded.

        Parameters
        ----------
        corpus : str
            The path+filename of the file.
        encoding : str, optional
            Text encoding of the corpus file.

        Returns
        -------
        bool
            True if file loaded, or False if file not found.
        """
        if not os.path.exists(corpus):
            return False
        with open(corpus, "r", encoding=encoding) as infile:
            for line in infile:
                for key in self._parse_words(line):
                    self.create_dictionary_entry(key, 1)
        return True

    def save_pickle_stream(self, stream):
        """Pickle :attr:`_deletes`, :attr:`_words`, and
        :attr:`_max_length` into a stream for quicker loading later.

        Parameters
        ----------
        stream : str
            The stream to store the pickle data.
        """
        pickle_data = {
            "deletes": self._deletes,
            "words": self._words,
            "max_length": self._max_length,
            "data_version": self.data_version
        }
        pickle.dump(pickle_data, stream)

    def save_pickle(self, filename, compressed=True):
        """Pickle :attr:`_deletes`, :attr:`_words`, and
        :attr:`_max_length` into a stream for quicker loading later.

        Parameters
        ----------
        filename : str
            The path+filename of the pickle file.
        compressed : bool, optional
            A flag to determine whether to compress the pickled data.
        """
        with (gzip.open if compressed else open)(filename, "wb") as f:
            self.save_pickle_stream(f)

    def load_pickle_stream(self, stream):
        """Load delete combination from stream as pickle. This will
        reduce the loading time compared to running
        :meth:`load_dictionary` again.

        Parameters
        ----------
        stream : str
            The stream from which the pickle data is loaded.

        Returns
        -------
        bool
            True if delete combinations are successfully loaded.
        """
        pickle_data = pickle.load(stream)
        if ("data_version" not in pickle_data
                or pickle_data["data_version"] != self.data_version):
            return False
        self._deletes = pickle_data["deletes"]
        self._words = pickle_data["words"]
        self._max_length = pickle_data["max_length"]
        return True

    def load_pickle(self, filename, compressed=True):
        """Load delete combination from file as pickle. This will
        reduce the loading time compared to running
        :meth:`load_dictionary` again.

        Parameters
        ----------
        filename : str
            The path+filename of the pickle file.
        compressed : bool, optional
            A flag to determine whether to read the pickled data as
            compressed data.

        Returns
        -------
        bool
            True if delete combinations are successfully loaded.
        """
        with (gzip.open if compressed else open)(filename, "rb") as f:
            return self.load_pickle_stream(f)

    def lookup(self, phrase, verbosity, max_edit_distance=None,
               include_unknown=False, ignore_token=None,
               transfer_casing=False):
        """Find suggested spellings for a given phrase word.

        Parameters
        ----------
        phrase : str
            The word being spell checked.
        verbosity : :class:`Verbosity`
            The value controlling the quantity/closeness of the
            returned suggestions.
        max_edit_distance : int, optional
            The maximum edit distance between phrase and suggested
            words. Set to :attr:`_max_dictionary_edit_distance` by
            default
        include_unknown : bool, optional
            A flag to determine whether to include phrase word in
            suggestions, if no words within edit distance found.
        ignore_token : regex pattern, optional
            A regex pattern describing what words/phrases to ignore and
            leave unchanged
        transfer_casing : bool, optional
            A flag to determine whether the casing --- i.e., uppercase
            vs lowercase --- should be carried over from `phrase`.

        Returns
        -------
        suggestions : list
            suggestions is a list of :class:`SuggestItem` objects
            representing suggested correct spellings for the phrase
            word, sorted by edit distance, and secondarily by count
            frequency.

        Raises
        ------
        ValueError
            If `max_edit_distance` is greater than
            :attr:`_max_dictionary_edit_distance`
        """
        if max_edit_distance is None:
            max_edit_distance = self._max_dictionary_edit_distance
        if max_edit_distance > self._max_dictionary_edit_distance:
            raise ValueError("Distance too large")
        suggestions = list()
        phrase_len = len(phrase)

        if transfer_casing:
            original_phrase = phrase
            phrase = phrase.lower()

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
            if transfer_casing:
                suggestions.append(SuggestItem(original_phrase, 0, suggestion_count))
            else:
                suggestions.append(SuggestItem(phrase, 0, suggestion_count))
            # early exit - return exact match, unless caller wants all
            # matches
            if verbosity != Verbosity.ALL:
                return early_exit()

        if (ignore_token is not None
                and re.match(ignore_token, phrase) is not None):
            suggestion_count = 1
            suggestions.append(SuggestItem(phrase, 0, suggestion_count))
            # early exit - return exact match, unless caller wants all
            # matches
            if verbosity != Verbosity.ALL:
                return early_exit()

        # early termination, if we only want to check if word in
        # dictionary or get its frequency e.g. for word segmentation
        if max_edit_distance == 0:
            return early_exit()

        considered_deletes = set()
        considered_suggestions = set()
        # we considered the phrase already in the
        # 'phrase in self._words' above
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

            # early termination: if candidate distance is already
            # higher than suggestion distance, than there are no better
            # suggestions to be expected
            if len_diff > max_edit_distance_2:
                # skip to next candidate if Verbosity.ALL, look no
                # further if Verbosity.TOP or CLOSEST (candidates are
                # ordered by delete distance, so none are closer than
                # current)
                if verbosity == Verbosity.ALL:
                    continue
                break

            if candidate in self._deletes:
                dict_suggestions = self._deletes[candidate]
                for suggestion in dict_suggestions:
                    if suggestion == phrase:
                        continue
                    suggestion_len = len(suggestion)
                    # phrase and suggestion lengths
                    # diff > allowed/current best distance
                    if (abs(suggestion_len - phrase_len) > max_edit_distance_2
                            # suggestion must be for a different delete
                            # string, in same bin only because of hash
                            # collision
                            or suggestion_len < candidate_len
                            # if suggestion len = delete len, then it
                            # either equals delete or is in same bin
                            # only because of hash collision
                            or (suggestion_len == candidate_len
                                and suggestion != candidate)):
                        continue
                    suggestion_prefix_len = min(suggestion_len,
                                                self._prefix_length)
                    if (suggestion_prefix_len > phrase_prefix_len
                            and suggestion_prefix_len - candidate_len > max_edit_distance_2):
                        continue
                    # True Damerau-Levenshtein Edit Distance: adjust
                    # distance, if both distances>0
                    # We allow simultaneous edits (deletes) of
                    # max_edit_distance on on both the dictionary and
                    # the phrase term. For replaces and adjacent
                    # transposes the resulting edit distance stays
                    # <= max_edit_distance. For inserts and deletes the
                    # resulting edit distance might exceed
                    # max_edit_distance. To prevent suggestions of a
                    # higher edit distance, we need to calculate the
                    # resulting edit distance, if there are
                    # simultaneous edits on both sides.
                    # Example: (bank==bnak and bank==bink, but
                    # bank!=kanb and bank!=xban and bank!=baxn for
                    # max_edit_distance=1). Two deletes on each side of
                    # a pair makes them all equal, but the first two
                    # pairs have edit distance=1, the others edit
                    # distance=2.
                    distance = 0
                    min_distance = 0
                    if candidate_len == 0:
                        # suggestions which have no common chars with
                        # phrase (phrase_len<=max_edit_distance &&
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
                    # number of edits in prefix ==maxediddistance AND
                    # no identical suffix, then
                    # editdistance>max_edit_distance and no need for
                    # Levenshtein calculation
                    # (phraseLen >= prefixLength) &&
                    # (suggestionLen >= prefixLength)
                    else:
                        # handles the shortcircuit of min_distance
                        # assignment when first boolean expression
                        # evaluates to False
                        if self._prefix_length - max_edit_distance == candidate_len:
                            min_distance = (min(phrase_len, suggestion_len) -
                                            self._prefix_length)
                        else:
                            min_distance = 0
                        # pylint: disable=C0301,R0916
                        if (self._prefix_length - max_edit_distance == candidate_len
                                and (min_distance > 1
                                     and phrase[phrase_len + 1 - min_distance :] != suggestion[suggestion_len + 1 - min_distance :])
                                or (min_distance > 0
                                    and phrase[phrase_len - min_distance] != suggestion[suggestion_len - min_distance]
                                    and (phrase[phrase_len - min_distance - 1] != suggestion[suggestion_len - min_distance]
                                         or phrase[phrase_len - min_distance] != suggestion[suggestion_len - min_distance - 1]))):
                            continue
                        else:
                            # delete_in_suggestion_prefix is somewhat
                            # expensive, and only pays off when
                            # verbosity is TOP or CLOSEST
                            if ((verbosity != Verbosity.ALL
                                 and not self._delete_in_suggestion_prefix(candidate, candidate_len, suggestion, suggestion_len))
                                    or suggestion in considered_suggestions):
                                continue
                            considered_suggestions.add(suggestion)
                            distance = distance_comparer.compare(
                                phrase, suggestion, max_edit_distance_2)
                            if distance < 0:
                                continue
                    # do not process higher distances than those
                    # already found, if verbosity<ALL (note:
                    # max_edit_distance_2 will always equal
                    # max_edit_distance when Verbosity.ALL)
                    if distance <= max_edit_distance_2:
                        suggestion_count = self._words[suggestion]
                        si = SuggestItem(suggestion, distance,
                                         suggestion_count)
                        if suggestions:
                            if verbosity == Verbosity.CLOSEST:
                                # we will calculate DamLev distance
                                # only to the smallest found distance
                                # so far
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
            # add edits: derive edits (deletes) from candidate (phrase)
            # and add them to candidates list. this is a recursive
            # process until the maximum edit distance has been reached
            if (len_diff < max_edit_distance
                    and candidate_len <= self._prefix_length):
                # do not create edits with edit distance smaller than
                # suggestions already found
                if (verbosity != Verbosity.ALL
                        and len_diff >= max_edit_distance_2):
                    continue
                for i in range(candidate_len):
                    delete = candidate[: i] + candidate[i + 1 :]
                    if delete not in considered_deletes:
                        considered_deletes.add(delete)
                        candidates.append(delete)
        if len(suggestions) > 1:
            suggestions.sort()

        if transfer_casing:
            suggestions = [SuggestItem(
                helpers.transfer_casing_for_similar_text(original_phrase,
                                                         s.term),
                s.distance, s.count) for s in suggestions]

        early_exit()
        return suggestions

    def lookup_compound(self, phrase, max_edit_distance,
                        ignore_non_words=False,
                        transfer_casing=False):
        """`lookup_compound` supports compound aware automatic spelling
        correction of multi-word input strings with three cases:

        1. mistakenly inserted space into a correct word led to two
           incorrect terms
        2. mistakenly omitted space between two correct words led to
           one incorrect combined term
        3. multiple independent input terms with/without spelling
           errors

        Find suggested spellings for a multi-word input string
        (supports word splitting/merging).

        Parameters
        ----------
        phrase : str
            The string being spell checked.
        max_edit_distance : int
            The maximum edit distance between input and suggested
            words.
        ignore_non_words : bool, optional
            A flag to determine whether numbers and acronyms are left
            alone during the spell checking process
        transfer_casing : bool, optional
            A flag to determine whether the casing --- i.e., uppercase
            vs lowercase --- should be carried over from `phrase`.

        Returns
        -------
        suggestions_line : list
            suggestions_line is a list of :class:`SuggestItem` objects
            representing suggested correct spellings for `phrase`.
        """
        # Parse input string into single terms
        term_list_1 = helpers.parse_words(phrase)
        # Second list of single terms with preserved cases so we can
        # ignore acronyms (all cap words)
        if ignore_non_words:
            term_list_2 = helpers.parse_words(phrase, True)
        suggestions = list()
        suggestion_parts = list()
        distance_comparer = EditDistance(self._distance_algorithm)

        # translate every item to its best suggestion, otherwise it
        # remains unchanged
        is_last_combi = False
        for i, __ in enumerate(term_list_1):
            if ignore_non_words:
                if helpers.try_parse_int64(term_list_1[i]) is not None:
                    suggestion_parts.append(SuggestItem(term_list_1[i], 0, 0))
                    continue
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
                        # estimated word occurrence probability
                        # P=10 / (N * 10^word length l)
                        best_2 = SuggestItem(term_list_1[i],
                                             max_edit_distance + 1,
                                             10 // 10 ** len(term_list_1[i]))
                    # distance_1=edit distance between 2 split terms and
                    # their best corrections : als comparative value
                    # for the combination
                    distance_1 = best_1.distance + best_2.distance
                    if (distance_1 >= 0
                            and (suggestions_combi[0].distance + 1 < distance_1
                                 or (suggestions_combi[0].distance + 1 == distance_1
                                     and (suggestions_combi[0].count > best_1.count / self.N * best_2.count)))):
                        suggestions_combi[0].distance += 1
                        suggestion_parts[-1] = suggestions_combi[0]
                        is_last_combi = True
                        continue
            is_last_combi = False

            # alway split terms without suggestion / never split terms
            # with suggestion ed=0 / never split single char terms
            if suggestions and (suggestions[0].distance == 0
                                or len(term_list_1[i]) == 1):
                # choose best suggestion
                suggestion_parts.append(suggestions[0])
            else:
                # if no perfect suggestion, split word into pairs
                suggestion_split_best = None
                # add original term
                if suggestions:
                    suggestion_split_best = suggestions[0]
                if len(term_list_1[i]) > 1:
                    for j in range(1, len(term_list_1[i])):
                        part_1 = term_list_1[i][: j]
                        part_2 = term_list_1[i][j :]
                        suggestions_1 = self.lookup(part_1, Verbosity.TOP,
                                                    max_edit_distance)
                        if suggestions_1:
                            suggestions_2 = self.lookup(part_2, Verbosity.TOP,
                                                        max_edit_distance)
                            if suggestions_2:
                                # select best suggestion for split pair
                                tmp_term = (suggestions_1[0].term + " " +
                                            suggestions_2[0].term)
                                tmp_distance = distance_comparer.compare(
                                    term_list_1[i], tmp_term,
                                    max_edit_distance)
                                if tmp_distance < 0:
                                    tmp_distance = max_edit_distance + 1
                                if suggestion_split_best is not None:
                                    if tmp_distance > suggestion_split_best.distance:
                                        continue
                                    if tmp_distance < suggestion_split_best.distance:
                                        suggestion_split_best = None
                                if tmp_term in self._bigrams:
                                    tmp_count = self._bigrams[tmp_term]
                                    # increase count, if split
                                    # corrections are part of or
                                    # identical to input single term
                                    # correction exists
                                    if suggestions:
                                        best_si = suggestions[0]
                                        # alternatively remove the
                                        # single term from
                                        # suggestion_split, but then
                                        # other splittings could win
                                        if suggestions_1[0].term + suggestions_2[0].term == term_list_1[i]:
                                            # make count bigger than
                                            # count of single term
                                            # correction
                                            tmp_count = max(tmp_count,
                                                            best_si.count + 2)
                                        elif (suggestions_1[0].term == best_si.term
                                              or suggestions_2[0].term == best_si.term):
                                            # make count bigger than
                                            # count of single term
                                            # correction
                                            tmp_count = max(tmp_count,
                                                            best_si.count + 1)
                                    # no single term correction exists
                                    elif suggestions_1[0].term + suggestions_2[0].term == term_list_1[i]:
                                        tmp_count = max(
                                            tmp_count,
                                            max(suggestions_1[0].count,
                                                suggestions_2[0].count) + 2)
                                else:
                                    # The Naive Bayes probability of
                                    # the word combination is the
                                    # product of the two word
                                    # probabilities: P(AB)=P(A)*P(B)
                                    # use it to estimate the frequency
                                    # count of the combination, which
                                    # then is used to rank/select the
                                    # best splitting variant
                                    tmp_count = min(
                                        self.bigram_count_min,
                                        int(suggestions_1[0].count /
                                            self.N * suggestions_2[0].count))
                                suggestion_split = SuggestItem(
                                    tmp_term, tmp_distance, tmp_count)
                                if (suggestion_split_best is None or
                                        suggestion_split.count > suggestion_split_best.count):
                                    suggestion_split_best = suggestion_split

                    if suggestion_split_best is not None:
                        # select best suggestion for split pair
                        suggestion_parts.append(suggestion_split_best)
                        self._replaced_words[term_list_1[i]] = suggestion_split_best
                    else:
                        si = SuggestItem(term_list_1[i],
                                         max_edit_distance + 1,
                                         int(10 / 10 ** len(term_list_1[i])))
                        suggestion_parts.append(si)
                        self._replaced_words[term_list_1[i]] = si
                else:
                    # estimated word occurrence probability
                    # P=10 / (N * 10^word length l)
                    si = SuggestItem(term_list_1[i], max_edit_distance + 1,
                                     int(10 / 10 ** len(term_list_1[i])))
                    suggestion_parts.append(si)
                    self._replaced_words[term_list_1[i]] = si
        joined_term = ""
        joined_count = self.N
        for si in suggestion_parts:
            joined_term += si.term + " "
            joined_count *= si.count / self.N
        joined_term = joined_term.rstrip()
        if transfer_casing:
            joined_term = helpers.transfer_casing_for_similar_text(phrase,
                                                                   joined_term)
        suggestion = SuggestItem(joined_term,
                                 distance_comparer.compare(
                                     phrase, joined_term, 2 ** 31 - 1),
                                 int(joined_count))
        suggestions_line = list()
        suggestions_line.append(suggestion)

        return suggestions_line

    def word_segmentation(self, phrase, max_edit_distance=None,
                          max_segmentation_word_length=None,
                          ignore_token=None):
        """`word_segmentation` divides a string into words by inserting
        missing spaces at the appropriate positions misspelled words
        are corrected and do not affect segmentation existing spaces
        are allowed and considered for optimum segmentation

        `word_segmentation` uses a novel approach *without* recursion.
        https://medium.com/@wolfgarbe/fast-word-segmentation-for-noisy-text-2c2c41f9e8da
        While each string of length n can be segmented in 2^n−1
        possible compositions
        https://en.wikipedia.org/wiki/Composition_(combinatorics)
        `word_segmentation` has a linear runtime O(n) to find the optimum
        composition

        Find suggested spellings for a multi-word input string
        (supports word splitting/merging).

        Parameters
        ----------
        phrase : str
            The string being spell checked.
        max_segmentation_word_length : int
            The maximum word length that should be considered.
        max_edit_distance : int, optional
            The maximum edit distance between input and corrected words
            (0=no correction/segmentation only).
        ignore_token : regex pattern, optional
            A regex pattern describing what words/phrases to ignore and
            leave unchanged

        Returns
        -------
        compositions[idx] :class:`Composition`
            The word segmented string, the word segmented and spelling
            corrected string, the edit distance sum between input
            string and corrected string, the sum of word occurence
            probabilities in log scale (a measure of how common and
            probable the corrected segmentation is).
        """
        if max_edit_distance is None:
            max_edit_distance = self._max_dictionary_edit_distance
        if max_segmentation_word_length is None:
            max_segmentation_word_length = self._max_length
        array_size = min(max_segmentation_word_length, len(phrase))
        compositions = [Composition()] * array_size
        circular_index = cycle(range(array_size))
        idx = -1

        # outer loop (column): all possible part start positions
        for j in range(len(phrase)):
            # inner loop (row): all possible part lengths (from start
            # position): part can't be bigger than longest word in
            # dictionary (other than long unknown word)
            imax = min(len(phrase) - j, max_segmentation_word_length)
            for i in range(1, imax + 1):
                # get top spelling correction/ed for part
                part = phrase[j : j + i]
                separator_len = 0
                top_ed = 0
                top_log_prob = 0.0
                top_result = ""

                if part[0].isspace():
                    # remove space for levensthein calculation
                    part = part[1 :]
                else:
                    # add ed+1: space did not exist, had to be inserted
                    separator_len = 1

                # remove space from part1, add number of removed spaces
                # to top_ed
                top_ed += len(part)
                # remove space.
                # add number of removed spaces to ed
                part = part.replace(" ", "")
                top_ed -= len(part)

                results = self.lookup(part, Verbosity.TOP, max_edit_distance,
                                      ignore_token=ignore_token)
                if results:
                    top_result = results[0].term
                    top_ed += results[0].distance
                    # Naive Bayes Rule. We assume the word
                    # probabilities of two words to be independent.
                    # Therefore the resulting probability of the word
                    # combination is the product of the two word
                    # probabilities. Instead of computing the product
                    # of probabilities we are computing the sum of the
                    # logarithm of probabilities because the
                    # probabilities of words are about 10^-10, the
                    # product of many such small numbers could exceed
                    # (underflow) the floating number range and become
                    # zero. log(ab)=log(a)+log(b)
                    top_log_prob = math.log10(float(results[0].count) /
                                              float(self.N))
                else:
                    top_result = part
                    # default, if word not found. otherwise long input
                    # text would win as long unknown word (with
                    # ed=edmax+1), although there there should many
                    # spaces inserted
                    top_ed += len(part)
                    top_log_prob = math.log10(10.0 / self.N /
                                              math.pow(10.0, len(part)))

                dest = (i + idx) % array_size
                # set values in first loop
                if j == 0:
                    compositions[dest] = Composition(part, top_result,
                                                     top_ed, top_log_prob)
                # pylint: disable=C0301,R0916
                elif (i == max_segmentation_word_length
                      # replace values if better log_prob_sum, if same
                      # edit distance OR one space difference
                      or ((compositions[idx].distance_sum + top_ed == compositions[dest].distance_sum
                           or compositions[idx].distance_sum + separator_len + top_ed == compositions[dest].distance_sum)
                          and compositions[dest].log_prob_sum < compositions[idx].log_prob_sum + top_log_prob)
                      # replace values if smaller edit distance
                      or compositions[idx].distance_sum + separator_len + top_ed < compositions[dest].distance_sum):
                    compositions[dest] = Composition(
                        compositions[idx].segmented_string + " " + part,
                        compositions[idx].corrected_string + " " + top_result,
                        compositions[idx].distance_sum + separator_len + top_ed,
                        compositions[idx].log_prob_sum + top_log_prob)
            idx = next(circular_index)
        return compositions[idx]

    def _delete_in_suggestion_prefix(self, delete, delete_len, suggestion,
                                     suggestion_len):
        """Check whether all delete chars are present in the suggestion
        prefix in correct order, otherwise this is just a hash
        collision
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

    def _parse_words(self, text):
        """Create a non-unique wordlist from sample text
        language independent (e.g. works with Chinese characters)
        """
        # // \w Alphanumeric characters (including non-latin
        # characters, umlaut characters and digits) plus "_". [^\W_] is
        # the equivalent of \w excluding "_".
        # Compatible with non-latin characters, does not split words at
        # apostrophes.
        # Uses capturing groups to combine a negated set with a
        # character set
        matches = re.findall(r"(([^\W_]|['’])+)", text.lower())
        # The above regex returns ("ghi'jkl", "l") for "ghi'jkl", so we
        # extract the first element
        matches = [match[0] for match in matches]
        return matches

    def _edits(self, word, edit_distance, delete_words):
        """Inexpensive and language independent: only deletes,
        no transposes + replaces + inserts replaces and inserts are
        expensive and language dependent
        """
        edit_distance += 1
        word_len = len(word)
        if word_len > 1:
            for i in range(word_len):
                delete = word[: i] + word[i + 1 :]
                if delete not in delete_words:
                    delete_words.add(delete)
                    # recursion, if maximum edit distance not yet
                    # reached
                    if edit_distance < self._max_dictionary_edit_distance:
                        self._edits(delete, edit_distance, delete_words)
        return delete_words

    def _edits_prefix(self, key):
        hash_set = set()
        if len(key) <= self._max_dictionary_edit_distance:
            hash_set.add("")
        if len(key) > self._prefix_length:
            key = key[: self._prefix_length]
        hash_set.add(key)
        return self._edits(key, 0, hash_set)

    @property
    def below_threshold_words(self):
        return self._below_threshold_words

    @property
    def bigrams(self):
        return self._bigrams

    @property
    def deletes(self):
        return self._deletes

    @property
    def replaced_words(self):
        return self._replaced_words

    @property
    def words(self):
        return self._words

    @property
    def word_count(self):
        return len(self._words)

class SuggestItem(object):
    """Spelling suggestion returned from :meth:`lookup`.

    Parameters
    ----------
    term : str
        The suggested word.
    distance : int
        Edit distance from search word.
    count : int or float
        Frequency of suggestion in dictionary or Naive Bayes
        probability of the individual suggestion parts

    Attributes
    ----------
    _term : str
        The suggested correctly spelled word.
    _distance : int
        Edit distance between searched for word and suggestion.
    _count : int or float
        Frequency of suggestion in the dictionary (a measure of how
        common the word is) or Naive Bayes probability of the
        individual suggestion parts in :meth:`lookup_compound`.
    """
    def __init__(self, term, distance, count):
        self._term = term
        self._distance = distance
        self._count = count

    def __eq__(self, other):
        """
        Returns
        -------
        bool
            True if both distance and frequency count are the same
        """
        if self._distance == other.distance:
            return self._count == other.count
        else:
            return self._distance == other.distance

    def __lt__(self, other):
        """
        Returns
        -------
        bool
            Order by distance ascending, then by frequency count
            descending
        """
        if self._distance == other.distance:
            return self._count > other.count
        else:
            return self._distance < other.distance

    def __str__(self):
        """
        Returns
        -------
        str
            Displays attributes as "term, distance, count"
        """
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

Composition = namedtuple("Composition",
                         ["segmented_string", "corrected_string",
                          "distance_sum", "log_prob_sum"])
Composition.__new__.__defaults__ = (None,) * len(Composition._fields)
Composition.__doc__ = """Used by :meth:`word_segmentation`

**NOTE**: "Parameters" is used instead "Attributes" due to a bug which
overwrites attribute descriptions.

Parameters
----------
segmented_string : str
    The word segmented string.
corrected_string : str
    The spelling corrected string.
distance_sum : int
    The sum of edit distance between input string and corrected string
log_prob_sum : float
    The sum of word occurrence probabilities in log scale (a measure of
    how common and probable the corrected segmentation is).
"""

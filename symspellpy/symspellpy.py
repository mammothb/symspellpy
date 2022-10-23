# MIT License
#
# Copyright (c) 2022 mmb L (Python port)
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
.. module:: symspellpy
   :synopsis: Module for Symmetric Delete spelling correction algorithm.
"""

import logging
import math
import re
import string
import sys
import unicodedata
from collections import defaultdict
from itertools import cycle
from pathlib import Path
from typing import IO, Dict, List, Optional, Pattern, Set, Union

from symspellpy import helpers
from symspellpy.composition import Composition
from symspellpy.editdistance import DistanceAlgorithm, EditDistance
from symspellpy.pickle_mixin import PickleMixin
from symspellpy.suggest_item import SuggestItem
from symspellpy.verbosity import Verbosity

logger = logging.getLogger(__name__)
WORD_PATTERN = re.compile(r"(([^\W_]|['’])+)")


class SymSpell(PickleMixin):
    """Symmetric Delete spelling correction algorithm.

    `initial_capacity` from the original code is omitted since python cannot
    preallocate memory. `compact_mask` from the original code is omitted since
    we're not mapping suggested corrections to hash codes.

    Args:
        max_dictionary_edit_distance: Maximum edit distance for doing lookups.
        prefix_length: The length of word prefixes used for spell checking.
        count_threshold: The minimum frequency count for dictionary words to be
            considered correct spellings.

    Attributes:
        _max_dictionary_edit_distance (int): Maximum dictionary term length.
        _prefix_length (int): The length of word prefixes used for spell
            checking.
        _count_threshold (int): A threshold may be specified, when a term occurs
            so frequently in the corpus that it is considered a valid word for
            spelling correction.
        _distance_algorithm (DistanceAlgorithm): Edit distance algorithms.
        _max_length (int): Length of longest word in the dictionary.

    Raises:
        ValueError: If `max_dictionary_edit_distance` is negative.
        ValueError: If `prefix_length` is less than 1 or not greater than
            `max_dictionary_edit_distance`.
        ValueError: If `count_threshold` is negative.
    """

    data_version = 3
    # Number of all words in the corpus used to generate the frequency
    # dictionary. This is used to calculate the word occurrence probability p
    # from word counts c : p=c/N. N equals the sum of all counts c in the
    # dictionary only if the dictionary is complete, but not if the dictionary is
    # truncated or filtered.
    N = 1024908267229
    bigram_count_min = sys.maxsize

    def __init__(
        self,
        max_dictionary_edit_distance: int = 2,
        prefix_length: int = 7,
        count_threshold: int = 1,
    ) -> None:
        if max_dictionary_edit_distance < 0:
            raise ValueError("max_dictionary_edit_distance cannot be negative")
        if prefix_length < 1:
            raise ValueError("prefix_length cannot be less than 1")
        if prefix_length <= max_dictionary_edit_distance:
            raise ValueError(
                "prefix_length must be greater than max_dictionary_edit_distance"
            )
        if count_threshold < 0:
            raise ValueError("count_threshold cannot be negative")
        self._words: Dict[str, int] = {}
        self._below_threshold_words: Dict[str, int] = {}
        self._bigrams: Dict[str, int] = {}
        self._deletes: Dict[str, List[str]] = defaultdict(list)
        self._replaced_words: Dict[str, SuggestItem] = {}

        self._max_dictionary_edit_distance = max_dictionary_edit_distance
        self._prefix_length = prefix_length
        self._count_threshold = count_threshold
        self._distance_algorithm = DistanceAlgorithm.DAMERAU_OSA_FAST
        self._max_length = 0

    @property
    def below_threshold_words(self) -> (Dict[str, int]):
        """Dictionary of unique words that are below the count threshold for
        being considered correct spellings.
        """
        return self._below_threshold_words

    @property
    def bigrams(self) -> Dict[str, int]:
        """Dictionary of unique correct spelling bigrams, and the frequency count
        for each word.
        """
        return self._bigrams

    @property
    def deletes(self) -> Dict[str, List[str]]:
        """Dictionary that contains a mapping of lists of suggested correction
        words to the original words and the deletes derived from them. A list of
        suggestions might have a single suggestion, or multiple suggestions.
        """
        return self._deletes

    @property
    def distance_algorithm(self) -> DistanceAlgorithm:
        """The current distance algorithm."""
        return self._distance_algorithm

    @distance_algorithm.setter
    def distance_algorithm(self, value: DistanceAlgorithm) -> None:
        if not isinstance(value, DistanceAlgorithm):
            raise TypeError(
                "can only assign DistanceAlgorithm type values to distance_algorithm"
            )
        self._distance_algorithm = value

    @property
    def entry_count(self) -> int:
        """Number of unique correct spelling words."""
        return len(self._deletes)

    @property
    def replaced_words(self) -> Dict[str, SuggestItem]:
        """Dictionary corrected/modified words."""
        return self._replaced_words

    @property
    def words(self) -> Dict[str, int]:
        """Dictionary of unique correct spelling words, and the frequency count
        for each word.
        """
        return self._words

    @property
    def word_count(self) -> int:
        """Number of unique correct spelling words."""
        return len(self._words)

    def create_dictionary(
        self, corpus: Union[Path, str, IO[str]], encoding: Optional[str] = None
    ) -> bool:
        """Loads multiple dictionary words from a file containing plain text.

        **NOTE**: Merges with any dictionary data already loaded.

        Args:
            corpus: The path+filename of the file or afile object of the
                dictionary.
            encoding: Text encoding of the corpus file.

        Returns:
            ``True`` if file loaded, or ``False`` if file not found.
        """
        if isinstance(corpus, (Path, str)):
            corpus = Path(corpus)
            if not corpus.exists():
                logger.error(f"Corpus not found at {corpus}.")
                return False
            for key in self._parse_words(corpus.read_text(encoding=encoding)):
                self.create_dictionary_entry(key, 1)
        else:
            for line in corpus:
                for key in self._parse_words(line):
                    self.create_dictionary_entry(key, 1)
        return True

    def create_dictionary_entry(self, key: str, count: int) -> bool:
        """Creates/updates an entry in the dictionary.

        For every word there are deletes with an edit distance of
        1..max_edit_distance created and added to the dictionary. Every delete
        entry has a suggestions list, which points to the original term(s) it was
        created from. The dictionary may be dynamically updated (word frequency
        and new words) at any time by calling create_dictionary_entry.

        Args:
            key: The word to add to dictionary.
            count: The frequency count for word.

        Returns:
            ``True`` if the word was added as a new correctly spelled word, or
            ``False`` if the word is added as a below threshold word, or updates
            an existing correctly spelled word.
        """
        if count <= 0:
            # Early return if count is zero, as it can't change anything
            if self._count_threshold > 0:
                return False
            count = 0

        # Look first in below threshold words, update count, and allow promotion
        # to correct spelling word if count reaches threshold threshold must be
        # >1 for there to be the possibility of low threshold words
        if self._count_threshold > 1 and key in self._below_threshold_words:
            count_previous = self._below_threshold_words[key]
            # calculate new count for below threshold word
            count = helpers.increment_count(count, count_previous)
            # has reached threshold - remove from below threshold collection (it
            # will be added to correct words below)
            if count >= self._count_threshold:
                self._below_threshold_words.pop(key)
            else:
                self._below_threshold_words[key] = count
                return False
        elif key in self._words:
            count_previous = self._words[key]
            # just update count if it's an already added above threshold word
            self._words[key] = helpers.increment_count(count, count_previous)
            return False
        elif count < self._count_threshold:
            # new or existing below threshold word
            self._below_threshold_words[key] = count
            return False

        # what we have at this point is a new, above threshold word
        self._words[key] = count

        # edits/suggestions are created only once, no matter how often word
        # occurs. edits/suggestions are created as soon as the word occurs in the
        # corpus, even if the same term existed before in the dictionary as an
        # edit from another word
        if len(key) > self._max_length:
            self._max_length = len(key)

        # create deletes
        edits = self._edits_prefix(key)
        for delete in edits:
            self._deletes[delete].append(key)
        return True

    def delete_dictionary_entry(self, key: str) -> bool:
        """Deletes an entry in the dictionary.

        If the deleted entry is the longest word, update :attr:`_max_length`
        with the next longest word.

        Args:
            key: The word to add to dictionary.

        Returns:
            ``True`` if the word is successfully deleted, or ``False`` if the
            word is not found.
        """
        if key not in self._words:
            return False
        del self._words[key]
        # look for the next longest word if we just deleted the longest word
        if len(key) == self._max_length:
            self._max_length = max(map(len, self._words.keys()))

        # create deletes
        edits = self._edits_prefix(key)
        for delete in edits:
            self._deletes[delete].remove(key)
        return True

    def load_bigram_dictionary(
        self,
        corpus: Union[Path, str],
        term_index: int,
        count_index: int,
        separator: Optional[str] = None,
        encoding: Optional[str] = None,
    ) -> bool:
        """Loads multiple dictionary entries from a file of word/frequency count
        pairs.

        **NOTE**: Merges with any dictionary data already loaded.

        Args:
            corpus: The path+filename of the file.
            term_index: The column position of the word.
            count_index: The column position of the frequency count.
            separator: Separator characters between term(s) and count.
            encoding: Text encoding of the dictionary file.

        Returns:
            ``True`` if file loaded, or ``False`` if file not found.
        """
        corpus = Path(corpus)
        if not corpus.exists():
            logger.error(f"Bigram dictionary file not found at {corpus}.")
            return False
        with open(corpus, "r", encoding=encoding) as infile:
            return self._load_bigram_dictionary_stream(
                infile, term_index, count_index, separator
            )

    def load_dictionary(
        self,
        corpus: Union[Path, str],
        term_index: int,
        count_index: int,
        separator: str = " ",
        encoding: Optional[str] = None,
    ):
        """Loads multiple dictionary entries from a file of word/frequency count
        pairs.

        **NOTE**: Merges with any dictionary data already loaded.

        Args:
            corpus: The path+filename of the file.
            term_index: The column position of the word.
            count_index: The column position of the frequency count.
            separator: Separator characters between term(s) and count.
            encoding: Text encoding of the dictionary file.

        Returns:
            ``True`` if file loaded, or ``False`` if file not found.
        """
        corpus = Path(corpus)
        if not corpus.exists():
            logger.error(f"Dictionary file not found at {corpus}.")
            return False
        with open(corpus, "r", encoding=encoding) as infile:
            return self._load_dictionary_stream(
                infile, term_index, count_index, separator
            )

    def lookup(
        self,
        phrase: str,
        verbosity: Verbosity,
        max_edit_distance: Optional[int] = None,
        include_unknown: bool = False,
        ignore_token: Optional[Pattern[str]] = None,
        transfer_casing: bool = False,
    ) -> List[SuggestItem]:
        """Finds suggested spellings for a given phrase word.

        Args:
            phrase: The word being spell checked.
            verbosity: The value controlling the quantity/closeness of the
                returned suggestions.
            max_edit_distance: The maximum edit distance between phrase and
                suggested words. Set to :attr:`_max_dictionary_edit_distance` by
                default.
            include_unknown: A flag to determine whether to include phrase word
                in suggestions, if no words within edit distance found.
            ignore_token: A regex pattern describing what words/phrases to ignore
                and leave unchanged.
            transfer_casing: A flag to determine whether the casing --- i.e.,
                uppercase vs lowercase --- should be carried over from `phrase`.

        Returns:
            A list of :class:`SuggestItem` objects representing suggested correct
            spellings for the phrase word, sorted by edit distance, and
            secondarily by count frequency.

        Raises:
            ValueError: If `max_edit_distance` is greater than
                :attr:`_max_dictionary_edit_distance`
        """
        if max_edit_distance is None:
            max_edit_distance = self._max_dictionary_edit_distance
        if max_edit_distance > self._max_dictionary_edit_distance:
            raise ValueError("distance too large")
        suggestions: List[SuggestItem] = []
        phrase_len = len(phrase)

        if transfer_casing:
            original_phrase = phrase
            phrase = phrase.lower()

        def early_exit():
            if include_unknown and not suggestions:
                suggestions.append(SuggestItem(phrase, max_edit_distance + 1, 0))
            return suggestions

        # early exit - word is too big to possibly match any words
        if phrase_len - max_edit_distance > self._max_length:
            return early_exit()

        # quick look for exact match
        if phrase in self._words:
            suggestion_count = self._words[phrase]
            if transfer_casing:
                suggestions.append(SuggestItem(original_phrase, 0, suggestion_count))
            else:
                suggestions.append(SuggestItem(phrase, 0, suggestion_count))
            # early exit - return exact match, unless caller wants all matches
            if verbosity != Verbosity.ALL:
                return early_exit()

        if ignore_token is not None and re.match(ignore_token, phrase) is not None:
            suggestion_count = 1
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
        candidates = []

        # add original prefix
        phrase_prefix_len = phrase_len
        if phrase_prefix_len > self._prefix_length:
            phrase_prefix_len = self._prefix_length
            candidates.append(phrase[:phrase_prefix_len])
        else:
            candidates.append(phrase)
        distance_comparer = EditDistance(self._distance_algorithm)
        while candidate_pointer < len(candidates):
            candidate = candidates[candidate_pointer]
            candidate_pointer += 1
            candidate_len = len(candidate)
            len_diff = phrase_prefix_len - candidate_len

            # early termination: if candidate distance is already higher than
            # suggestion distance, then there are no better suggestions to be
            # expected
            if len_diff > max_edit_distance_2:
                # skip to next candidate if Verbosity.ALL, look no
                # further if Verbosity.TOP or CLOSEST (candidates are
                # ordered by delete distance, so none are closer than
                # current)
                if verbosity == Verbosity.ALL:  # pragma: no cover
                    # `max_edit_distance_2`` only updated when
                    # verbosity != ALL. New candidates are generated from
                    # deletes so it keeps getting shorter. This should never
                    # be reached.
                    continue
                break  # pragma: no cover, "peephole" optimization, http://bugs.python.org/issue2506

            if candidate in self._deletes:
                dict_suggestions = self._deletes[candidate]
                for suggestion in dict_suggestions:
                    if suggestion == phrase:
                        continue
                    suggestion_len = len(suggestion)
                    # phrase and suggestion lengths diff > allowed/current best
                    # distance
                    if (
                        abs(suggestion_len - phrase_len) > max_edit_distance_2
                        # suggestion must be for a different delete string, in
                        # same bin only because of hash collision
                        or suggestion_len < candidate_len
                        # if suggestion len = delete len, then it either equals
                        # delete or is in same bin only because of hash collision
                        or (suggestion_len == candidate_len and suggestion != candidate)
                    ):
                        continue  # pragma: no cover, "peephole" optimization, http://bugs.python.org/issue2506
                    suggestion_prefix_len = min(suggestion_len, self._prefix_length)
                    if (
                        suggestion_prefix_len > phrase_prefix_len
                        and suggestion_prefix_len - candidate_len > max_edit_distance_2
                    ):
                        continue
                    # True Damerau-Levenshtein Edit Distance: adjust distance,
                    # if both distances>0. We allow simultaneous edits (deletes)
                    # of max_edit_distance on on both the dictionary and the
                    # phrase term. For replaces and adjacent transposes the
                    # resulting edit distance stays <= max_edit_distance. For
                    # inserts and deletes the resulting edit distance might
                    # exceed max_edit_distance. To prevent suggestions of a
                    # higher edit distance, we need to calculate the resulting
                    # edit distance, if there are simultaneous edits on both
                    # sides. Example: (bank==bnak and bank==bink, but bank!=kanb
                    # and bank!=xban and bank!=baxn for max_edit_distance=1).
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
                        if (
                            distance > max_edit_distance_2
                            or suggestion in considered_suggestions
                        ):
                            continue
                    elif suggestion_len == 1:
                        # This should always be phrase_len - 1? Since
                        # suggestions are generated from deletes of the input
                        # phrase
                        distance = (
                            phrase_len
                            if phrase.index(suggestion[0]) < 0
                            else phrase_len - 1
                        )
                        # `suggestion` only gets added to
                        # `considered_suggestions` when `suggestion_len>1`.
                        # Given the max_dictionary_edit_distance and
                        # prefix_length restrictions, `distance`` should never
                        # be >max_edit_distance_2
                        if (
                            distance > max_edit_distance_2
                            or suggestion in considered_suggestions
                        ):  # pragma: no cover
                            continue
                    # number of edits in prefix ==maxeditdistance AND no
                    # identical suffix, then editdistance>max_edit_distance and
                    # no need for Levenshtein calculation
                    # (phraseLen >= prefixLength) &&
                    # (suggestionLen >= prefixLength)
                    else:
                        # handles the shortcircuit of min_distance assignment
                        # when first boolean expression evaluates to False
                        if self._prefix_length - max_edit_distance == candidate_len:
                            min_distance = (
                                min(phrase_len, suggestion_len) - self._prefix_length
                            )
                        else:
                            min_distance = 0
                        # pylint: disable=too-many-boolean-expressions
                        if (
                            self._prefix_length - max_edit_distance == candidate_len
                            and (
                                min_distance > 1
                                and phrase[phrase_len + 1 - min_distance :]
                                != suggestion[suggestion_len + 1 - min_distance :]
                            )
                            or (
                                min_distance > 0
                                and phrase[phrase_len - min_distance]
                                != suggestion[suggestion_len - min_distance]
                                and (
                                    phrase[phrase_len - min_distance - 1]
                                    != suggestion[suggestion_len - min_distance]
                                    or phrase[phrase_len - min_distance]
                                    != suggestion[suggestion_len - min_distance - 1]
                                )
                            )
                        ):
                            continue
                        # delete_in_suggestion_prefix is somewhat expensive, and
                        # only pays off when verbosity is TOP or CLOSEST
                        if suggestion in considered_suggestions:
                            continue
                        considered_suggestions.add(suggestion)
                        distance = distance_comparer.compare(
                            phrase, suggestion, max_edit_distance_2
                        )
                        if distance < 0:
                            continue
                    # do not process higher distances than those already found,
                    # if verbosity<ALL (note: max_edit_distance_2 will always
                    # equal max_edit_distance when Verbosity.ALL)
                    if distance <= max_edit_distance_2:  # pragma: no branch
                        suggestion_count = self._words[suggestion]
                        item = SuggestItem(suggestion, distance, suggestion_count)
                        if suggestions:
                            if verbosity == Verbosity.CLOSEST:
                                # we will calculate DamLev distance only to the
                                # smallest found distance so far
                                if distance < max_edit_distance_2:
                                    suggestions = []
                            elif verbosity == Verbosity.TOP:
                                if (  # pragma: no branch, "peephole" optimization, http://bugs.python.org/issue2506
                                    distance < max_edit_distance_2
                                    or suggestion_count > suggestions[0].count
                                ):
                                    max_edit_distance_2 = distance
                                    suggestions[0] = item
                                continue
                        if verbosity != Verbosity.ALL:
                            max_edit_distance_2 = distance
                        suggestions.append(item)
            # add edits: derive edits (deletes) from candidate (phrase) and add
            # them to candidates list. this is a recursive process until the
            # maximum edit distance has been reached
            if len_diff < max_edit_distance and candidate_len <= self._prefix_length:
                # do not create edits with edit distance smaller than
                # suggestions already found
                if verbosity != Verbosity.ALL and len_diff >= max_edit_distance_2:
                    continue
                for i in range(candidate_len):
                    delete = candidate[:i] + candidate[i + 1 :]
                    if delete not in considered_deletes:
                        considered_deletes.add(delete)
                        candidates.append(delete)
        if len(suggestions) > 1:
            suggestions.sort()

        if transfer_casing:
            suggestions = [
                SuggestItem(
                    helpers.case_transfer_similar(original_phrase, s.term),
                    s.distance,
                    s.count,
                )
                for s in suggestions
            ]

        early_exit()
        return suggestions

    def lookup_compound(
        self,
        phrase: str,
        max_edit_distance: int,
        ignore_non_words: bool = False,
        transfer_casing: bool = False,
        split_by_space: bool = False,
        ignore_term_with_digits: bool = False,
    ) -> List[SuggestItem]:
        """`lookup_compound` supports compound aware automatic spelling
        correction of multi-word input strings with three cases:

        1. mistakenly inserted space into a correct word led to two incorrect
           terms
        2. mistakenly omitted space between two correct words led to one
           incorrect combined term
        3. multiple independent input terms with/without spelling errors

        Find suggested spellings for a multi-word input string
        (supports word splitting/merging).

        Args:
            phrase: The string being spell checked.
            max_edit_distance: The maximum edit distance between input and
                suggested words.
            ignore_non_words: A flag to determine whether numbers and acronyms
                are left alone during the spell checking process.
            transfer_casing: A flag to determine whether the casing --- i.e.,
                uppercase vs lowercase --- should be carried over from `phrase`.
            split_by_space: Splits the phrase into words simply based on space.
            ignore_any_term_with_digits: A flag to determine whether any term
                with digits is left alone during the spell checking process. Only
                works when ``ignore_non_words` is also ``True``.

        Returns:
            A list of :class:`SuggestItem` objects representing suggested correct
            spellings for `phrase`.
        """
        # Parse input string into single terms
        terms_1 = helpers.parse_words(phrase, split_by_space=split_by_space)
        # Second list of single terms with preserved cases so we can ignore
        # acronyms (all cap words)
        if ignore_non_words:
            terms_2 = helpers.parse_words(phrase, True, split_by_space)
        suggestions = []
        suggestion_parts = []
        distance_comparer = EditDistance(self._distance_algorithm)

        # translate every item to its best suggestion, otherwise it remains
        # unchanged
        is_last_combi = False
        for i, _ in enumerate(terms_1):
            if ignore_non_words:
                if helpers.try_parse_int64(terms_1[i]) is not None:
                    suggestion_parts.append(SuggestItem(terms_1[i], 0, self.N))
                    continue
                if helpers.is_acronym(terms_2[i], ignore_term_with_digits):
                    suggestion_parts.append(SuggestItem(terms_2[i], 0, self.N))
                    continue
            suggestions = self.lookup(terms_1[i], Verbosity.TOP, max_edit_distance)
            # combi check, always before split
            if i > 0 and not is_last_combi:
                suggestions_combi = self.lookup(
                    terms_1[i - 1] + terms_1[i],
                    Verbosity.TOP,
                    max_edit_distance,
                )
                if suggestions_combi:
                    best_1 = suggestion_parts[-1]
                    if suggestions:
                        best_2 = suggestions[0]
                    else:
                        # estimated word occurrence probability
                        # P=10 / (N * 10^word length l)
                        best_2 = SuggestItem.create_with_probability(
                            terms_1[i], max_edit_distance + 1
                        )
                    # distance_1=edit distance between 2 split terms and their
                    # best corrections: als comparative value for the combination
                    distance_1 = best_1.distance + best_2.distance
                    if distance_1 >= 0 and (
                        suggestions_combi[0].distance + 1 < distance_1
                        or (
                            suggestions_combi[0].distance + 1 == distance_1
                            and (
                                suggestions_combi[0].count
                                > best_1.count / self.N * best_2.count
                            )
                        )
                    ):
                        suggestions_combi[0].distance += 1
                        suggestion_parts[-1] = suggestions_combi[0]
                        self._replaced_words[terms_1[i - 1]] = suggestions_combi[0]
                        is_last_combi = True
                        continue
            is_last_combi = False

            # alway split terms without suggestion / never split terms with
            # suggestion ed=0 / never split single char terms
            if suggestions and (suggestions[0].distance == 0 or len(terms_1[i]) == 1):
                # choose best suggestion
                suggestion_parts.append(suggestions[0])
            else:
                # if no perfect suggestion, split word into pairs
                suggestion_split_best = None
                # add original term
                if suggestions:
                    suggestion_split_best = suggestions[0]
                if len(terms_1[i]) > 1:
                    for j in range(1, len(terms_1[i])):
                        part_1 = terms_1[i][:j]
                        part_2 = terms_1[i][j:]
                        suggestions_1 = self.lookup(
                            part_1, Verbosity.TOP, max_edit_distance
                        )
                        if not suggestions_1:
                            continue
                        suggestions_2 = self.lookup(
                            part_2, Verbosity.TOP, max_edit_distance
                        )
                        if not suggestions_2:
                            continue
                        # select best suggestion for split pair
                        tmp_term = f"{suggestions_1[0].term} {suggestions_2[0].term}"
                        tmp_distance = distance_comparer.compare(
                            terms_1[i], tmp_term, max_edit_distance
                        )
                        if tmp_distance < 0:
                            tmp_distance = max_edit_distance + 1
                        if suggestion_split_best is not None:
                            if tmp_distance > suggestion_split_best.distance:
                                continue
                            if tmp_distance < suggestion_split_best.distance:
                                suggestion_split_best = None
                        if tmp_term in self._bigrams:
                            tmp_count = self._bigrams[tmp_term]
                            # increase count, if split corrections are part of
                            # or identical to input single term correction exists
                            if suggestions:
                                best_si = suggestions[0]
                                # alternatively remove the single term from
                                # suggestion_split, but then other splittings
                                # could win
                                if (
                                    suggestions_1[0].term + suggestions_2[0].term
                                    == terms_1[i]
                                ):
                                    # make count bigger than count of single
                                    # term correction
                                    tmp_count = max(tmp_count, best_si.count + 2)
                                elif best_si.term in (
                                    suggestions_1[0].term,
                                    suggestions_2[0].term,
                                ):
                                    # make count bigger than count of single
                                    # term correction
                                    tmp_count = max(tmp_count, best_si.count + 1)
                            # no single term correction exists
                            elif (
                                suggestions_1[0].term + suggestions_2[0].term
                                == terms_1[i]
                            ):
                                tmp_count = max(
                                    tmp_count,
                                    max(
                                        suggestions_1[0].count,
                                        suggestions_2[0].count,
                                    )
                                    + 2,
                                )
                        else:
                            # The Naive Bayes probability of the word
                            # combination is the product of the two word
                            # probabilities: P(AB)=P(A)*P(B) use it to estimate
                            # the frequency count of the combination, which then
                            # is used to rank/select the best splitting variant
                            tmp_count = min(
                                self.bigram_count_min,
                                int(
                                    suggestions_1[0].count
                                    / self.N
                                    * suggestions_2[0].count
                                ),
                            )
                        suggestion_split = SuggestItem(
                            tmp_term, tmp_distance, tmp_count
                        )
                        if (
                            suggestion_split_best is None
                            or suggestion_split.count > suggestion_split_best.count
                        ):
                            suggestion_split_best = suggestion_split

                    if suggestion_split_best is not None:
                        # select best suggestion for split pair
                        suggestion_parts.append(suggestion_split_best)
                        self._replaced_words[terms_1[i]] = suggestion_split_best
                    else:
                        item = SuggestItem.create_with_probability(
                            terms_1[i], max_edit_distance + 1
                        )
                        suggestion_parts.append(item)
                        self._replaced_words[terms_1[i]] = item
                else:
                    # estimated word occurrence probability
                    # P=10 / (N * 10^word length l)
                    item = SuggestItem.create_with_probability(
                        terms_1[i], max_edit_distance + 1
                    )
                    suggestion_parts.append(item)
                    self._replaced_words[terms_1[i]] = item
        joined_term = ""
        joined_count: float = self.N
        for item in suggestion_parts:
            joined_term += item.term + " "
            joined_count *= item.count / self.N
        joined_term = joined_term.rstrip()
        if transfer_casing:
            joined_term = helpers.case_transfer_similar(phrase, joined_term)
        suggestion = SuggestItem(
            joined_term,
            distance_comparer.compare(phrase, joined_term, 2 ** 31 - 1),
            int(joined_count),
        )
        return [suggestion]

    def word_segmentation(
        self,
        phrase: str,
        max_edit_distance: Optional[int] = None,
        max_segmentation_word_length: Optional[int] = None,
        ignore_token: Optional[Pattern] = None,
    ) -> Composition:
        """`word_segmentation` divides a string into words by inserting missing
        spaces at the appropriate positions misspelled words are corrected and do
        not affect segmentation existing spaces are allowed and considered for
        optimum segmentation.

        `word_segmentation` uses a novel approach *without* recursion.
        https://medium.com/@wolfgarbe/fast-word-segmentation-for-noisy-text-2c2c41f9e8da
        While each string of length n can be segmented in 2^n−1 possible
        compositions
        https://en.wikipedia.org/wiki/Composition_(combinatorics)
        `word_segmentation` has a linear runtime O(n) to find the optimum
        composition.

        Finds suggested spellings for a multi-word input string (supports word
        splitting/merging).

        Args:
            phrase: The string being spell checked.
            max_segmentation_word_length: The maximum word length that should be
                considered.
            max_edit_distance: The maximum edit distance between input and
                corrected words (0=no correction/segmentation only).
            ignore_token: A regex pattern describing what words/phrases to ignore
                and leave unchanged.

        Returns:
            The word segmented string, the word segmented and spelling corrected
            string, the edit distance sum between input string and corrected
            string, the sum of word occurence probabilities in log scale (a
            measure of how common and probable the corrected segmentation is).
        """
        # normalize ligatures: scientiﬁc -> scientific
        phrase = unicodedata.normalize("NFKC", phrase).replace("\u002D", "")

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
            # inner loop (row): all possible part lengths (from start position):
            # part can't be bigger than longest word in dictionary (other than
            # long unknown word)
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
                    part = part[1:]
                else:
                    # add ed+1: space did not exist, had to be inserted
                    separator_len = 1

                # remove space from part1, add number of removed spaces to top_ed
                top_ed += len(part)
                # remove space. add number of removed spaces to ed
                part = part.replace(" ", "")
                top_ed -= len(part)

                # v6.7: Lookup against the lowercase term
                results = self.lookup(
                    part.lower(),
                    Verbosity.TOP,
                    max_edit_distance,
                    ignore_token=ignore_token,
                )
                if results:
                    top_result = results[0].term
                    # v6.7: retain/preserve upper case
                    if len(part) > 0 and part[0].isupper():
                        top_result = top_result.capitalize()

                    top_ed += results[0].distance
                    # Naive Bayes Rule. We assume the word probabilities of two
                    # words to be independent. Therefore the resulting
                    # probability of the word combination is the product of the
                    # two word probabilities. Instead of computing the product
                    # of probabilities we are computing the sum of the logarithm
                    # of probabilities because the probabilities of words are
                    # about 10^-10, the product of many such small numbers could
                    # exceed (underflow) the floating number range and become
                    # zero. log(ab)=log(a)+log(b)
                    top_log_prob = math.log10(float(results[0].count) / float(self.N))
                else:
                    top_result = part
                    # default, if word not found. otherwise long input text
                    # would win as long unknown word (with ed=edmax+1), although
                    # there there should many spaces inserted
                    top_ed += len(part)
                    top_log_prob = math.log10(10.0 / self.N / 10.0 ** len(part))

                dest = (i + idx) % array_size
                # set values in first loop
                if j == 0:
                    compositions[dest] = Composition(
                        part, top_result, top_ed, top_log_prob
                    )
                # pylint: disable=C0301,R0916
                elif (
                    i == max_segmentation_word_length
                    # replace values if better log_prob_sum, if same edit
                    # distance OR one space difference
                    or (
                        compositions[dest].distance_sum
                        in (
                            compositions[idx].distance_sum + top_ed,
                            compositions[idx].distance_sum + separator_len + top_ed,
                        )
                        and compositions[dest].log_prob_sum
                        < compositions[idx].log_prob_sum + top_log_prob
                    )
                    # replace values if smaller edit distance
                    or compositions[idx].distance_sum + separator_len + top_ed
                    < compositions[dest].distance_sum
                ):
                    if (
                        len(top_result) == 1 and top_result[0] in string.punctuation
                    ) or (len(top_result) == 2 and top_result.startswith("'")):
                        compositions[dest] = Composition.create(
                            compositions[idx], part, top_result, top_ed, top_log_prob
                        )
                    else:
                        compositions[dest] = Composition.create(
                            compositions[idx],
                            f" {part}",
                            f" {top_result}",
                            separator_len + top_ed,
                            top_log_prob,
                        )
            idx = next(circular_index)
        return compositions[idx]

    def _delete_in_suggestion_prefix(
        self, delete: str, delete_len: int, suggestion: str, suggestion_len: int
    ) -> bool:  # pragma: no cover
        """Checks whether all delete chars are present in the suggestion prefix
        in correct order, otherwise this is just a hash collision.

        **NOTE**: No longer used in the Python port.
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

    def _edits(
        self,
        word: str,
        edit_distance: int,
        delete_words: Set[str],
        current_distance: int = 0,
    ) -> Set[str]:
        """Inexpensive and language independent: only deletes, no transposes +
        replaces + inserts replaces and inserts are expensive and language
        dependent.
        """
        edit_distance += 1
        if not word:
            return delete_words
        for i in range(current_distance, len(word)):
            delete = word[:i] + word[i + 1 :]
            if delete not in delete_words:
                delete_words.add(delete)
            # recursion, if maximum edit distance not yet reached
            if edit_distance < self._max_dictionary_edit_distance:
                self._edits(delete, edit_distance, delete_words, current_distance=i)
        return delete_words

    def _edits_prefix(self, key: str) -> Set[str]:
        hash_set = set()
        if len(key) <= self._max_dictionary_edit_distance:
            hash_set.add("")
        if len(key) > self._prefix_length:
            key = key[: self._prefix_length]
        hash_set.add(key)
        return self._edits(key, 0, hash_set)

    def _load_bigram_dictionary_stream(
        self,
        corpus_stream: IO[str],
        term_index: int,
        count_index: int,
        separator: Optional[str] = None,
    ):
        """Loads multiple dictionary entries from a stream of word/frequency
        count pairs.

        **NOTE**: Merges with any dictionary data already loaded.

        Args:
            corpus_stream: A file object of the dictionary.
            term_index: The column position of the word.
            count_index: The column position of the frequency count.
            separator: Separator characters between term(s) and count.

        Returns:
            ``True`` after file object is loaded.
        """
        min_parts = 3 if separator is None else 2
        for line in corpus_stream:
            parts = line.rstrip().split(separator)
            if len(parts) < min_parts:
                continue
            count = helpers.try_parse_int64(parts[count_index])
            if count is None:
                continue
            key = (
                f"{parts[term_index]} {parts[term_index + 1]}"
                if separator is None
                else parts[term_index]
            )
            self._bigrams[key] = count
            if count < self.bigram_count_min:
                self.bigram_count_min = count
        return True

    def _load_dictionary_stream(
        self,
        corpus_stream: IO[str],
        term_index: int,
        count_index: int,
        separator: str = " ",
    ) -> bool:
        """Loads multiple dictionary entries from a stream of word/frequency
        count pairs.

        **NOTE**: Merges with any dictionary data already loaded.

        Args:
            corpus_stream: A file object of the dictionary.
            term_index: The column position of the word.
            count_index: The column position of the frequency count.
            separator: Separator characters between term(s) and count.

        Returns:
            ``True`` after file object is loaded.
        """
        for line in corpus_stream:
            parts = line.rstrip().split(separator)
            if len(parts) < 2:
                continue
            count = helpers.try_parse_int64(parts[count_index])
            if count is None:
                continue
            key = parts[term_index]
            self.create_dictionary_entry(key, count)
        return True

    @staticmethod
    def _parse_words(text: str) -> List[str]:
        """Creates a non-unique wordlist from sample text language independent
        (e.g. works with Chinese characters).
        """
        # // \w Alphanumeric characters (including non-latin characters, umlaut
        # characters and digits) plus "_". [^\W_] is the equivalent of \w
        # excluding "_". Compatible with non-latin characters, does not split
        # words at apostrophes. Uses capturing groups to combine a negated set
        # with a character set.
        matches = WORD_PATTERN.findall(text.lower())
        # The above regex returns ("ghi'jkl", "l") for "ghi'jkl", so we extract
        # the first element
        matches = [match[0] for match in matches]
        return matches

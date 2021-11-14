import sys
from itertools import combinations, permutations

import numpy as np
import pytest
from symspellpy.editdistance import (
    AbstractDistanceComparer,
    DamerauOsa,
    EditDistance,
    Levenshtein,
)

SHORT_STRING = "string"
LONG_STRING = "long_string"
VERY_LONG_STRING = "very_long_string"


def expected_levenshtein(string_1, string_2, max_distance):
    max_distance = max_distance = int(min(2 ** 31 - 1, max_distance))
    len_1 = len(string_1)
    len_2 = len(string_2)
    d = np.zeros((len_1 + 1, len_2 + 1))
    for i in range(len_1 + 1):
        d[i, 0] = i
    for i in range(len_2 + 1):
        d[0, i] = i
    for j in range(1, len_2 + 1):
        for i in range(1, len_1 + 1):
            if string_1[i - 1] == string_2[j - 1]:
                # no operation
                d[i, j] = d[i - 1, j - 1]
            else:
                d[i, j] = min(
                    min(d[i - 1, j] + 1, d[i, j - 1] + 1), d[i - 1, j - 1] + 1
                )
    distance = d[len_1, len_2]
    return distance if distance <= max_distance else -1


def expected_damerau_osa(string_1, string_2, max_distance):
    max_distance = max_distance = int(min(2 ** 31 - 1, max_distance))
    len_1 = len(string_1)
    len_2 = len(string_2)
    d = np.zeros((len_1 + 1, len_2 + 1))
    for i in range(len_1 + 1):
        d[i, 0] = i
    for i in range(len_2 + 1):
        d[0, i] = i
    for i in range(1, len_1 + 1):
        for j in range(1, len_2 + 1):
            cost = 0 if string_1[i - 1] == string_2[j - 1] else 1
            d[i, j] = min(min(d[i - 1, j] + 1, d[i, j - 1] + 1), d[i - 1, j - 1] + cost)
            if (
                i > 1
                and j > 1
                and string_1[i - 1] == string_2[j - 2]
                and string_1[i - 2] == string_2[j - 1]
            ):
                d[i, j] = min(d[i, j], d[i - 2, j - 2] + cost)
    distance = d[len_1, len_2]
    return distance if distance <= max_distance else -1


@pytest.fixture(params=["damerau_osa", "levenshtein"])
def get_comparer(request):
    comparer_dict = {
        "damerau_osa": {"actual": DamerauOsa(), "expected": expected_damerau_osa},
        "levenshtein": {"actual": Levenshtein(), "expected": expected_levenshtein},
    }
    yield comparer_dict[request.param]["actual"], comparer_dict[request.param][
        "expected"
    ]


@pytest.fixture
def get_short_and_long_strings():
    return [
        (SHORT_STRING, None, {"null": len(SHORT_STRING), "zero": -1, "neg": -1}),
        (LONG_STRING, None, {"null": -1, "zero": -1, "neg": -1}),
        (None, SHORT_STRING, {"null": len(SHORT_STRING), "zero": -1, "neg": -1}),
        (None, LONG_STRING, {"null": -1, "zero": -1, "neg": -1}),
        (SHORT_STRING, SHORT_STRING, {"null": 0, "zero": 0, "neg": 0}),
        (None, None, {"null": 0, "zero": 0, "neg": 0}),
    ]


@pytest.fixture(params=[0, 1, 3, sys.maxsize])
def get_strings(request):
    alphabet = "abcd"
    strings = [""]
    for i in range(1, len(alphabet) + 1):
        for combi in combinations(alphabet, i):
            strings += ["".join(p) for p in permutations(combi)]
    yield strings, request.param


class TestEditDistance:
    def test_unknown_distance_algorithm(self):
        with pytest.raises(ValueError) as excinfo:
            _ = EditDistance(2)
        assert "Unknown distance algorithm" == str(excinfo.value)

    def test_abstract_distance_comparer(self):
        with pytest.raises(NotImplementedError) as excinfo:
            comparer = AbstractDistanceComparer()
            _ = comparer.distance("string_1", "string_2", 10)
        assert "Should have implemented this" == str(excinfo.value)

    def test_comparer_match_ref(self, get_comparer, get_strings):
        comparer, expected = get_comparer
        strings, max_distance = get_strings

        for s1 in strings:
            for s2 in strings:
                assert expected(s1, s2, max_distance) == comparer.distance(
                    s1, s2, max_distance
                )

    def test_comparer_null_distance(self, get_comparer, get_short_and_long_strings):
        comparer, _ = get_comparer

        for s1, s2, expected in get_short_and_long_strings:
            distance = comparer.distance(s1, s2, 10)
            assert expected["null"] == distance

    def test_comparer_negative_max_distance(
        self, get_comparer, get_short_and_long_strings
    ):
        comparer, _ = get_comparer

        for s1, s2, expected in get_short_and_long_strings:
            distance = comparer.distance(s1, s2, 0)
            assert expected["zero"] == distance

        for s1, s2, expected in get_short_and_long_strings:
            distance = comparer.distance(s1, s2, 0)
            assert expected["neg"] == distance

    def test_comparer_very_long_string(self, get_comparer):
        comparer, _ = get_comparer
        distance = comparer.distance(SHORT_STRING, VERY_LONG_STRING, 5)

        assert -1 == distance

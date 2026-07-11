import sys
from collections.abc import Callable, Generator
from itertools import combinations, permutations

import pytest

from symspellpy.abstract_distance_comparer import AbstractDistanceComparer
from symspellpy.editdistance import (
    DamerauOsa,
    DamerauOsaFast,
    DistanceAlgorithm,
    EditDistance,
    Levenshtein,
    LevenshteinFast,
)

try:
    import editdistpy

    EDITDISTPY_AVAILABLE = True
except ImportError:
    EDITDISTPY_AVAILABLE = False

SHORT_STRING = "string"
LONG_STRING = "long_string"
VERY_LONG_STRING = "very_long_string"


def expected_levenshtein(string_1: str, string_2: str, max_distance: int) -> int:
    max_distance = int(min(2**31 - 1, max_distance))
    len_1 = len(string_1)
    len_2 = len(string_2)
    d = [[0] * (len_2 + 1) for _ in range(len_1 + 1)]
    for i in range(len_1 + 1):
        d[i][0] = i
    for i in range(len_2 + 1):
        d[0][i] = i
    for j in range(1, len_2 + 1):
        for i in range(1, len_1 + 1):
            if string_1[i - 1] == string_2[j - 1]:
                # no operation
                d[i][j] = d[i - 1][j - 1]
            else:
                d[i][j] = min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + 1)
    distance = d[len_1][len_2]
    return distance if distance <= max_distance else -1


def expected_damerau_osa(string_1: str, string_2: str, max_distance: int) -> int:
    max_distance = int(min(2**31 - 1, max_distance))
    len_1 = len(string_1)
    len_2 = len(string_2)
    d = [[0] * (len_2 + 1) for _ in range(len_1 + 1)]
    for i in range(len_1 + 1):
        d[i][0] = i
    for i in range(len_2 + 1):
        d[0][i] = i
    for i in range(1, len_1 + 1):
        for j in range(1, len_2 + 1):
            cost = 0 if string_1[i - 1] == string_2[j - 1] else 1
            d[i][j] = min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + cost)
            if (
                i > 1
                and j > 1
                and string_1[i - 1] == string_2[j - 2]
                and string_1[i - 2] == string_2[j - 1]
            ):
                d[i][j] = min(d[i][j], d[i - 2][j - 2] + cost)
    distance = d[len_1][len_2]
    return distance if distance <= max_distance else -1


class CustomDistanceComparer(AbstractDistanceComparer):
    def distance(
        self, string_1: str | None, string_2: str | None, max_distance: int
    ) -> int:
        return -2


_COMPARER_PARAMS = ["damerau_osa", "levenshtein"]
if EDITDISTPY_AVAILABLE:
    _COMPARER_PARAMS += ["damerau_osa_fast", "levenshtein_fast"]


def _get_comparer_entry(
    name: str,
) -> tuple[AbstractDistanceComparer, Callable[[str, str, int], int]]:
    """Build a comparer and its reference function, by name."""
    match name:
        case "damerau_osa":
            return DamerauOsa(), expected_damerau_osa
        case "levenshtein":
            return Levenshtein(), expected_levenshtein
        case "damerau_osa_fast":
            return DamerauOsaFast(), expected_damerau_osa
        case "levenshtein_fast":
            return LevenshteinFast(), expected_levenshtein
        case _:
            raise ValueError(f"Unknown comparer: {name}")


@pytest.fixture(params=_COMPARER_PARAMS)
def get_comparer(
    request: pytest.FixtureRequest,
) -> Generator[tuple[AbstractDistanceComparer, Callable[[str, str, int], int]]]:
    yield _get_comparer_entry(request.param)


def _get_edit_distance_entry(
    name: str,
) -> tuple[EditDistance, type[AbstractDistanceComparer]]:
    """Build an EditDistance wrapper and its expected comparer type, by name."""
    match name:
        case "damerau_osa":
            return EditDistance(DistanceAlgorithm.DAMERAU_OSA), DamerauOsa
        case "levenshtein":
            return EditDistance(DistanceAlgorithm.LEVENSHTEIN), Levenshtein
        case "damerau_osa_fast":
            return EditDistance(DistanceAlgorithm.DAMERAU_OSA_FAST), DamerauOsaFast
        case "levenshtein_fast":
            return EditDistance(DistanceAlgorithm.LEVENSHTEIN_FAST), LevenshteinFast
        case _:
            raise ValueError(f"Unknown edit distance entry: {name}")


@pytest.fixture(params=_COMPARER_PARAMS)
def get_edit_distance(
    request: pytest.FixtureRequest,
) -> Generator[tuple[EditDistance, type[AbstractDistanceComparer]]]:
    yield _get_edit_distance_entry(request.param)


@pytest.fixture
def get_short_and_long_strings() -> list[tuple[str | None, str | None, dict[str, int]]]:
    return [
        (SHORT_STRING, None, {"null": len(SHORT_STRING), "zero": -1, "neg": -1}),
        (LONG_STRING, None, {"null": -1, "zero": -1, "neg": -1}),
        (None, SHORT_STRING, {"null": len(SHORT_STRING), "zero": -1, "neg": -1}),
        (None, LONG_STRING, {"null": -1, "zero": -1, "neg": -1}),
        (SHORT_STRING, SHORT_STRING, {"null": 0, "zero": 0, "neg": 0}),
        (None, None, {"null": 0, "zero": 0, "neg": 0}),
    ]


@pytest.fixture(params=[0, 1, 3, sys.maxsize])
def get_strings(request: pytest.FixtureRequest) -> Generator[tuple[list[str], int]]:
    alphabet = "abcd"
    strings = [""]
    for i in range(1, len(alphabet) + 1):
        for combi in combinations(alphabet, i):
            strings += ["".join(p) for p in permutations(combi)]
    yield strings, request.param


class TestEditDistance:
    def test_unknown_distance_algorithm(self):
        with pytest.raises(ValueError) as excinfo:
            _ = EditDistance(2)  # pyright:ignore[reportArgumentType]
        assert "unknown distance algorithm" == str(excinfo.value)

    def test_missing_custom_comparer(self):
        with pytest.raises(ValueError) as excinfo:
            _ = EditDistance(DistanceAlgorithm.USER_PROVIDED)
        assert "no comparer passed in" in str(excinfo.value)

    def test_abstract_distance_comparer(self):
        with pytest.raises(TypeError) as excinfo:
            comparer = AbstractDistanceComparer()  # pyright:ignore[reportAbstractUsage]
            _ = comparer.distance("string_1", "string_2", 10)
        assert str(excinfo.value).startswith(
            "Can't instantiate abstract class AbstractDistanceComparer"
        )

    def test_warn_when_builtin_comparer_override_custom_comparer(self):
        with pytest.warns(UserWarning, match="A built-in comparer will be used.$"):
            comparer = CustomDistanceComparer()
            EditDistance(DistanceAlgorithm.LEVENSHTEIN, comparer)

    def test_internal_distance_comparer(
        self, get_edit_distance: tuple[EditDistance, type[AbstractDistanceComparer]]
    ):
        edit_distance, expected = get_edit_distance
        assert isinstance(edit_distance._distance_comparer, expected)

    def test_comparer_match_ref(
        self,
        get_comparer: tuple[AbstractDistanceComparer, Callable[[str, str, int], int]],
        get_strings: tuple[list[str], int],
    ):
        comparer, expected = get_comparer
        strings, max_distance = get_strings

        for s1 in strings:
            for s2 in strings:
                assert expected(s1, s2, max_distance) == comparer.distance(
                    s1, s2, max_distance
                )

    def test_editdistance_use_custom_comparer(self, get_strings: tuple[list[str], int]):
        strings, max_distance = get_strings
        comparer = CustomDistanceComparer()
        EditDistance(DistanceAlgorithm.USER_PROVIDED, comparer)

        for s1 in strings:
            for s2 in strings:
                assert -2 == comparer.distance(s1, s2, max_distance)

    def test_comparer_null_distance(
        self,
        get_comparer: tuple[AbstractDistanceComparer, Callable[[str, str, int], int]],
        get_short_and_long_strings: list[tuple[str | None, str | None, dict[str, int]]],
    ):
        comparer, _ = get_comparer

        for s1, s2, expected in get_short_and_long_strings:
            distance = comparer.distance(s1, s2, 10)
            assert expected["null"] == distance

    def test_comparer_negative_max_distance(
        self,
        get_comparer: tuple[AbstractDistanceComparer, Callable[[str, str, int], int]],
        get_short_and_long_strings: list[tuple[str | None, str | None, dict[str, int]]],
    ):
        comparer, _ = get_comparer

        for s1, s2, expected in get_short_and_long_strings:
            distance = comparer.distance(s1, s2, 0)
            assert expected["zero"] == distance

        for s1, s2, expected in get_short_and_long_strings:
            distance = comparer.distance(s1, s2, 0)
            assert expected["neg"] == distance

    def test_comparer_very_long_string(
        self,
        get_comparer: tuple[AbstractDistanceComparer, Callable[[str, str, int], int]],
    ):
        comparer, _ = get_comparer
        distance = comparer.distance(SHORT_STRING, VERY_LONG_STRING, 5)

        assert -1 == distance

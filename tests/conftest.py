import importlib.resources
import json
from collections.abc import Generator
from pathlib import Path

import pytest

from symspellpy.symspellpy import SymSpell

FORTESTS_DIR = Path(__file__).resolve().parent / "fortests"


#######################################################################
# Paths
#######################################################################
@pytest.fixture
def bigram_path() -> Generator[Path, None, None]:
    ref = (
        importlib.resources.files("symspellpy")
        / "frequency_bigramdictionary_en_243_342.txt"
    )
    with importlib.resources.as_file(ref) as path:
        yield path


@pytest.fixture
def dictionary_path() -> Generator[Path, None, None]:
    ref = importlib.resources.files("symspellpy") / "frequency_dictionary_en_82_765.txt"
    with importlib.resources.as_file(ref) as path:
        yield path


@pytest.fixture
def pickle_path() -> Path:
    return FORTESTS_DIR / "dictionary.pickle"


@pytest.fixture
def query_path() -> Path:
    return FORTESTS_DIR / "noisy_query_en_1000.txt"


#######################################################################
# Misc
#######################################################################
@pytest.fixture
def get_same_word_and_count() -> list[tuple[str, int]]:
    word = "hello"
    return [(word, 11), (word, 3)]


@pytest.fixture
def get_fortests_data(request: pytest.FixtureRequest) -> list[dict[str, object]]:
    with open(FORTESTS_DIR / request.param) as infile:
        return json.load(infile)["data"]


#######################################################################
# symspells
#######################################################################
@pytest.fixture
def symspell_default() -> SymSpell:
    return SymSpell()


@pytest.fixture
def symspell_default_entry(
    symspell_default: SymSpell, request: pytest.FixtureRequest
) -> SymSpell:
    for entry in request.param:
        symspell_default.create_dictionary_entry(entry[0], entry[1])
    return symspell_default


@pytest.fixture
def symspell_default_load(
    symspell_default: SymSpell,
    dictionary_path: Path,
    bigram_path: Path,
    request: pytest.FixtureRequest,
) -> tuple[SymSpell, str]:
    symspell_default.load_dictionary(dictionary_path, 0, 1)
    if request.param == "bigram":
        symspell_default.load_bigram_dictionary(bigram_path, 0, 2)
    return symspell_default, request.param


@pytest.fixture
def symspell_long() -> SymSpell:
    return SymSpell(5)


@pytest.fixture
def symspell_long_entry(
    symspell_long: SymSpell, request: pytest.FixtureRequest
) -> tuple[SymSpell, list[str]]:
    for entry in request.param:
        symspell_long.create_dictionary_entry(entry, 2)
    return symspell_long, request.param


@pytest.fixture
def symspell_short(request: pytest.FixtureRequest) -> SymSpell:
    if request.param is None:
        return SymSpell(1, 3)
    return SymSpell(1, 3, count_threshold=request.param)

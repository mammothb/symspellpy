import json
from pathlib import Path

import pkg_resources
import pytest

from symspellpy import SymSpell

FORTESTS_DIR = Path(__file__).resolve().parent / "fortests"

#######################################################################
# Paths
#######################################################################
@pytest.fixture
def bigram_path():
    return pkg_resources.resource_filename(
        "symspellpy", "frequency_bigramdictionary_en_243_342.txt"
    )


@pytest.fixture
def dictionary_path():
    return pkg_resources.resource_filename(
        "symspellpy", "frequency_dictionary_en_82_765.txt"
    )


@pytest.fixture
def pickle_path():
    return FORTESTS_DIR / "dictionary.pickle"


@pytest.fixture
def query_path():
    return FORTESTS_DIR / "noisy_query_en_1000.txt"


#######################################################################
# Misc
#######################################################################
@pytest.fixture
def get_same_word_and_count():
    word = "hello"
    return [(word, 11), (word, 3)]


@pytest.fixture
def get_fortests_data(request):
    with open(FORTESTS_DIR / request.param) as infile:
        return json.load(infile)["data"]


#######################################################################
# symspells
#######################################################################
@pytest.fixture
def symspell_default():
    return SymSpell()


@pytest.fixture
def symspell_default_entry(symspell_default, request):
    for entry in request.param:
        symspell_default.create_dictionary_entry(entry[0], entry[1])
    return symspell_default


@pytest.fixture
def symspell_default_load(symspell_default, dictionary_path, bigram_path, request):
    symspell_default.load_dictionary(dictionary_path, 0, 1)
    if request.param == "bigram":
        symspell_default.load_bigram_dictionary(bigram_path, 0, 2)
    return symspell_default, request.param


@pytest.fixture
def symspell_long():
    return SymSpell(5)


@pytest.fixture
def symspell_long_entry(symspell_long, request):
    for entry in request.param:
        symspell_long.create_dictionary_entry(entry, 2)
    return symspell_long, request.param


@pytest.fixture
def symspell_short(request):
    if request.param is None:
        return SymSpell(1, 3)
    return SymSpell(1, 3, count_threshold=request.param)

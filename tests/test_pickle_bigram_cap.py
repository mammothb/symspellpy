import pickle
import sys
from io import StringIO
from pathlib import Path

import pytest

from symspellpy import SymSpell


def snapshot(sym_spell: SymSpell) -> list[tuple[str, int, int]]:
    return [
        (suggestion.term, suggestion.distance, suggestion.count)
        for suggestion in sym_spell.lookup_compound("helloworld", 2)
    ]


@pytest.mark.parametrize("mode", ["bytes", "compressed", "plain"])
@pytest.mark.parametrize("reuse", [False, True])
@pytest.mark.parametrize("overwritten", [False, True])
def test_reload_restores_bigram_cap(
    tmp_path: Path, mode: str, reuse: bool, overwritten: bool
):
    original = SymSpell()
    original.load_dictionary(StringIO("hello 10000000\nworld 10000000\n"), 0, 1)
    bigram_path = tmp_path / "bigrams.txt"
    bigram_path.write_text("hello hello 10\n")
    original.load_bigram_dictionary(bigram_path, 0, 2)
    if overwritten:
        bigram_path.write_text("hello hello 50\n")
        original.load_bigram_dictionary(bigram_path, 0, 2)
    expected = snapshot(original)
    assert expected == [("hello world", 1, 10)]

    restored = SymSpell()
    if reuse:
        old_path = tmp_path / "old.txt"
        old_path.write_text("old words 1\n")
        restored.load_bigram_dictionary(old_path, 0, 2)
    if mode == "bytes":
        data = original.save_pickle(to_bytes=True)
        assert data is not None
        restored.load_pickle(data, from_bytes=True)
    else:
        path = tmp_path / "dictionary.pickle"
        compressed = mode == "compressed"
        original.save_pickle(path, compressed=compressed)
        restored.load_pickle(path, compressed=compressed)

    assert snapshot(restored) == expected
    assert restored.bigram_count_min == original.bigram_count_min


@pytest.mark.parametrize("mode", ["bytes", "compressed", "plain"])
def test_reload_without_bigrams_resets_old_cap(tmp_path: Path, mode: str):
    original = SymSpell()
    original.create_dictionary_entry("hello", 10)
    restored = SymSpell()
    old_path = tmp_path / "old.txt"
    old_path.write_text("old words 1\n")
    restored.load_bigram_dictionary(old_path, 0, 2)
    if mode == "bytes":
        data = original.save_pickle(to_bytes=True)
        assert data is not None
        restored.load_pickle(data, from_bytes=True)
    else:
        path = tmp_path / "dictionary.pickle"
        compressed = mode == "compressed"
        original.save_pickle(path, compressed=compressed)
        restored.load_pickle(path, compressed=compressed)

    assert restored.bigrams == {}
    assert restored.bigram_count_min == sys.maxsize


@pytest.mark.parametrize("with_bigrams", [False, True])
def test_reload_legacy_pickle_without_bigram_cap(tmp_path: Path, with_bigrams: bool):
    original = SymSpell()
    original.create_dictionary_entry("hello", 10)
    if with_bigrams:
        path = tmp_path / "bigrams.txt"
        path.write_text("hello world 10\n")
        original.load_bigram_dictionary(path, 0, 2)
    data = original.save_pickle(to_bytes=True)
    assert data is not None
    legacy_data = pickle.loads(data)
    legacy_data.pop("bigram_count_min", None)
    restored = SymSpell()
    path = tmp_path / "old.txt"
    path.write_text("old words 1\n")
    restored.load_bigram_dictionary(path, 0, 2)

    assert restored.load_pickle(pickle.dumps(legacy_data), from_bytes=True)
    assert restored.bigram_count_min == original.bigram_count_min

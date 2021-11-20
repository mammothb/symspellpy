import pytest

from symspellpy.suggest_item import SuggestItem


@pytest.fixture
def suggest_item():
    return SuggestItem("term", 0, 0)


class TestSuggestItem:
    def test_invalid_equal_to(self, suggest_item):
        assert suggest_item.__eq__(0) is NotImplemented
        assert not suggest_item == 0

    def test_invalid_less_than(self, suggest_item):
        assert suggest_item.__lt__(0) is NotImplemented
        with pytest.raises(TypeError) as excinfo:
            suggest_item < 0
        assert "'<' not supported between instances of 'SuggestItem' and 'int'" == str(
            excinfo.value
        )

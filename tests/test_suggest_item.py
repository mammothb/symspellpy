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

    def test_suggest_item(self):
        si_1 = SuggestItem("asdf", 12, 34)
        si_2 = SuggestItem("sdfg", 12, 34)
        si_3 = SuggestItem("dfgh", 56, 78)

        assert si_1 == si_2
        assert si_2 != si_3

        assert "asdf" == si_1.term
        si_1.term = "qwer"
        assert "qwer" == si_1.term

        assert 34 == si_1.count
        si_1.count = 78
        assert 78 == si_1.count

        assert "qwer, 12, 78" == str(si_1)

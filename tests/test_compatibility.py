from symspellpy.helpers import null_distance_results, prefix_suffix_prep


def test_null_distance_results():
    assert null_distance_results(None, None, 1) == 0
    assert null_distance_results(None, string2=None, max_distance=1) == 0
    assert null_distance_results(string1=None, string2=None, max_distance=1) == 0
    assert null_distance_results(string_1=None, string_2=None, max_distance=1) == 0


def test_prefix_suffix_prep():
    assert prefix_suffix_prep("dabca", "ddca") == (2, 1, 1)
    assert prefix_suffix_prep("dabca", string2="ddca") == (2, 1, 1)
    assert prefix_suffix_prep(string1="dabca", string2="ddca") == (2, 1, 1)
    assert prefix_suffix_prep(string_1="dabca", string_2="ddca") == (2, 1, 1)

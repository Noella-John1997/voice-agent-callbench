from callbench.metrics import percentile, word_error_rate


def test_wer_identical_is_zero():
    assert word_error_rate("the name is priya", "the name is priya") == 0.0


def test_wer_one_substitution():
    # 1 wrong word out of 4
    assert word_error_rate("the name is priya", "the nine is priya") == 0.25


def test_wer_deletion_and_insertion():
    assert word_error_rate("a b c", "a c") == 1 / 3
    assert word_error_rate("a b", "a b c") == 0.5


def test_wer_chinese_is_per_character():
    assert word_error_rate("名字是陈伟", "名字是陈为") == 0.2


def test_percentile_nearest_rank():
    vals = list(range(1, 101))
    assert percentile(vals, 50) == 50
    assert percentile(vals, 95) == 95
    assert percentile([], 95) == 0.0

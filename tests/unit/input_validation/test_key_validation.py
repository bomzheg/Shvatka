import random

from shvatka.utils.input_validation import normalize_key, is_multiple_keys_normal, is_key_valid


def test_normal_single_key(valid_keys: list[str]):
    for line in valid_keys:
        assert normalize_key(line)
        assert is_key_valid(line)


def test_wrong_single_key(wrong_keys: list[str]):
    for line in wrong_keys:
        assert not normalize_key(line)
        assert not is_key_valid(line)


def test_normal_multiple_keys(valid_keys: list[str]):
    assert is_multiple_keys_normal(valid_keys)


def test_wrong_multiple_keys(wrong_keys: list[str]):
    assert not is_multiple_keys_normal(wrong_keys)


def test_one_wrong_key_in_multiple_normal(valid_keys: list[str], wrong_keys: list[str]):
    wrong_key = random.choice(wrong_keys)
    test_keys = [wrong_key, *valid_keys]
    assert not is_multiple_keys_normal(test_keys)
    test_keys = [*valid_keys, wrong_key]
    assert not is_multiple_keys_normal(test_keys)
    for _ in range(5):
        random.shuffle(test_keys)
        assert not is_multiple_keys_normal(test_keys)

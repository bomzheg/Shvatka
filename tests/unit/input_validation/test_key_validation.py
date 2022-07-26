import random

from app.utils.input_validation import is_key_normal, is_multiple_keys_normal


def test_normal_single_key(valid_keys: list[str]):
    for line in valid_keys:
        assert is_key_normal(line)


def test_wrong_single_key(wrong_keys: list[str]):
    for line in wrong_keys:
        assert not is_key_normal(line)


def test_normal_multiple_keys(valid_keys: list[str]):
    keys = "\n".join(valid_keys)
    assert is_multiple_keys_normal(keys)


def test_wrong_multiple_keys(wrong_keys: list[str]):
    keys = "\n".join(wrong_keys)
    assert not is_multiple_keys_normal(keys)


def test_one_wrong_key_in_multiple_normal(valid_keys: list[str], wrong_keys: list[str]):
    wrong_key = random.choice(wrong_keys)
    test_keys = [wrong_key, *valid_keys]
    assert not is_multiple_keys_normal("\n".join(test_keys))
    test_keys = [*valid_keys, wrong_key]
    assert not is_multiple_keys_normal("\n".join(test_keys))
    for _ in range(5):
        random.shuffle(test_keys)
        assert not is_multiple_keys_normal("\n".join(test_keys))

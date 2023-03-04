from shvatka.core.utils.input_validation import is_level_id_correct


def test_normal_id(valid_id: list[str]):
    for level_id in valid_id:
        assert is_level_id_correct(level_id.strip())


def test_wrong_id(wrong_id: list[str]):
    for level_id in wrong_id:
        assert not is_level_id_correct(level_id.strip())

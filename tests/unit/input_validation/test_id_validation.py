from shvatka.core.utils.input_validation import validate_level_id


def test_normal_id(valid_id: list[str]):
    for level_id in valid_id:
        assert validate_level_id(level_id.strip()) is not None


def test_wrong_id(wrong_id: list[str]):
    for level_id in wrong_id:
        assert validate_level_id(level_id.strip()) is None

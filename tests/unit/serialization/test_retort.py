from dataclasses import dataclass

import pytest
from adaptix import Retort
from shvatka.common.factory import FixedIterableProvider


@dataclass(frozen=True)
class B:
    b: str

@dataclass
class A:
    a: set[B]



@pytest.fixture
def retort():
    return Retort(
        recipe=[
            FixedIterableProvider(),
        ]
    )

def test_retort(retort: Retort):
    assert retort.dump(set(), set) == []
    assert retort.load([], set) == set()
    assert retort.dump({1, 2}, set) == [1, 2]
    assert retort.load([1, 2], set) == {1, 2}
    assert retort.dump(A({B("a")})) == {"a": [{"b": "a"}]}

from dataclasses import dataclass

import pytest
from adaptix import Retort, Mediator, Dumper
from adaptix._internal.morphing.iterable_provider import IterableProvider
from adaptix._internal.morphing.provider_template import ABCProxy
from adaptix._internal.morphing.request_cls import DumperRequest
from adaptix._internal.provider.location import GenericParamLoc
from adaptix._internal.provider.request_cls import DebugTrailRequest


@dataclass(frozen=True)
class B:
    b: str

@dataclass
class A:
    a: set[B]

class FixedIterableProvider(IterableProvider):
    def provide_dumper(self, mediator: Mediator, request: DumperRequest) -> Dumper:
        norm, arg = self._fetch_norm_and_arg(request)

        arg_dumper = mediator.mandatory_provide(
            request.append_loc(GenericParamLoc(type=arg, generic_pos=0)),
            lambda x: "Cannot create dumper for iterable. Dumper for element cannot be created",
        )
        debug_trail = mediator.mandatory_provide(DebugTrailRequest(loc_stack=request.loc_stack))
        return mediator.cached_call(
            self._make_dumper,
            origin=norm.origin,
            iter_factory=list,
            arg_dumper=arg_dumper,
            debug_trail=debug_trail,
        )

def test_retort():
    retort = Retort(
        recipe=[
            FixedIterableProvider(),
        ]
    )
    assert retort.dump(set(), set) == []
    assert retort.load([], set) == set()
    assert retort.dump({1, 2}, set) == [1, 2]
    assert retort.load([1, 2], set) == {1, 2}
    assert retort.dump(A({B("a")})) == {"a": [{"b": "a"}]}

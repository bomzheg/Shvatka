from collections import defaultdict
from dataclasses import dataclass
from uuid import uuid4

from dishka.dependency_source.factory import Factory
from dishka.entities.key import DependencyKey
from dishka.entities.scope import BaseScope
from dishka.registry import Registry


@dataclass
class Class:
    id: str
    name: str
    component: str
    scope: BaseScope
    dependencies: list[str]


def factory_to_class(factory: Factory, keys: dict[DependencyKey, str], container: type):
    hint = factory.provides.type_hint
    if hint == container:
        scope = ""
    else:
        scope = factory.scope  # type: ignore[assignment]
    name = getattr(hint, "__name__", str(hint))
    return Class(
        id=keys[factory.provides],
        name=name,
        scope=scope,  # type: ignore[arg-type]
        component=factory.provides.component,  # type: ignore[arg-type]
        dependencies=[keys[dep] for dep in factory.dependencies],
    )


def render_class(cls: Class):
    return f'        class {cls.id}["{cls.name} ({cls.scope})"]'


def render_relations(cls: Class):
    return "".join(f"    {dep} ..> {cls.id}\n" for dep in cls.dependencies)


def render_component(component: str, classes: list[Class]):
    component = component or "DEFAULT"
    return (
        f"    namespace {component} {{\n"
        + "\n".join(render_class(cls) for cls in classes)
        + "\n    }\n"
    )


def render(registries: list[Registry], container):
    res = "classDiagram\n"
    keys: dict[DependencyKey, str] = {}
    components: dict[str, list[Class]] = defaultdict(list)
    for registry in registries:
        for factory in registry.factories.values():
            keys[factory.provides] = str(uuid4()).replace("-", "_")
    for registry in registries:
        for factory in registry.factories.values():
            cls = factory_to_class(factory, keys, container)
            res += render_relations(cls)
            components[factory.provides.component].append(cls)  # type: ignore[index]
    for component, classes in components.items():
        res += render_component(component, classes)
    return res

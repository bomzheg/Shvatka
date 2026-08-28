"""Guard the transitions diagram against handler-driven jumps nobody declared.

`render_transitions` only sees Start/SwitchTo/Next/Back/Cancel widgets in a
window's keyboard plus its `preview_add_transitions`. What a handler does at
runtime (`manager.start(...)` / `manager.switch_to(...)`) is invisible, so every
such jump has to be declared with PreviewStart / PreviewSwitchTo.

This is a static check: it reads the dialog modules instead of importing them,
so a jump is spotted even when no test ever clicks that button.
"""

import ast
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DIALOGS_ROOT = REPO_ROOT / "shvatka/tgbot/dialogs"
HANDLER_KWARGS = frozenset({"on_click", "on_success", "on_error", "func"})
TRANSITION_WIDGETS = frozenset({"Start", "SwitchTo", "PreviewStart", "PreviewSwitchTo"})
JUMP_METHODS = frozenset({"start", "switch_to"})


def _state_name(node: ast.AST) -> str | None:
    """`states.SomeSG.window` -> `"SomeSG:window"`."""
    if (
        isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Attribute)
        and isinstance(node.value.value, ast.Name)
        and node.value.value.id == "states"
    ):
        return f"{node.value.attr}:{node.attr}"
    return None


def _states_in(node: ast.AST) -> set[str]:
    return {name for child in ast.walk(node) if (name := _state_name(child))}


@dataclass
class Func:
    jumps: set[str] = field(default_factory=set)
    calls: set[str] = field(default_factory=set)


def _parse_function(node: ast.FunctionDef | ast.AsyncFunctionDef) -> Func:
    func = Func()
    for call in ast.walk(node):
        if not isinstance(call, ast.Call):
            continue
        if isinstance(call.func, ast.Attribute):
            if call.func.attr in JUMP_METHODS:
                func.jumps |= _states_in(call)
        elif isinstance(call.func, ast.Name):
            func.calls.add(call.func.id)
    return func


def _parse_functions(path: Path) -> dict[str, Func]:
    """Every function of a module, with the states it jumps to."""
    functions = {
        node.name: _parse_function(node)
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
    }
    # handlers often jump through a local helper, so follow calls inside the module
    for _ in range(len(functions)):
        for func in functions.values():
            for callee in func.calls:
                if callee in functions:
                    func.jumps |= functions[callee].jumps
    return functions


_MODULES: dict[str, dict[str, Func]] = {}


def _module(dotted: str) -> dict[str, Func]:
    if dotted not in _MODULES:
        path = REPO_ROOT / (dotted.replace(".", "/") + ".py")
        _MODULES[dotted] = _parse_functions(path) if path.exists() else {}
    return _MODULES[dotted]


def _imported_from(path: Path) -> dict[str, str]:
    """Local name -> module it was imported from."""
    package = ".".join(path.parent.relative_to(REPO_ROOT).parts)
    imports: dict[str, str] = {}
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if not isinstance(node, ast.ImportFrom):
            continue
        if node.level:
            module = f"{package}.{node.module}" if node.module else package
        else:
            module = node.module or ""
        for alias in node.names:
            imports[alias.asname or alias.name] = module
    return imports


def _undeclared_jumps(path: Path) -> list[str]:
    imports = _imported_from(path)
    problems: list[str] = []
    for window in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if not (isinstance(window, ast.Call) and getattr(window.func, "id", None) == "Window"):
            continue
        state = next((_state_name(kw.value) for kw in window.keywords if kw.arg == "state"), None)
        declared: set[str] = set()
        handlers: set[str] = set()
        for node in ast.walk(window):
            if isinstance(node, ast.Call) and getattr(node.func, "id", None) in TRANSITION_WIDGETS:
                declared |= _states_in(node)
            if (
                isinstance(node, ast.keyword)
                and node.arg in HANDLER_KWARGS
                and isinstance(node.value, ast.Name)
            ):
                handlers.add(node.value.id)
        declared.add(state)

        for handler in sorted(handlers):
            func = _module(imports.get(handler, "")).get(handler)
            if func is None:
                continue
            problems.extend(
                f"{state}: {handler} jumps to {target}, add it to preview_add_transitions"
                for target in sorted(func.jumps - declared)
            )
    return problems


def test_handler_jumps_are_declared() -> None:
    paths = sorted(DIALOGS_ROOT.glob("*/dialogs.py"))
    assert paths, "no dialog modules found"

    problems = [problem for path in paths for problem in _undeclared_jumps(path)]

    assert problems == []

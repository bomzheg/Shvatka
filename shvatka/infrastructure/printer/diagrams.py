from io import BytesIO
from pathlib import Path
from tempfile import mktemp

from shvatka.core.scenario import dto
from shvatka.core.scenario.adapters import TransitionsPrinter

DEFAULT_NODE_NAME = "__default__"


class DiagramPrinter(TransitionsPrinter):
    def print(self, transitions: dto.Transitions) -> BytesIO:
        builder = DiagramBuilder(transitions)
        return builder.build()


class DiagramBuilder:
    def __init__(self, transitions: dto.Transitions) -> None:
        self.transitions = transitions
        self.file = mktemp(suffix="_diagram", prefix="shvatka_")

    def build(self) -> BytesIO:
        self._build_diagram()
        result = BytesIO()
        file = Path(self.file + ".puml")
        with file.open("rb") as f:
            result.write(f.read())
        file.unlink(missing_ok=True)
        result.seek(0)
        return result

    def _build_diagram(self) -> None:
        conditions_registry: dict[tuple[str, str], int] = {}
        i = 0
        for level, conditions in self.transitions.levels_conditions.items():
            for condition, is_routed in conditions:
                conditions_registry[(level, condition)] = i
                i += 1
        result = "@startuml\n\nleft to right direction\n\n"
        for number, name_id in self.transitions.levels:
            result += f"package \"{self.level_label(number, name_id)}\" as {name_id} {{\n"
            for condition, is_routed in self.transitions.levels_conditions[name_id]:
                result += f" object \"{condition}\" as cond_{conditions_registry[(name_id, condition)]}\n"
            prev: str | None = None
            for condition, is_routed in self.transitions.levels_conditions[name_id]:
                if prev is not None:
                    result += f" cond_{conditions_registry[(name_id, prev)]} -[hidden]down-> cond_{conditions_registry[(name_id, condition)]}\n"
                prev = condition
            result += "\n}\n"
        result += f"package \"Finish\" as {TransitionsPrinter.FINISH_NAME} {{\n object Finish\n}}\n"
        for tr in self.transitions.forward_transitions:
            result += f"{tr.from_}.cond_{conditions_registry[(tr.from_, tr.condition)]} --> {tr.to}\n"
        for tr in self.transitions.routed_transitions:
            result += f"{tr.from_}.cond_{conditions_registry[(tr.from_, tr.condition)]} ..> {tr.to}\n"
        result += "\n\n@enduml"
        with open(self.file + ".puml", "w") as f:
            f.write(result)


    def level_label(self, number: int, name_id: str) -> str:
        return f"№{number+1} ({name_id})"

import string
from io import BytesIO
import zlib
import base64

import aiohttp.client

from shvatka.core.scenario import dto
from shvatka.core.scenario.adapters import TransitionsPrinter

PLANTUML_URL = "https://www.plantuml.com/plantuml/svg/{encoded}"

DEFAULT_NODE_NAME = "__default__"

maketrans = bytes.maketrans

plantuml_alphabet = string.digits + string.ascii_uppercase + string.ascii_lowercase + "-_"
base64_alphabet = string.ascii_uppercase + string.ascii_lowercase + string.digits + "+/"
b64_to_plantuml = maketrans(base64_alphabet.encode("utf-8"), plantuml_alphabet.encode("utf-8"))
plantuml_to_b64 = maketrans(plantuml_alphabet.encode("utf-8"), base64_alphabet.encode("utf-8"))


def plantuml_encode(plantuml_text: str) -> str:
    """zlib compress the plantuml text and encode it for the plantuml server"""
    zlibbed_str = zlib.compress(plantuml_text.encode("utf-8"))
    compressed_string = zlibbed_str[2:-4]
    return base64.b64encode(compressed_string).translate(b64_to_plantuml).decode("utf-8")


class DiagramPrinter(TransitionsPrinter):
    def __init__(self, session: aiohttp.client.ClientSession) -> None:
        self.session = session

    def print(self, transitions: dto.Transitions) -> str:
        builder = DiagramBuilder(transitions)
        return builder.build()

    async def render(self, diagram: str) -> BytesIO:
        async with self.session.get(PLANTUML_URL.format(encoded=plantuml_encode(diagram))) as resp:
            resp.raise_for_status()
            return BytesIO(await resp.read())


class DiagramBuilder:
    def __init__(self, transitions: dto.Transitions) -> None:
        self.transitions = transitions

    def build(self) -> str:
        return self._build_diagram()

    def _build_diagram(self) -> str:
        conditions_registry: dict[tuple[str, str], int] = {}
        i = 0
        for level, conditions in self.transitions.levels_conditions.items():
            for condition, _ in conditions:
                conditions_registry[(level, condition)] = i
                i += 1
        result = "@startuml\n\nleft to right direction\n\n"
        for number, name_id in self.transitions.levels:
            result += f'package "{self.level_label(number, name_id)}" as {name_id} {{\n'
            for condition, _ in self.transitions.levels_conditions[name_id]:
                result += (
                    f' object "{condition}" as cond_{conditions_registry[(name_id, condition)]}\n'
                )
            prev: str | None = None
            for condition, _ in self.transitions.levels_conditions[name_id]:
                if prev is not None:
                    result += (
                        f" cond_{conditions_registry[(name_id, prev)]} "
                        f"-[hidden]down-> "
                        f"cond_{conditions_registry[(name_id, condition)]}\n"
                    )
                prev = condition
            result += "\n}\n"
        result += f'package "Finish" as {TransitionsPrinter.FINISH_NAME} {{\n object Finish\n}}\n'
        for tr in self.transitions.forward_transitions:
            result += (
                f"{tr.from_}.cond_{conditions_registry[(tr.from_, tr.condition)]} --> {tr.to}\n"
            )
        for tr in self.transitions.routed_transitions:
            result += (
                f"{tr.from_}.cond_{conditions_registry[(tr.from_, tr.condition)]} ..> {tr.to}\n"
            )
        result += "\n\n@enduml"
        return result

    def level_label(self, number: int, name_id: str) -> str:
        return f"№{number+1} ({name_id})"

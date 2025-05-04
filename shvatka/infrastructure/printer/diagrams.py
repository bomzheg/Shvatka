from io import BytesIO
from pathlib import Path
from tempfile import mktemp

from diagrams import Diagram, Cluster, Node, Edge
from diagrams.aws.business import Chime
from diagrams.aws.compute import EC2ElasticIpAddress
from diagrams.aws.management import OpsworksDeployments

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
        file = Path(self.file + ".png")
        with file.open("rb") as f:
            result.write(f.read())
        file.unlink(missing_ok=True)
        result.seek(0)
        return result

    def _build_diagram(self) -> None:
        with Diagram(
            name=self.transitions.game_name,
            show=False,
            filename=self.file,
            outformat="png",
            direction="tb"
        ):
            nodes: dict[str, dict[str, Node]] = {}
            for number, name_id in self.transitions.levels:
                with Cluster(label=f"№{number} ({name_id})"):
                    for condition, is_routed in self.transitions.levels_conditions[name_id]:
                        if is_routed:
                            node = OpsworksDeployments(label=condition)
                        else:
                            node = EC2ElasticIpAddress(label=condition)
                            nodes.setdefault(name_id, {})[DEFAULT_NODE_NAME] = node
                        nodes.setdefault(name_id, {})[condition] = node
            for tr in self.transitions.forward_transitions:
                if tr.to == TransitionsPrinter.FINISH_NAME:
                    nodes.setdefault(tr.to, {})[DEFAULT_NODE_NAME] = Chime(label="Finish")
                nodes[tr.from_][tr.condition] >> Edge() >> nodes[tr.to][DEFAULT_NODE_NAME]
            for tr in self.transitions.routed_transitions:
                nodes[tr.from_][tr.condition] >> Edge() >> nodes[tr.to][DEFAULT_NODE_NAME]

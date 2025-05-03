from io import BytesIO
from tempfile import NamedTemporaryFile

from diagrams import Diagram, Cluster, Node, Edge
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
        self.file = NamedTemporaryFile("wb", suffix=".png")
        self.file.close()

    def build(self) -> BytesIO:
        self._build_diagram()
        result = BytesIO()
        with open(self.file.name, "rb") as f:
            result.write(self.file.read())
        result.seek(0)
        return result

    def _build_diagram(self) -> None:
        with Diagram(name=self.transitions.game_name, show=False, filename=self.file.name):
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
            for transition in self.transitions.forward_transitions:
                (
                    nodes[transition.from_][transition.condition]
                    >> Edge()
                    >> nodes[transition.to][DEFAULT_NODE_NAME]
                )
            for transition in self.transitions.routed_transitions:
                (
                    nodes[transition.from_][transition.condition]
                    >> Edge()
                    >> nodes[transition.to][DEFAULT_NODE_NAME]
                )


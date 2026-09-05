from dataclasses import dataclass


@dataclass
class MonitoringConfig:
    probe_interval: float = 0.1
    stall_threshold: float = 0.25
    stall_traceback: bool = True
    stall_report_interval: float = 10.0
    blocking_threads: int | None = None

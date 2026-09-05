from dataclasses import dataclass


@dataclass
class MonitoringConfig:
    # on means a probe task, and with stall_traceback a watchdog thread too
    enabled: bool = False
    probe_interval: float = 0.1
    stall_threshold: float = 0.25
    stall_traceback: bool = True
    stall_report_interval: float = 10.0

from dataclasses import dataclass


@dataclass
class MonitoringConfig:
    """The ``monitoring`` section of config.yml — how closely the process
    watches its own event loop, and how much of it it is allowed to hand to
    threads.

    Every field has a default that is safe on a live game, so the section may
    be left out entirely.
    """

    probe_interval: float = 0.1
    """how often the loop is asked for a turn, in seconds. also the resolution
    of the watchdog: it cannot see a stall shorter than this."""

    stall_threshold: float = 0.25
    """a loop that hasn't had a turn for this long, in seconds, is stalled"""

    stall_traceback: bool = True
    """dump the stack the loop is stuck in when it stalls. costs one thread"""

    stall_report_interval: float = 10.0
    """at most one traceback per this many seconds. the counter still sees
    every stall, so the rate stays honest while the log stays readable"""

    blocking_threads: int | None = None
    """size of the thread pool blocking work is handed to. ``None`` keeps
    python's own default of ``min(32, cpu_count + 4)``"""

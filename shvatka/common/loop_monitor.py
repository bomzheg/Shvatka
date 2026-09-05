import asyncio
import logging
import sys
import threading
import time
import traceback
from contextlib import suppress
from types import FrameType

from prometheus_client import Counter, Histogram

from shvatka.common.config.models.monitoring import MonitoringConfig

logger = logging.getLogger(__name__)

LOOP_LAG = Histogram(
    "asyncio_loop_lag_seconds",
    "how much later than asked a periodic sleep on the event loop actually woke up",
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)
LOOP_STALLS = Counter(
    "asyncio_loop_stalls_total",
    "times the event loop went without a turn for longer than the stall threshold",
)


class LoopMonitor:
    def __init__(self, config: MonitoringConfig) -> None:
        self.config = config
        self._heartbeat = time.monotonic()
        self._loop_thread_id: int | None = None
        self._probe: asyncio.Task[None] | None = None
        self._watchdog: threading.Thread | None = None
        self._stopping = threading.Event()

    async def start(self) -> None:
        self._heartbeat = time.monotonic()
        self._loop_thread_id = threading.get_ident()
        self._stopping.clear()
        self._probe = asyncio.create_task(  # noqa: TID251  # supervised right here, by stop()
            self._measure(), name="loop-lag-probe"
        )
        if self.config.stall_traceback:
            self._watchdog = threading.Thread(
                target=self._watch, name="loop-watchdog", daemon=True
            )
            self._watchdog.start()
        logger.info(
            "loop monitor started on %s: probing every %.3f s, %s",
            # uvicorn picks uvloop purely on whether it can import it, so this
            # is the one line that says which loop a deployment actually got
            type(asyncio.get_running_loop()).__module__,
            self.config.probe_interval,
            f"reporting stalls over {self.config.stall_threshold:.3f} s"
            if self.config.stall_traceback
            else "stall tracebacks disabled",
        )

    async def stop(self) -> None:
        self._stopping.set()
        if self._probe is not None:
            self._probe.cancel()
            with suppress(asyncio.CancelledError):
                await self._probe
            self._probe = None
        if self._watchdog is not None:
            # the thread waits on the event, so it is already on its way out
            self._watchdog.join(timeout=self.config.probe_interval * 10)
            self._watchdog = None

    async def _measure(self) -> None:
        interval = self.config.probe_interval
        while True:
            started = time.monotonic()
            await asyncio.sleep(interval)
            woke_at = time.monotonic()
            LOOP_LAG.observe(max(0.0, woke_at - started - interval))
            self._heartbeat = woke_at

    def _watch(self) -> None:
        reported_this_stall = False
        last_report = 0.0
        while not self._stopping.wait(self.config.probe_interval):
            stalled_for = time.monotonic() - self._heartbeat
            if stalled_for < self.config.stall_threshold:
                reported_this_stall = False
                continue
            if reported_this_stall:
                continue
            reported_this_stall = True
            LOOP_STALLS.inc()
            now = time.monotonic()
            # a bad game stalls constantly; one traceback per interval is enough
            # to name the offender, and the counter keeps the true rate
            if now - last_report < self.config.stall_report_interval:
                continue
            last_report = now
            self._report(stalled_for)

    def _report(self, stalled_for: float) -> None:
        frame = self._loop_frame()
        if frame is None:
            logger.warning("event loop blocked for %.3f s, its frame is gone", stalled_for)
            return
        logger.warning(
            "event loop blocked for %.3f s in:\n%s",
            stalled_for,
            "".join(traceback.format_stack(frame)),
        )

    def _loop_frame(self) -> FrameType | None:
        if self._loop_thread_id is None:
            return None
        return sys._current_frames().get(self._loop_thread_id)  # noqa: SLF001

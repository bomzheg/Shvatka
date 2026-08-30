"""Capturing log records without ``caplog``.

``caplog`` collects through a handler it puts on the **root** logger, and the
app configures logging with ``logging.config.dictConfig``
(``shvatka/common/config/parser/logging_config.py``), which replaces the root
logger's handlers wholesale — caplog's included. Whether that happens before a
test or during it depends on when the session-scoped ``paths`` fixture is first
asked for, so a caplog assertion here passes or fails by test order.

Listening on the logger under test instead is immune to all of it: its own
handlers are untouched by a root reconfiguration.
"""

import logging
from collections.abc import Iterator
from contextlib import contextmanager


class RecordingHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)

    @property
    def text(self) -> str:
        return "\n".join(record.getMessage() for record in self.records)


@contextmanager
def capture_logs(name: str, level: int = logging.DEBUG) -> Iterator[RecordingHandler]:
    """Collect what ``name`` logs at ``level`` or above, for the block's duration."""
    logger = logging.getLogger(name)
    handler = RecordingHandler()
    handler.setLevel(level)
    previous = logger.level
    logger.setLevel(level)
    logger.addHandler(handler)
    try:
        yield handler
    finally:
        logger.removeHandler(handler)
        logger.setLevel(previous)

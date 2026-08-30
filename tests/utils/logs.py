"""Capturing log records without ``caplog``.

Two things in this repository make ``caplog`` unreliable, and both are global
state a test cannot see:

* the alembic migrations call ``logging.config.fileConfig``
  (``shvatka/infrastructure/db/migrations/env.py``), which used to leave every
  already-created logger with ``disabled = True`` — a disabled logger drops its
  records whatever level or handlers it has;
* ``setup_logging`` calls ``logging.config.dictConfig``, which replaces the
  **root** logger's handlers wholesale, and a root handler is exactly how
  ``caplog`` collects.

Which of them has happened by the time a test runs depends on test order, so an
assertion on ``caplog.text`` here passes or fails by where it sits in the suite.
Listening on the logger under test, and making sure it is enabled, depends on
neither.
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
    was_disabled, previous_level = logger.disabled, logger.level
    logger.disabled = False
    logger.setLevel(level)
    logger.addHandler(handler)
    try:
        yield handler
    finally:
        logger.removeHandler(handler)
        logger.setLevel(previous_level)
        logger.disabled = was_disabled

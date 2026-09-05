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

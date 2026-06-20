import logging

from . import log_context


class RequestContextFilter(logging.Filter):
    """Inject request_id and correlation_id from context vars into every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = log_context.request_id.get()
        record.correlation_id = log_context.correlation_id.get()
        return True

from __future__ import annotations

from contextvars import ContextVar, Token
import logging


_request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)


def set_request_id(request_id: str) -> Token:
    return _request_id_var.set(request_id)


def get_request_id() -> str | None:
    return _request_id_var.get()


def reset_request_id(token: Token) -> None:
    _request_id_var.reset(token)


def outbound_request_headers() -> dict[str, str]:
    request_id = get_request_id()
    if not request_id:
        return {}
    return {"X-Request-ID": request_id}


class RequestIDLogFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        request_id = get_request_id() or "-"
        record.request_id = request_id
        message = record.getMessage()
        if message and "[request_id=" not in message:
            record.msg = f"[request_id={request_id}] {record.msg}"
        return True


def install_request_id_logging() -> None:
    root = logging.getLogger()
    if any(isinstance(existing, RequestIDLogFilter) for existing in root.filters):
        return
    filter_obj = RequestIDLogFilter()
    root.addFilter(filter_obj)
    for handler in root.handlers:
        handler.addFilter(filter_obj)


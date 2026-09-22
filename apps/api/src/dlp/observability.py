"""Low-cardinality request telemetry. Never export bodies, prompts, headers, full URLs or user identifiers."""
from __future__ import annotations

from contextlib import contextmanager

from dlp.config import Settings

_tracer = None
_duration = None


def configure_telemetry(settings: Settings) -> None:
    global _tracer, _duration
    if not settings.applicationinsights_connection_string or _tracer is not None:
        return
    from azure.monitor.opentelemetry import configure_azure_monitor
    from opentelemetry import metrics, trace
    from opentelemetry.sdk.resources import Resource

    # Framework auto-instrumentation can capture exception details and URL identifiers.
    # We instrument the middleware ourselves using only the route template, method and response code.
    libraries = ("azure_sdk", "django", "fastapi", "flask", "httpx", "psycopg2", "requests", "urllib", "urllib3")
    configure_azure_monitor(
        connection_string=settings.applicationinsights_connection_string,
        logger_name="dlp.telemetry", enable_live_metrics=False, disable_offline_storage=True,
        sampling_ratio=0.1, resource=Resource.create({"service.name": "dlp-api", "service.version": "0.2"}),
        instrumentation_options={library: {"enabled": False} for library in libraries},
    )
    _tracer = trace.get_tracer("dlp.http")
    _duration = metrics.get_meter("dlp.http").create_histogram("http.server.request.duration", unit="s")


@contextmanager
def request_span():
    if _tracer is None:
        yield None
        return
    from opentelemetry.trace import SpanKind
    with _tracer.start_as_current_span("http.request", kind=SpanKind.SERVER,
                                       record_exception=False, set_status_on_exception=False) as span:
        yield span


def finish_request(span, *, method: str, route: str, status: int, duration: float) -> None:
    attributes = {"http.method": method, "http.route": route, "http.status_code": status}
    if span is not None:
        span.update_name(f"{method} {route}")
        span.set_attributes(attributes)
    if _duration is not None:
        _duration.record(duration, attributes)

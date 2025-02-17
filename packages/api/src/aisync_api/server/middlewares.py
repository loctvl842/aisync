from starlette.types import ASGIApp, Message, Receive, Scope, Send

from prometheus_client import Counter, Gauge, Histogram

import time
from contextlib import contextmanager


@contextmanager
def track_duration(histogram: Histogram, labels: dict):
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        histogram.labels(**labels).observe(duration)


class MetricMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app
        self.request_count = Counter(
            "http_requests_total",
            "Total HTTP requests",
            ["method", "path", "status"],
        )

        self.request_duration = Histogram(
            "http_request_duration_seconds",
            "HTTP request duration in seconds",
            ["method", "path"],
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0],
        )
        self.requests_in_progress = Gauge(
            "http_requests_in_progress",
            "Number of HTTP requests currently in progress",
            ["method", "path"],
        )

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "")
        path = scope.get("path", "")
        start_time = time.time()
        status_code = 0

        self.requests_in_progress.labels(method=method, path=path).inc()

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as exc:
            status_code = 500
            raise exc
        finally:
            duration = time.time() - start_time

            if method and path:
                self.request_duration.labels(
                    method=method,
                    path=path,
                ).observe(duration)

                self.request_count.labels(
                    method=method,
                    path=path,
                    status=status_code,
                ).inc()

                self.requests_in_progress.labels(
                    method=method,
                    path=path,
                ).dec()

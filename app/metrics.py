from prometheus_client import Counter, Histogram

REQUESTS = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)

REQUEST_SECONDS = Histogram(
    "http_request_duration_seconds",
    "Request duration in seconds",
    ["method", "path"],
)
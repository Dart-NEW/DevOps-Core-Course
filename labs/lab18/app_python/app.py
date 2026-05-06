"""DevOps Info Service main application module."""

import json
import logging
import os
import platform
import socket
import threading
import time
from datetime import datetime, timezone

from flask import Flask, Response, request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

app = Flask(__name__)

HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
VISITS_FILE = os.getenv('VISITS_FILE', os.path.join('data', 'visits'))


class JSONFormatter(logging.Formatter):
    """Render single-line JSON logs for Loki ingestion."""

    def format(self, record):
        payload = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage()
        }

        for field in ('event', 'method', 'path', 'status_code', 'client_ip'):
            if hasattr(record, field):
                payload[field] = getattr(record, field)

        if record.exc_info:
            payload['exception'] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)


def configure_logging():
    """Configure root logging to emit JSON to stdout."""
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(logging.INFO if not DEBUG else logging.DEBUG)
    root_logger.addHandler(handler)


configure_logging()
logger = logging.getLogger(__name__)
START_TIME = datetime.now(timezone.utc)

# RED metrics for request-driven service monitoring.
HTTP_REQUESTS_TOTAL = Counter(
    'http_requests_total',
    'Total HTTP requests processed',
    ['method', 'endpoint', 'status_code']
)
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint', 'status_code']
)
HTTP_REQUESTS_IN_PROGRESS = Gauge(
    'http_requests_in_progress',
    'HTTP requests currently in progress',
    ['method', 'endpoint']
)
ENDPOINT_CALLS_TOTAL = Counter(
    'devops_info_endpoint_calls_total',
    'Total calls per endpoint',
    ['endpoint']
)
SYSTEM_INFO_COLLECTION_SECONDS = Histogram(
    'devops_info_system_collection_seconds',
    'Time spent collecting system information'
)


class VisitCounter:
    """Persist and increment visit counts in a thread-safe way."""

    def __init__(self, path):
        self.path = path
        self._lock = threading.Lock()
        self._count = self._read_from_disk()

    def _ensure_parent_dir(self):
        directory = os.path.dirname(self.path)
        if directory:
            os.makedirs(directory, exist_ok=True)

    def _read_from_disk(self):
        try:
            with open(self.path, 'r', encoding='utf-8') as file:
                raw_value = file.read().strip()
        except FileNotFoundError:
            return 0

        if not raw_value:
            return 0

        try:
            return int(raw_value)
        except ValueError:
            logger.warning(
                'Invalid visits counter value, resetting to zero',
                extra={'event': 'invalid_visits_counter', 'path': self.path}
            )
            return 0

    def _write_to_disk(self, count):
        self._ensure_parent_dir()
        temp_path = f'{self.path}.tmp'
        with open(temp_path, 'w', encoding='utf-8') as file:
            file.write(str(count))
        os.replace(temp_path, self.path)

    def get_count(self):
        """Return the current persisted visit count."""
        with self._lock:
            self._count = self._read_from_disk()
            return self._count

    def increment(self):
        """Increment the visit count and persist it atomically."""
        with self._lock:
            current = self._read_from_disk()
            updated = current + 1
            self._write_to_disk(updated)
            self._count = updated
            return updated


visit_counter = VisitCounter(VISITS_FILE)


def log_event(level, message, **fields):
    """Emit structured application events with stable keys."""
    logger.log(level, message, extra=fields)


def json_response(data, status=200):
    """Create a JSON response with preserved key order."""
    return Response(
        json.dumps(data, ensure_ascii=False, indent=2),
        mimetype='application/json'
    ), status


def get_system_info():
    """Collect system information for the root endpoint."""
    try:
        hostname = socket.gethostname()
        platform_name = platform.system()

        if platform_name == 'Linux':
            try:
                import distro
                platform_version = f'{distro.name()} {distro.version()}'
            except ImportError:
                platform_version = platform.release()
        else:
            platform_version = platform.release()

        return {
            'hostname': hostname,
            'platform': platform_name,
            'platform_version': platform_version,
            'architecture': platform.machine(),
            'cpu_count': os.cpu_count(),
            'python_version': platform.python_version()
        }
    except Exception as error:
        logger.error('Error getting system info', exc_info=error)
        return {}


def get_uptime():
    """Calculate application uptime."""
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60

    return {
        'seconds': seconds,
        'human': (
            f"{hours} hour{'s' if hours != 1 else ''}, "
            f"{minutes} minute{'s' if minutes != 1 else ''}"
        )
    }


def get_runtime_info():
    """Get runtime information including uptime and current time."""
    uptime = get_uptime()
    return {
        'uptime_seconds': uptime['seconds'],
        'uptime_human': uptime['human'],
        'current_time': datetime.now(timezone.utc).isoformat(),
        'timezone': 'UTC'
    }


def get_request_info(req):
    """Extract request information for the response body."""
    return {
        'client_ip': req.remote_addr or 'unknown',
        'user_agent': req.headers.get('User-Agent', 'unknown'),
        'method': req.method,
        'path': req.path
    }


def get_endpoints():
    """Get list of available endpoints."""
    return [
        {
            'path': '/',
            'method': 'GET',
            'description': 'Service information'
        },
        {
            'path': '/health',
            'method': 'GET',
            'description': 'Health check'
        },
        {
            'path': '/visits',
            'method': 'GET',
            'description': 'Current persisted visit counter'
        },
        {
            'path': '/metrics',
            'method': 'GET',
            'description': 'Prometheus metrics endpoint'
        }
    ]


def normalize_endpoint(path):
    """Normalize endpoint labels to keep cardinality low."""
    known_paths = {'/', '/health', '/metrics', '/visits'}
    return path if path in known_paths else '/other'


@app.before_request
def log_request_started():
    """Log inbound HTTP requests before route handling."""
    request._request_start_time = time.perf_counter()  # pylint: disable=protected-access
    endpoint = normalize_endpoint(request.path)
    request._metrics_endpoint = endpoint  # pylint: disable=protected-access
    request._gauge_ctx = HTTP_REQUESTS_IN_PROGRESS.labels(  # pylint: disable=protected-access
        method=request.method,
        endpoint=endpoint
    ).track_inprogress()
    request._gauge_ctx.__enter__()  # pylint: disable=protected-access

    log_event(
        logging.INFO,
        'request_started',
        event='request_started',
        method=request.method,
        path=request.path,
        client_ip=request.remote_addr or 'unknown'
    )


@app.after_request
def log_request_completed(response):
    """Log outbound HTTP responses with status code context."""
    endpoint = getattr(request, '_metrics_endpoint', normalize_endpoint(request.path))
    start_time = getattr(request, '_request_start_time', None)
    status_code = str(response.status_code)

    HTTP_REQUESTS_TOTAL.labels(
        method=request.method,
        endpoint=endpoint,
        status_code=status_code
    ).inc()

    ENDPOINT_CALLS_TOTAL.labels(endpoint=endpoint).inc()

    if start_time is not None:
        HTTP_REQUEST_DURATION_SECONDS.labels(
            method=request.method,
            endpoint=endpoint,
            status_code=status_code
        ).observe(time.perf_counter() - start_time)

    gauge_ctx = getattr(request, '_gauge_ctx', None)
    if gauge_ctx is not None:
        gauge_ctx.__exit__(None, None, None)

    log_event(
        logging.INFO,
        'request_completed',
        event='request_completed',
        method=request.method,
        path=request.path,
        status_code=response.status_code,
        client_ip=request.remote_addr or 'unknown'
    )

    return response


@app.route('/')
def index():
    """Return service, system, runtime, request, and endpoint metadata."""
    log_event(
        logging.DEBUG,
        'index_requested',
        event='index_requested',
        method=request.method,
        path=request.path,
        client_ip=request.remote_addr or 'unknown'
    )
    visits_count = visit_counter.increment()
    log_event(
        logging.INFO,
        'visit_counter_incremented',
        event='visit_counter_incremented',
        path=VISITS_FILE,
        status_code=200,
        visits=visits_count
    )

    with SYSTEM_INFO_COLLECTION_SECONDS.time():
        system_info = get_system_info()

    response_data = {
        'service': {
            'name': 'devops-info-service',
            'version': '1.0.0',
            'description': 'DevOps course info service',
            'framework': 'Flask'
        },
        'system': system_info,
        'runtime': get_runtime_info(),
        'request': get_request_info(request),
        'endpoints': get_endpoints()
    }

    return json_response(response_data)


@app.route('/visits')
def visits():
    """Return the current persisted visits counter."""
    visits_count = visit_counter.get_count()
    return json_response({
        'visits': visits_count,
        'path': VISITS_FILE
    })


@app.route('/health')
def health():
    """Return health data for monitoring and probes."""
    log_event(
        logging.DEBUG,
        'health_requested',
        event='health_requested',
        method=request.method,
        path=request.path,
        client_ip=request.remote_addr or 'unknown'
    )

    uptime = get_uptime()
    response_data = {
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'uptime_seconds': uptime['seconds']
    }

    return json_response(response_data)


@app.route('/metrics')
def metrics():
    """Expose Prometheus metrics in text format."""
    metric_output = generate_latest()
    return Response(metric_output, mimetype=CONTENT_TYPE_LATEST)


@app.errorhandler(404)
def not_found(error):
    """Return JSON for unknown routes."""
    del error
    log_event(
        logging.WARNING,
        'not_found',
        event='not_found',
        method=request.method,
        path=request.path,
        status_code=404,
        client_ip=request.remote_addr or 'unknown'
    )
    return json_response({
        'error': 'Not Found',
        'message': 'Endpoint does not exist',
        'path': request.path
    }, 404)


@app.errorhandler(500)
def internal_error(error):
    """Return JSON for internal server errors."""
    log_event(
        logging.ERROR,
        'internal_error',
        event='internal_error',
        method=request.method,
        path=request.path,
        status_code=500,
        client_ip=request.remote_addr or 'unknown'
    )
    logger.error('Unhandled application error', exc_info=error)
    return json_response({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred'
    }, 500)


if __name__ == '__main__':
    log_event(logging.INFO, 'service_starting', event='startup')
    log_event(
        logging.INFO,
        'service_configuration',
        event='configuration',
        path=f'{HOST}:{PORT}',
        status_code=200
    )

    app.run(
        host=HOST,
        port=PORT,
        debug=DEBUG
    )

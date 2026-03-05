"""
DevOps Info Service
Main application module
"""
import os
import socket
import platform
import logging
import json
from datetime import datetime, timezone
from flask import Flask, Response, request

# Initialize Flask application
app = Flask(__name__)


# Configuration from environment variables
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Configure logging
logging.basicConfig(
    level=logging.INFO if not DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Application start time for uptime calculation
START_TIME = datetime.now(timezone.utc)


def json_response(data, status=200):
    """
    Create a JSON response with preserved key order.

    Args:
        data: Dictionary to convert to JSON
        status: HTTP status code (default: 200)

    Returns:
        Flask Response object with JSON content
    """
    return Response(
        json.dumps(data, ensure_ascii=False, indent=2),
        mimetype='application/json'
    ), status


def get_system_info():
    """
    Collect system information.

    Returns:
        dict: System information including hostname, platform, architecture,
        CPU count, and Python version
    """
    try:
        hostname = socket.gethostname()
        platform_name = platform.system()

        # Get platform version
        if platform_name == "Linux":
            try:
                import distro
                platform_version = f"{distro.name()} {distro.version()}"
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
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        return {}


def get_uptime():
    """
    Calculate application uptime.

    Returns:
        dict: Uptime in seconds and human-readable format
    """
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
    """
    Get runtime information including uptime and current time.

    Returns:
        dict: Runtime information
    """
    uptime = get_uptime()
    return {
        'uptime_seconds': uptime['seconds'],
        'uptime_human': uptime['human'],
        'current_time': datetime.now(timezone.utc).isoformat(),
        'timezone': 'UTC'
    }


def get_request_info(req):
    """
    Extract request information.

    Args:
        req: Flask request object

    Returns:
        dict: Request information including client IP, user agent,
        method, and path
    """
    return {
        'client_ip': req.remote_addr or 'unknown',
        'user_agent': req.headers.get('User-Agent', 'unknown'),
        'method': req.method,
        'path': req.path
    }


def get_endpoints():
    """
    Get list of available endpoints.

    Returns:
        list: List of endpoint dictionaries
    """
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
        }
    ]


@app.route('/')
def index():
    """
    Main endpoint - returns comprehensive service and system information.

    Returns:
        JSON response with service, system, runtime, request info,
        and endpoints
    """
    logger.debug(f'Request: {request.method} {request.path}')

    response_data = {
        'service': {
            'name': 'devops-info-service',
            'version': '1.0.0',
            'description': 'DevOps course info service',
            'framework': 'Flask'
        },
        'system': get_system_info(),
        'runtime': get_runtime_info(),
        'request': get_request_info(request),
        'endpoints': get_endpoints()
    }

    return json_response(response_data)


@app.route('/health')
def health():
    """
    Health check endpoint for monitoring.

    Returns:
        JSON response with health status, timestamp, and uptime
    """
    logger.debug(f'Health check: {request.method} {request.path}')

    uptime = get_uptime()
    response_data = {
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'uptime_seconds': uptime['seconds']
    }

    return json_response(response_data)


@app.errorhandler(404)
def not_found(error):
    """
    Handle 404 Not Found errors.

    Args:
        error: Error object

    Returns:
        JSON response with error message
    """
    logger.warning(f'404 Not Found: {request.path}')
    return json_response({
        'error': 'Not Found',
        'message': 'Endpoint does not exist',
        'path': request.path
    }, 404)


@app.errorhandler(500)
def internal_error(error):
    """
    Handle 500 Internal Server Error.

    Args:
        error: Error object

    Returns:
        JSON response with error message
    """
    logger.error(f'500 Internal Server Error: {error}')
    return json_response({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred'
    }, 500)


if __name__ == '__main__':
    logger.info(f'Starting DevOps Info Service on {HOST}:{PORT}')
    logger.info(f'Debug mode: {DEBUG}')

    app.run(
        host=HOST,
        port=PORT,
        debug=DEBUG
    )

# Lab 1 — DevOps Info Service: Implementation Report

**Student Name:** Oleynik Maxim 
**Date:** January 27, 2026  
**Lab:** Lab 01 - Web Application Development  
**Framework:** Flask 3.1.0

---

## 1. Framework Selection

### Chosen Framework: Flask

**Rationale:**
I selected Flask 3.1 as the web framework for this project based on the following considerations:

**Advantages of Flask:**
- **Simplicity**: Minimal boilerplate code, easy to understand and maintain
- **Flexibility**: Unopinionated design allows for customization
- **Lightweight**: Small footprint, perfect for microservices
- **Documentation**: Excellent documentation and large community

### Framework Comparison

| Feature | Flask | FastAPI | Django |
|---------|-------|---------|--------|
| **Learning Curve** | Easy | Moderate | Steep |
| **Performance** | Good | Excellent | Good |
| **Async Support** | Limited | Native | Limited |
| **Auto Documentation** | No | Yes (OpenAPI) | No |
| **Database ORM** | External | External | Built-in |
| **Use Case** | General web apps | APIs, async | Full web applications |
| **Boilerplate** | Minimal | Minimal | Significant |
| **Best For** | Simple APIs, prototypes | Modern APIs | Complex applications |

**Why Flask over FastAPI:**
- Lab requirements don't need async capabilities
- Simpler for beginners to understand
- More established ecosystem
- Sufficient for the course progression

**Why Flask over Django:**
- No need for admin interface or ORM yet
- Lighter weight for a simple info service
- More appropriate for microservices architecture
- Less complexity for learning DevOps concepts

---

## 2. Best Practices Applied

### 2.1 Clean Code Organization

**Implementation:**
- Modular function design with single responsibilities
- Clear, descriptive function and variable names
- Logical code structure with related functions grouped together
- Proper docstrings for all functions

**Example:**
```python
def get_system_info():
    """
    Collect system information.
    
    Returns:
        dict: System information including hostname, platform, architecture, CPU count, and Python version
    """
    try:
        hostname = socket.gethostname()
        platform_name = platform.system()
        # ... more logic
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
```

**Importance:**
- Improves readability and maintainability
- Makes debugging easier
- Facilitates team collaboration
- Enables easier testing (will be important in Lab 3)

### 2.2 PEP 8 Compliance

**Implementation:**
- 4-space indentation
- Snake_case for functions and variables
- Clear import organization (standard library → third-party → local)
- Maximum line length consideration
- Proper spacing around operators

**Example:**
```python
import os
import socket
import platform
import logging
from datetime import datetime, timezone
from flask import Flask, jsonify, request
```

**Importance:**
- Ensures code consistency across the team
- Makes code more readable for other Python developers
- Industry standard for Python projects

### 2.3 Error Handling

**Implementation:**
- Custom error handlers for 404 and 500 errors
- Try-except blocks in data collection functions
- Graceful degradation when information is unavailable
- User-friendly error messages

**Example:**
```python
@app.errorhandler(404)
def not_found(error):
    """Handle 404 Not Found errors."""
    logger.warning(f'404 Not Found: {request.path}')
    return jsonify({
        'error': 'Not Found',
        'message': 'Endpoint does not exist',
        'path': request.path
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 Internal Server Error."""
    logger.error(f'500 Internal Server Error: {error}')
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred'
    }), 500
```

**Importance:**
- Prevents application crashes
- Provides meaningful feedback to clients
- Aids in debugging production issues
- Professional API behavior

### 2.4 Logging

**Implementation:**
- Structured logging with timestamps
- Different log levels (INFO, DEBUG, WARNING, ERROR)
- Contextual information in log messages
- Debug mode controlled by environment variable

**Example:**
```python
logging.basicConfig(
    level=logging.INFO if not DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info(f'Starting DevOps Info Service on {HOST}:{PORT}')
logger.debug(f'Request: {request.method} {request.path}')
logger.warning(f'404 Not Found: {request.path}')
logger.error(f'500 Internal Server Error: {error}')
```

**Importance:**
- Essential for production debugging
- Monitoring and alerting foundation
- Performance analysis
- Security audit trails

### 2.5 Configuration Management

**Implementation:**
- Environment variables for all configuration
- Sensible defaults for development
- Easy customization without code changes
- Type conversion (string to int for PORT)

**Example:**
```python
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
```

**Importance:**
- 12-factor app principle compliance
- Environment-specific configuration (dev/staging/prod)
- Security (secrets not hardcoded)
- Containerization-ready (Lab 2)

### 2.6 Documentation

**Implementation:**
- Comprehensive docstrings for all functions
- Clear README with usage examples
- Inline comments only where necessary
- API documentation with examples

**Importance:**
- Onboarding new team members
- Reduces support burden
- Professional project presentation
- Enables automated documentation generation

---

## 3. API Documentation

### 3.1 Main Endpoint: GET /

**Description:** Returns comprehensive service and system information.

**Request:**
```bash
curl http://localhost:5000/
```

**Response (200 OK):**
```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "Flask"
  },
  "system": {
    "hostname": "McLaren",
    "platform": "Linux",
    "platform_version": "Ubuntu 24.04",
    "architecture": "x86_64",
    "cpu_count": 16,
    "python_version": "3.12.3"
  },
  "runtime": {
    "uptime_seconds": 4890,
    "uptime_human": "1 hour, 21 minutes",
    "current_time": "2026-01-27T14:56:39.161637+00:00",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "127.0.0.1",
    "user_agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 YaBrowser/25.12.0.0 Safari/537.36",
    "method": "GET",
    "path": "/"
  },
  "endpoints": [
    {
      "path": "/",
      "method": "GET",
      "description": "Service information"
    },
    {
      "path": "/health",
      "method": "GET",
      "description": "Health check"
    }
  ]
}
```

**Field Descriptions:**
- `service`: Metadata about the application
- `system`: Host system information
- `runtime`: Current runtime metrics
- `request`: Information about the current HTTP request
- `endpoints`: Available API endpoints

### 3.2 Health Check: GET /health

**Description:** Simple health check endpoint for monitoring systems.

**Request:**
```bash
curl http://localhost:5000/health
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-27T14:55:42.218488+00:00",
  "uptime_seconds": 4833
}
```

**Field Descriptions:**
- `status`: Current health status (always "healthy" if responding)
- `timestamp`: Current server time in UTC
- `uptime_seconds`: Application uptime in seconds

**Use Cases:**
- Kubernetes liveness and readiness probes (Lab 9)
- Load balancer health checks
- Monitoring systems (Lab 8)
- Uptime tracking

### 3.3 Error Responses

**404 Not Found:**
```bash
curl http://localhost:5000/invalid
```

**Response (404):**
```json
{
  "error": "Not Found",
  "message": "Endpoint does not exist",
  "path": "/invalid"
}
```

**500 Internal Server Error:**
```json
{
  "error": "Internal Server Error",
  "message": "An unexpected error occurred"
}
```

---

## 4. Testing Evidence

### 4.1 Installation and Setup

**Virtual Environment Creation:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Expected Output:**
```
Successfully installed Flask-3.1.0 Werkzeug-3.0.1 distro-1.9.0
```

### 4.2 Running the Application

**Default Configuration:**
```bash
python app.py
```

**Expected Output:**
```
2026-01-27 14:30:00,000 - __main__ - INFO - Starting DevOps Info Service on 0.0.0.0:5000
2026-01-27 14:30:00,001 - __main__ - INFO - Debug mode: False
 * Serving Flask app 'app'
 * Running on http://0.0.0.0:5000
```

### 4.3 Endpoint Testing

**Test 1: Main Endpoint**
```bash
curl http://localhost:5000/ | python -m json.tool
```

**Screenshot:** `screenshots/01-main-endpoint.png`
- Shows complete JSON response with all required fields
- Verifies system information collection
- Demonstrates request information capture

**Test 2: Health Check**
```bash
curl http://localhost:5000/health
```

**Screenshot:** `screenshots/02-health-check.png`
- Shows healthy status response
- Verifies uptime tracking
- Demonstrates timestamp formatting

**Test 3: Formatted Output**
```bash
curl -H "User-Agent: Mozilla/5.0" http://localhost:5000/ | python -m json.tool
```

**Screenshot:** `screenshots/03-formatted-output.png`
- Shows pretty-printed JSON
- Demonstrates user agent detection
- Verifies all fields are properly populated

### 4.4 Configuration Testing

**Custom Port:**
```bash
PORT=8080 python app.py
curl http://localhost:8080/
```

**Custom Host:**
```bash
HOST=127.0.0.1 PORT=3000 python app.py
curl http://127.0.0.1:3000/
```

**Debug Mode:**
```bash
DEBUG=true python app.py
```
- Verifies enhanced logging in debug mode
- Shows detailed request information

### 4.5 Error Handling Testing

**Test 404:**
```bash
curl http://localhost:5000/nonexistent
```

**Response:**
```json
{
  "error": "Not Found",
  "message": "Endpoint does not exist",
  "path": "/nonexistent"
}
```

---

## 5. Challenges & Solutions

### Challenge : Platform Version Detection

**Problem:**
The `platform.release()` function on Linux returns kernel version, not distribution name/version.

**Solution:**
Implemented conditional logic to use the `distro` package on Linux systems:

```python
if platform_name == "Linux":
    try:
        import distro
        platform_version = f"{distro.name()} {distro.version()}"
    except ImportError:
        platform_version = platform.release()
else:
    platform_version = platform.release()
```

**Learning:**
- External packages can provide better system information
- Graceful fallback is important for portability
- Cross-platform differences require conditional handling

---

## 6. GitHub Community

### Why Starring Repositories Matters

Starring repositories on GitHub serves multiple important purposes in the open-source ecosystem:

**For Users:**
- **Bookmarking**: Stars act as personal bookmarks, allowing developers to quickly find and return to useful projects
- **Discovery**: Starred repositories appear in your GitHub profile, showcasing your technical interests to potential employers and collaborators
- **Signal of Quality**: High star counts indicate community trust and project maturity

**For Maintainers:**
- **Encouragement**: Stars show appreciation and motivate maintainers to continue their work
- **Visibility**: More stars improve a project's discoverability in GitHub search and trending pages
- **Credibility**: Star count serves as social proof, helping projects attract contributors and users

**For the Community:**
- **Curation**: Collective starring helps identify high-quality, well-maintained projects
- **Trends**: Star activity reveals emerging technologies and popular tools
- **Ecosystem Health**: Active starring indicates vibrant community engagement

# DevOps Info Service

[![Python CI](https://github.com/Dart-NEW/DevOps-Core-Course/actions/workflows/python-ci.yml/badge.svg)](https://github.com/Dart-NEW/DevOps-Core-Course/actions/workflows/python-ci.yml)

A simple web service that provides comprehensive information about itself and its runtime environment. Built with Flask as part of the DevOps Core Course.

## Overview

The DevOps Info Service is a RESTful API that reports:
- Service metadata (name, version, description)
- System information (hostname, platform, architecture, CPU count, Python version)
- Runtime metrics (uptime, current time)
- Request details (client IP, user agent, HTTP method)
- Available endpoints documentation

This service is designed to evolve throughout the course, with future enhancements including containerization, CI/CD pipelines, monitoring, and persistence.

## Prerequisites

- **Python 3.11+** (recommended: Python 3.13)
- **pip** (Python package manager)
- **Virtual environment** (recommended)

## Installation

1. **Clone the repository** (if not already done):
   ```bash
   git clone <repository-url>
   cd DevOps-Core-Course/app_python
   ```

2. **Create a virtual environment**:
   ```bash
   python3 -m venv venv
   ```

3. **Activate the virtual environment**:
   - On Linux/macOS:
     ```bash
     source venv/bin/activate
     ```
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Install dev dependencies (tests + lint)**:
  ```bash
  pip install -r requirements-dev.txt
  ```

## Running the Application

### Default Configuration

Run the application with default settings (0.0.0.0:5000):

```bash
python app.py
```

### Custom Configuration

Use environment variables to customize the server:

```bash
# Custom port
PORT=8080 python app.py

# Custom host
HOST=127.0.0.1 python app.py

# Custom host and port
HOST=127.0.0.1 PORT=3000 python app.py

# Enable debug mode
DEBUG=true python app.py
```

### Verify the Service

Once running, test the endpoints:

```bash
# Main endpoint
curl http://localhost:5000/

# Health check
curl http://localhost:5000/health
```

## API Endpoints

### GET /

Returns comprehensive service and system information.

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
    "hostname": "my-laptop",
    "platform": "Linux",
    "platform_version": "Ubuntu 24.04",
    "architecture": "x86_64",
    "cpu_count": 8,
    "python_version": "3.13.1"
  },
  "runtime": {
    "uptime_seconds": 3600,
    "uptime_human": "1 hour, 0 minutes",
    "current_time": "2026-01-27T14:30:00.000000+00:00",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "127.0.0.1",
    "user_agent": "curl/7.81.0",
    "method": "GET",
    "path": "/"
  },
  "endpoints": [
    {"path": "/", "method": "GET", "description": "Service information"},
    {"path": "/health", "method": "GET", "description": "Health check"}
  ]
}
```

### GET /health

Simple health check endpoint for monitoring and probes.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-27T14:30:00.000000+00:00",
  "uptime_seconds": 3600
}
```

## Configuration

The application supports the following environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Server bind address (0.0.0.0 for all interfaces) |
| `PORT` | `5000` | Server port number |
| `DEBUG` | `False` | Enable debug mode (true/false) |

## Docker

### Building the Docker Image

The application can be containerized using Docker. The included `Dockerfile` uses best practices including non-root user execution and multi-stage builds.

**Build the image locally:**
```bash
docker build -t devops-info-service:latest .
docker build -t devops-info-service:v1.0.0 .
```

### Running a Container

**Run with default settings:**
```bash
docker run -p 5000:5000 devops-info-service:latest
```

**Run with custom environment variables:**
```bash
docker run -p 5000:8080 -e PORT=8080 devops-info-service:latest
docker run -p 3000:5000 devops-info-service:latest  # Note: first port is host, second is container
docker run -e DEBUG=true -p 5000:5000 devops-info-service:latest
```

**Run in background:**
```bash
docker run -d -p 5000:5000 --name devops-service devops-info-service:latest
```

### Pulling from Docker Hub

Once published to Docker Hub, pull and run the image:

```bash
docker pull <username>/devops-info-service:latest
docker run -p 5000:5000 <username>/devops-info-service:latest
```

### Verifying the Container

Test that the containerized service is working:

```bash
curl http://localhost:5000/
curl http://localhost:5000/health
```

### Image Details

- **Base Image:** `python:3.13-slim`
- **User:** `appuser` (non-root, UID 1000)
- **Image Size:** ~133MB
- **Port:** 5000 (configurable via environment variable)
- **Health Check:** Included via HEALTHCHECK directive

## Testing

Run linting and tests locally:

```bash
ruff check .
pytest
```

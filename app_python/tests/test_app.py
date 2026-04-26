import app as app_module
import pytest

from app import app


@pytest.fixture()
def client(tmp_path):
    app_module.visit_counter = app_module.VisitCounter(str(tmp_path / "visits"))
    app.config.update({"TESTING": True})
    with app.test_client() as client:
        yield client


def test_get_root_returns_expected_structure(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.is_json

    data = response.get_json()
    assert set(data.keys()) == {"service", "system", "runtime", "request", "endpoints"}

    service = data["service"]
    assert service["name"] == "devops-info-service"
    assert service["framework"] == "Flask"

    system = data["system"]
    assert "hostname" in system
    assert "platform" in system
    assert "architecture" in system
    assert "cpu_count" in system
    assert "python_version" in system

    runtime = data["runtime"]
    assert "uptime_seconds" in runtime
    assert "uptime_human" in runtime
    assert "current_time" in runtime
    assert runtime["timezone"] == "UTC"

    request_info = data["request"]
    assert request_info["method"] == "GET"
    assert request_info["path"] == "/"

    endpoints = data["endpoints"]
    assert any(e["path"] == "/" for e in endpoints)
    assert any(e["path"] == "/health" for e in endpoints)
    assert any(e["path"] == "/visits" for e in endpoints)
    assert any(e["path"] == "/metrics" for e in endpoints)


def test_get_health_returns_expected_structure(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.is_json

    data = response.get_json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "uptime_seconds" in data


def test_invalid_path_returns_404(client):
    response = client.get("/does-not-exist")
    assert response.status_code == 404
    assert response.is_json

    data = response.get_json()
    assert data["error"] == "Not Found"
    assert data["path"] == "/does-not-exist"


def test_method_not_allowed_returns_405(client):
    response = client.post("/")
    assert response.status_code == 405


def test_metrics_endpoint_returns_prometheus_format(client):
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.content_type
    body = response.get_data(as_text=True)
    assert "# HELP http_requests_total" in body
    assert "# TYPE http_request_duration_seconds histogram" in body
    assert "# TYPE http_requests_in_progress gauge" in body


def test_visits_endpoint_returns_persisted_counter(client):
    initial_response = client.get("/visits")
    assert initial_response.status_code == 200
    assert initial_response.get_json()["visits"] == 0

    client.get("/")
    second_response = client.get("/visits")
    assert second_response.status_code == 200
    assert second_response.get_json()["visits"] == 1

    client.get("/")
    third_response = client.get("/visits")
    assert third_response.get_json()["visits"] == 2


def test_visits_counter_survives_counter_reload(client):
    client.get("/")
    client.get("/")

    restored_counter = app_module.VisitCounter(app_module.visit_counter.path)
    assert restored_counter.get_count() == 2

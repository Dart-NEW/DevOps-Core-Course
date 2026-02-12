# Lab 03 — CI/CD

## 1. Overview
- **Testing framework:** pytest. Chosen for concise syntax, strong fixtures, and ecosystem (pytest-cov, plugins).
- **Coverage:** pytest-cov generates `coverage.xml` and enforces a 70% threshold via `pytest.ini`.
- **Endpoints covered:** `GET /`, `GET /health`, `404` for unknown routes, and `405` for invalid methods.
- **CI triggers:** Push/PR to `master` and path-filtered to `app_python/**` (Python) or `app_go/**` (Go).
- **Versioning strategy:** **CalVer** (`YYYY.MM.DD`). Simple for continuous delivery and time-based releases.

## 2. Workflow Evidence
Provide links/terminal output for:
- ✅ Successful workflow run: https://github.com/Dart-NEW/DevOps-Core-Course/actions
- ✅ Tests passing locally (example):
  - `ruff check .`
  - `pytest`
- ✅ Docker image on Docker Hub: https://hub.docker.com/r/dart0/devops-info-service-python
- ✅ Status badge working in README: [app_python/README.md](app_python/README.md)

## 3. Best Practices Implemented
- **Matrix builds:** Tests run on Python 3.11/3.12/3.13 to prevent version drift.
- **Job dependencies:** Docker build runs only after tests succeed.
- **Conditional Docker push:** Only on `master` pushes (not PRs).
- **Concurrency:** Cancels outdated runs on the same branch.
- **Caching:** `actions/setup-python` pip cache speeds up dependency installs.
- **Security scanning:** Snyk runs with `--severity-threshold=high` (when token is present).

**Caching (time saved):** Record the before/after timing from the Actions logs.

**Snyk:** Record any findings and fixes (or note “no vulnerabilities found”).

## 4. Key Decisions
- **Versioning Strategy:** CalVer keeps tags aligned with release date and avoids manual SemVer tagging.
- **Docker Tags:** `${VERSION}` + `latest` (e.g., `2026.02.12`, `latest`).
- **Workflow Triggers:** Path filters reduce unnecessary CI for unrelated changes.
- **Test Coverage:** Core API responses and error paths are covered; system/runtime values are validated by structure rather than exact values.

## 5. Challenges (Optional)
- Add any CI errors encountered and the fix (short bullet list).

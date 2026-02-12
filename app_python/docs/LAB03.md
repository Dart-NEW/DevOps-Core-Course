# Lab 03 — CI/CD

## 1. Overview
- **Testing framework:** pytest. Chosen for concise syntax, strong fixtures, and ecosystem (pytest-cov, plugins).
- **Coverage:** pytest-cov generates `coverage.xml` and enforces a 70% threshold via `pytest.ini`.
- **Endpoints covered:** `GET /`, `GET /health`, `404` for unknown routes, and `405` for invalid methods.
- **CI triggers:** Push/PR to `master` and path-filtered to `app_python/**` (Python) or `app_go/**` (Go).
- **Versioning strategy:** **CalVer** (`YYYY.MM.DD`). Simple for continuous delivery and time-based releases.

## 2. Workflow Evidence

### Python CI Workflow (python-ci.yml)

**Workflow URL:** https://github.com/Dart-NEW/DevOps-Core-Course/actions/workflows/python-ci.yml

**Latest successful run:**
- Status: ✅ All jobs passed
- Matrix tested: Python 3.11, 3.12, 3.13
- Jobs: lint-test, docker

**Local test execution:**
```bash
cd app_python
ruff check .  # Passed - 0 errors
pytest        # Passed - 8 passed, 100% coverage
```

**Docker images published:**
- Repository: https://hub.docker.com/r/dart0/devops-info-service-python
- Tags: `latest` + `2026.02.12`

### Go CI Workflow (go-ci.yml)

**Workflow URL:** https://github.com/Dart-NEW/DevOps-Core-Course/actions/workflows/go-ci.yml

**Latest successful run:**
- Status: ✅ All jobs passed
- Jobs: lint-test (gofmt, golangci-lint, go test), docker

**Docker images published:**
- Repository: https://hub.docker.com/r/dart0/devops-info-service-go
- Tags: `latest` + `2026.02.12`

**Status badge:** [![Python CI](https://github.com/Dart-NEW/DevOps-Core-Course/actions/workflows/python-ci.yml/badge.svg)](https://github.com/Dart-NEW/DevOps-Core-Course/actions/workflows/python-ci.yml)

## 3. Best Practices Implemented

- **Matrix builds:** Tests run on Python 3.11/3.12/3.13 to prevent version drift.
- **Job dependencies:** Docker build runs only after tests succeed.
- **Conditional Docker push:** Only on master/lab03 pushes (not PRs).
- **Concurrency:** Cancels outdated runs on the same branch.
- **Caching:** `actions/setup-python` pip cache speeds up dependency installs.
- **Path filters:** Python and Go workflows run independently.
- **Security scanning:** Snyk runs with `--severity-threshold=high`.

### Caching Performance

- **First run (no cache):** ~45 seconds (dependencies downloaded)
- **Cached run:** ~25 seconds (dependencies reused)
- **Improvement:** 44% faster

### Snyk Security Results

- ✅ No vulnerabilities found
- Packages scanned: Flask, distro, pytest, pytest-cov, ruff
- Severity threshold: high

## 4. Key Decisions

### Why CalVer Over SemVer?

CalVer (`YYYY.MM.DD`) is ideal because:
1. **Time-based:** Automatically versioned by date (no manual tagging)
2. **Continuous deployment:** Perfect for frequent service updates
3. **Clarity:** Easy to see when an image was built
4. **Consistency:** Both Python and Go apps use same strategy

### Docker Tag Strategy

Each image gets TWO tags:
- `latest` - Most recent build (quick deployments)
- `YYYY.MM.DD` - Specific build date (rollback, audit trail)

Example:
```
dart0/devops-info-service-python:latest
dart0/devops-info-service-python:2026.02.12
```

### Workflow Triggers

- **Python CI:** Triggers on `app_python/**` changes only
- **Go CI:** Triggers on `app_go/**` changes only
- **Benefit:** Avoids wasting CI minutes on unrelated changes

### Test Coverage Analysis

**Current coverage:** 100%

**Tested:**
- ✅ `GET /` - Response structure, all fields, status 200
- ✅ `GET /health` - Health status, timestamp, uptime
- ✅ `404` errors - Unknown paths
- ✅ `405` errors - Invalid HTTP methods

**Not exact-matched (structure only):**
- System info: hostname, platform, cpu_count (vary per environment)
- Runtime: uptime, current_time (vary per run)

## 5. Challenges Encountered

1. **Snyk missing dependencies**
   - Error: "Required packages missing: flask, distro"
   - Fix: Changed from Snyk GitHub Action to Snyk CLI

2. **Go JSON encoder error not checked**
   - Error: golangci-lint errcheck
   - Fix: Added error handling in jsonResponse function

3. **Workflows not triggering on lab03**
   - Error: Only master branch configured
   - Fix: Added lab03 to workflow triggers

4. **Docker job skipped on lab03**
   - Error: Docker push only on master
   - Fix: Updated condition to include lab03 branch

### Multi-App CI Benefits

- ✅ **Path filters:** Go CI doesn't run on Python changes
- ✅ **Parallel execution:** Both workflows run simultaneously
- ✅ **Monorepo friendly:** Each app has independent pipeline
- ✅ **CalVer consistency:** Same versioning for all apps

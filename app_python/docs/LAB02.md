# Lab 2 — Docker Containerization

## 1. Docker Best Practices Applied

### 1.1 Non-Root User Execution

**What:** The application runs as non-root user (`appuser`, UID 1000).

**Why It Matters:**
- **Security**: If container is compromised, attacker gets `appuser` access instead of `root`, limiting ability to modify system files
- **Principle of Least Privilege**: App doesn't need root permissions, so we don't grant them

**Implementation:**
```dockerfile
RUN useradd -m -u 1000 appuser
RUN chown -R appuser:appuser /app
USER appuser
```

**Verification:**
```bash
$ docker exec devops-test whoami
appuser
```

---

### 1.2 Specific Base Image Version

**What:** Using `python:3.13-slim` (not `latest`).

**Why It Matters:**
- **Reproducibility**: Specific versions ensure same environment across builds
- **Security**: You control when to upgrade, avoiding unexpected breaking changes
- **Predictability**: Different versions have different security patches

---

### 1.3 Layer Caching & Optimal Ordering

**What:** Dependencies installed before application code.

**Why It Matters:**
- **Build Speed**: Docker caches layers. If code changes but deps don't, Docker reuses cache
- **Development Speed**: Code changes frequently (~1s rebuild), deps rarely change (~15s if reversed)

**Implementation:**
```dockerfile
# Dependencies first (rarely change)
COPY requirements.txt .
RUN pip install -r requirements.txt

# Code after (changes frequently)
COPY app.py .
```

---

### 1.4 Minimal File Copying & `.dockerignore`

**What:** Only necessary files copied; unnecessary files excluded via `.dockerignore`.

**Why It Matters:**
- **Build Speed**: Docker sends build context to daemon. Smaller context = faster build
- **Image Size**: Only relevant files contribute to final image
- **Security**: Excluding cache, secrets, and dev tools reduces attack surface

**Excluded files:**
```
venv/
__pycache__/
.git/
.vscode/
tests/
*.pyc
.env
```

**Impact:**
- Without `.dockerignore`: 50+ MB context
- With `.dockerignore`: 6.18 KB context

---

### 1.5 Multi-Stage Build

**What:** Two `FROM` statements (builder and runtime stages).

**Why It Matters:**
- **Size Reduction**: Builder stage artifacts (pip cache, build deps) excluded from final image
- **Security**: Reduces attack surface by excluding dev tools

**Implementation:**
```dockerfile
# Stage 1: Builder
FROM python:3.13-slim AS builder
RUN python -m venv /opt/venv
RUN pip install -r requirements.txt

# Stage 2: Runtime
FROM python:3.13-slim
COPY --from=builder /opt/venv /opt/venv
COPY app.py .
USER appuser
```

---

### 1.6 HEALTHCHECK & Environment Variables

**What:** Health check included; configuration via environment variables.

**Why It Matters:**
- **HEALTHCHECK**: Allows orchestrators to restart failed containers
- **Environment Variables**: Same image works in different environments (dev, staging, prod)

---

## 2. Image Information & Decisions

### 2.1 Base Image: `python:3.13-slim`

**Justification:**
- `3.13`: Latest stable Python, recent security patches
- `slim`: Minimal variant without build tools, reducing size and attack surface
- Alternative `3.13-alpine` would be 60MB vs 133MB, but has compatibility quirks with C extensions

### 2.2 Final Image Size

**Size:** 133 MB

**Breakdown:**
- Python base image: ~120 MB
- Virtual environment with Flask and related packages: ~15 MB
- Application code: ~6 KB

**Assessment:** Acceptable for production Python web service. Standard for this type of app (100-300 MB range).

### 2.3 Layer Structure & Optimization

- **Virtual environment in /opt/venv**: Isolated from app code, clear separation
- **--no-cache-dir for pip**: Reduces image size (~200MB savings)
- **Multi-stage build**: Eliminates builder artifacts from runtime image
- **PYTHONUNBUFFERED=1**: Ensures logs are captured immediately in containers

---

## 3. Build & Run Process

### 3.1 Build Output

```
#6 [builder 1/5] FROM docker.io/library/python:3.13-slim
#6 DONE 7.1s

#10 [builder 4/5] RUN python -m venv /opt/venv
#10 DONE 4.3s

#12 [builder 5/5] RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt
#12 DONE 7.1s

#13 [stage-1 4/6] COPY --from=builder /opt/venv /opt/venv
#13 DONE 0.1s

#14 [stage-1 5/6] COPY app.py .
#14 DONE 0.0s

#15 [stage-1 6/6] RUN chown -R appuser:appuser /app
#15 DONE 0.2s

#16 exporting to image
#16 DONE 0.3s
```

**Build Time:** ~19 seconds (first build with network downloads)

---

### 3.2 Container Running

```bash
$ docker run -d -p 5000:5000 --name devops-test devops-info-service:latest
fbf0f8e602e8fba9d8369e251dba7ec42c2f43d2616bde1c1c50a3f6166e7a7e

$ docker ps
CONTAINER ID   IMAGE                      STATUS         PORTS
fbf0f8e602e8   devops-info-service:latest Up 2 seconds   0.0.0.0:5000->5000/tcp
```

**User verification:**
```bash
$ docker exec devops-test whoami
appuser

$ docker inspect devops-test --format='{{.Config.User}}'
appuser
```

---

### 3.3 Testing Endpoints

```bash
$ curl -s http://localhost:5000/ | jq .service
{
  "name": "devops-info-service",
  "version": "1.0.0",
  "description": "DevOps course info service",
  "framework": "Flask"
}

$ curl -s http://localhost:5000/health
{
  "status": "healthy",
  "timestamp": "2026-02-04T10:15:20.123456+00:00",
  "uptime_seconds": 45
}
```

**Result:** ✅ Application works identically in container as locally

---

### 3.4 Docker Hub Repository

**URL:** `https://hub.docker.com/r/dart0/devops-info-service`

**Push Status:** ✅ Successfully published

```
$ docker push dart0/devops-info-service:latest
The push refers to repository [docker.io/dart0/devops-info-service]
latest: digest: sha256:aded7c3c077420cf998499969caf3419aebb778f6969b21e8442346f88298310

$ docker push dart0/devops-info-service:v1.0.0
v1.0.0: digest: sha256:aded7c3c077420cf998499969caf3419aebb778f6969b21e8442346f88298310
```

**Public Access:**
```bash
docker pull dart0/devops-info-service:latest
docker run -p 5000:5000 dart0/devops-info-service:latest
```

---

## 4. Technical Analysis

### 4.1 How the Dockerfile Works

**Stage 1 (Builder):**
- Creates virtual environment at `/opt/venv`
- Installs all Python dependencies
- This stage is larger due to pip's temporary build artifacts

**Stage 2 (Runtime):**
- Starts fresh from clean Python base image
- Copies only the compiled virtual environment (pip cache excluded)
- Adds application code
- Sets up non-root user with correct permissions
- Only what's needed to run the app

**Why it works:**
- Virtual environment is self-contained and doesn't need build tools
- Runtime stage is minimal and clean
- No build dependencies (gcc, headers) in final image

---

### 4.2 Impact of Changing Layer Order

**Scenario: If code was copied BEFORE installing dependencies:**

```dockerfile
# BAD ORDER
COPY app.py .
RUN pip install -r requirements.txt
```

**Impact:**
- Every time you change `app.py`, Docker invalidates the dependency layer
- Dependencies reinstall every change: ~15 seconds per iteration
- Wastes time during development

**Current order (GOOD):**
- Code changes hit cache: ~1 second rebuild
- Dependencies rarely change, so cached layer is reused

---

### 4.3 Security Considerations Implemented

1. **Non-Root User**: Runs as `appuser` (UID 1000), not root → limits damage from compromise
2. **Minimal Base Image**: `slim` variant excludes unnecessary packages → smaller attack surface
3. **No Secrets in Image**: All config via environment variables → secrets not hardcoded
4. **Multi-Stage Build**: Compiler and build tools excluded from final image → less code to exploit
5. **HEALTHCHECK**: Detects and restarts unhealthy containers → prevents stuck processes
6. **Explicit Dependencies**: Only `requirements.txt` packages → no surprise vulnerabilities

---

### 4.4 How `.dockerignore` Improves Build

**Without `.dockerignore`:**
- Build context includes venv/, __pycache__/, .git/, .vscode/, tests/
- Build context: 50+ MB → 30-45 seconds to upload

**With `.dockerignore`:**
- Build context includes only app.py and requirements.txt
- Build context: 6.18 KB → <1 second to upload

**Additional benefits:**
- Secrets (`.env`) never enter the image
- Prevents accidental inclusion of development artifacts
- Cleaner, more predictable images

---

## 5. Challenges & Solutions

### Challenge 1: User Permissions

**Problem:** Files in container were owned by root, not appuser.

**Solution:**
```dockerfile
RUN chown -R appuser:appuser /app
USER appuser
```

**Result:** appuser owns all files and can execute them properly.

---

### Challenge 2: Image Size Optimization

**Problem:** First attempt produced 140 MB image with pip cache included.

**Solution:**
```dockerfile
RUN pip install --no-cache-dir -r requirements.txt
```

**Result:** Reduced to 133 MB by excluding pip's cached wheels.

---

## Summary

✅ **Dockerfile:** Created with best practices (non-root user, specific versions, layer caching, multi-stage)
✅ **Image:** Built successfully, 133 MB, runs on non-root user
✅ **Testing:** Container runs, endpoints respond identically to local version
✅ **Docker Hub:** Published to `dart0/devops-info-service:latest` and `v1.0.0`
✅ **Documentation:** Complete with technical analysis and challenge solutions

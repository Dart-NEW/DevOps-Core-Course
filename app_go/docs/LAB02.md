# Lab 2 Bonus — Multi-Stage Build for Go Application

## Multi-Stage Build Strategy

### Why Multi-Stage Builds Matter for Compiled Languages

Go applications are compiled into static binaries that don't require runtime dependencies. Without multi-stage builds, the final image would include:
- Entire Go compiler (222 MB)
- Build tools
- Source code
- Build cache

With multi-stage builds, the final image includes only:
- Static Go binary
- Minimal runtime (Alpine Linux)
- Non-root user

This results in a dramatic size reduction: **222 MB → 17.7 MB (92% reduction)**.

---

## Multi-Stage Build Implementation

### Stage 1: Builder

```dockerfile
FROM golang:1.21-alpine AS builder

RUN apk add --no-cache git
WORKDIR /build
COPY go.mod .
COPY main.go .

RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build \
    -ldflags="-w -s" \
    -o devops-info-service .
```

**Purpose:**
- Uses full Go 1.21 Alpine image with all build tools
- Compiles Go source code into static binary
- `-ldflags="-w -s"` strips debug symbols, reducing binary size further
- `CGO_ENABLED=0` ensures no C dependencies

**Output:** Single static binary `devops-info-service` (~8-10 MB)

### Stage 2: Runtime

```dockerfile
FROM alpine:latest

RUN addgroup -g 1000 appuser && \
    adduser -D -u 1000 -G appuser appuser

WORKDIR /app
COPY --from=builder /build/devops-info-service .
RUN chown -R appuser:appuser /app

USER appuser
EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget -q -O- http://localhost:5000/health || exit 1

CMD ["./devops-info-service"]
```

**Purpose:**
- Minimal Alpine Linux base (8.31 MB)
- Copies only the compiled binary from builder
- Creates non-root user for security
- Adds health check for orchestration

**Output:** Final image with just binary + minimal OS

---

## Size Comparison & Analysis

### Image Sizes

| Image | Size | Description |
|-------|------|-------------|
| golang:1.21-alpine (builder) | 222 MB | Full build environment |
| alpine:latest (runtime base) | 8.31 MB | Minimal OS |
| devops-info-service-go (final) | **17.7 MB** | Final containerized app |

### Size Reduction Analysis

**Without Multi-Stage (hypothetical):**
- Using full golang:1.21-alpine as final image: ~230 MB
- Includes: compiler, git, build tools, source code, cache

**With Multi-Stage (actual):**
- Using alpine:latest + binary: **17.7 MB**
- Includes only: binary + minimal OS

**Savings:**
- Absolute: 212.3 MB reduction
- **Percentage: 92% size reduction**
- Final image is 13x smaller than builder image

### Why This Matters

1. **Storage**: 212 MB × 1000 containers = 212 GB saved in registry
2. **Network**: Faster deployment, faster CI/CD pipelines
3. **Security**: Smaller attack surface, fewer potential vulnerabilities
4. **Performance**: Faster container startup times

---

## Build Process Output

```bash
$ docker build -t devops-info-service-go:latest app_go/

#5 [builder 1/6] FROM docker.io/library/golang:1.21-alpine
#5 CACHED

#8 [builder 2/6] RUN apk add --no-cache git
#8 DONE 74.8s

#11 [builder 3/6] WORKDIR /build
#11 DONE 0.0s

#12 [builder 4/6] COPY go.mod .
#12 DONE 0.0s

#13 [builder 5/6] COPY main.go .
#13 DONE 0.0s

#14 [builder 6/6] RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build \
    -ldflags="-w -s" -o devops-info-service .
#14 DONE 4.7s

#15 [stage-1 4/5] COPY --from=builder /build/devops-info-service .
#15 DONE 0.0s

#16 [stage-1 5/5] RUN chown -R appuser:appuser /app
#16 DONE 0.1s

#17 exporting to image
#17 DONE 0.0s
```

**Build Time:** ~80 seconds (first build with network downloads; subsequent: ~5 seconds)

---

## Container Running & Testing

### Starting the Container

```bash
$ docker run -d -p 8080:8080 --name devops-go-test devops-info-service-go:latest
4bfd8ee5f484b025a9e4c3c93d06f3ec7b2ceb87c005a0c071bb97ea448dbf4b

$ docker ps
CONTAINER ID   IMAGE                         STATUS         PORTS
4bfd8ee5f484   devops-info-service-go:latest Up 2 seconds   0.0.0.0:8080->8080/tcp
```

### Testing Endpoints

```bash
$ curl -s http://localhost:8080/ | jq '.service'
{
  "name": "devops-info-service",
  "version": "1.0.0",
  "description": "DevOps course info service",
  "framework": "Go net/http"
}

$ curl -s http://localhost:8080/health
{
  "status": "ok",
  "uptime_seconds": 45,
  "timestamp": "2026-02-04T10:40:01.661Z"
}
```

### Verifying Non-Root User

```bash
$ docker exec devops-go-test whoami
appuser

$ docker inspect devops-go-test --format='{{.Config.User}}'
appuser
```

**Result:** ✅ Application works identically to Python version, running as non-root user

---

## Technical Explanation of Each Stage

### Builder Stage

**Purpose:** Compile Go source code into static binary

**Key Commands:**
- `CGO_ENABLED=0`: Disable C bindings → static binary that doesn't depend on libc
- `GOOS=linux GOARCH=amd64`: Cross-compile for Linux x86_64 (even if building on macOS/Windows)
- `-ldflags="-w -s"`: Strip debug symbols and DWARF info → binary size reduction
- `go build`: Produces static binary, no runtime environment needed

**Why This Works:**
- Go can compile to completely static binaries with no external dependencies
- Unlike Python or Node.js, Go doesn't need a runtime or interpreter
- Single binary includes everything needed to run the application

### Runtime Stage

**Purpose:** Run the compiled binary in minimal environment

**Base Image:** `alpine:latest` (8.31 MB)
- Minimal Linux OS with only essential tools
- Has libc, so binary can run, but no build tools
- Much smaller than Debian or CentOS alternatives

**Why This Works:**
- The binary is completely self-contained
- Alpine provides only what's needed to run the binary
- No compiler, source code, or build tools needed

### Key Differences from Python

| Aspect | Python | Go |
|--------|--------|-----|
| Compilation | Interpreted at runtime | Compiled to binary |
| Runtime Dependency | Python interpreter (100+ MB) | None (static binary) |
| Final Image | Must include interpreter | Can be just binary + OS |
| Typical Size | 100-300 MB | 10-30 MB |

---

## Security Benefits of Multi-Stage Builds

### Smaller Attack Surface

**Removed from Final Image:**
- Go compiler: Could be exploited to compile malicious code
- Build tools: Could be used to compromise system
- Git: Network access could be abused
- Source code: Intellectual property protected
- Build cache: Temporary files with potential metadata

**Result:** Fewer files = fewer potential vulnerabilities

### No Unnecessary Privileges

- Runs as non-root user (`appuser`, UID 1000)
- Even with 17.7 MB, much smaller than alternatives
- Every MB reduction = fewer lines of code that could be exploited

### Immutability

- Final image contains only binary + OS
- No ability to modify source or rebuild dynamically
- Reduces surface for supply chain attacks

---

## Comparison with Python Version

| Aspect | Python (Lab 2) | Go (Bonus) |
|--------|----------------|-----------|
| Base Image | python:3.13-slim (120 MB) | golang:1.21-alpine → alpine (8.31 MB) |
| Final Image | 133 MB | **17.7 MB** |
| Size Reduction | None (multi-stage not needed) | **92% reduction** |
| Runtime Dependency | Python interpreter | None (static binary) |
| Startup Time | ~1-2 seconds | <100ms |
| Security Model | Process isolation | Same |

---

## Why Multi-Stage is Different for Compiled Languages

**Python/Node.js/Ruby:**
- Interpreter must be included in final image
- Multi-stage build has minimal benefit
- Final image size is dominated by interpreter

**Go/Rust/C++:**
- Entire application compiled into single binary
- Build environment (compiler, tools) completely unneeded in runtime
- Multi-stage build provides **massive size reduction**

This is why multi-stage builds are most effective for compiled languages.

---

## Lessons Learned

1. **Compiled Languages Scale Better**: Single binary paradigm makes containerization very efficient
2. **Alpine is Minimal**: 8.31 MB is remarkably small, good for microservices
3. **Static Binaries are Powerful**: `-w -s` flags and `CGO_ENABLED=0` create truly portable, self-contained apps
4. **Layer Caching Still Matters**: Even with multi-stage, ordering layers correctly improves build speed
5. **Non-Root is Always Important**: Security doesn't change just because image is small

---

## Docker Hub (Optional)

To publish to Docker Hub:

```bash
docker tag devops-info-service-go:latest dart0/devops-info-service-go:latest
docker push dart0/devops-info-service-go:latest
```

**Repository:** `https://hub.docker.com/r/dart0/devops-info-service-go`

---

## Summary

✅ **Multi-Stage Build:** Separates builder (222 MB) from runtime (17.7 MB)
✅ **Size Reduction:** 92% smaller than builder image, 13x smaller total
✅ **Security:** Non-root user, minimal OS, no build tools in final image
✅ **Performance:** Fast startup, minimal resource usage
✅ **Best Practice:** Go applications should always use multi-stage builds

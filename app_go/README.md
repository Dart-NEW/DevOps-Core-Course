# DevOps Info Service — Go Implementation

Compiled Go implementation of the DevOps Info Service.

## Prerequisites

Go 1.21+

## Building

```bash
go build -o devops-info-service main.go
```

## Running

```bash
./devops-info-service
# With custom config:
PORT=5000 ./devops-info-service
```

## Endpoints

- `GET /` - Service information (all fields: service, system, runtime, request, endpoints)
- `GET /health` - Health check

## Configuration

| Variable | Default |
|----------|---------|
| `HOST` | `0.0.0.0` |
| `PORT` | `8080` |
| `DEBUG` | `false` |

## Binary Size

- Go: ~7.5 MB (single executable)
- Python: ~150+ MB (with venv)

## Advantages of Go for DevOps

1. **Single Binary**: Compiles to a standalone executable
2. **Fast Startup**: Microsecond startup time vs Python seconds
3. **Low Memory**: ~5-10 MB RAM vs Python 50+ MB
4. **Excellent for Containers**: Perfect fit for minimal Docker images
5. **Built-in HTTP**: Standard library `net/http` is production-ready
6. **Cross-compilation**: Build for any OS/architecture easily
7. **Standard Tools**: go fmt, go vet, go test built-in

## Development

Format code with Go standard:

```bash
go fmt ./...
go vet ./...
```

Run the application directly:

```bash
go run main.go
```

## Production Deployment

Build a minimal Docker image:

```dockerfile
FROM golang:1.21-alpine AS builder
WORKDIR /app
COPY . .
RUN go build -o devops-info-service main.go

FROM alpine:latest
COPY --from=builder /app/devops-info-service /app/
EXPOSE 8080
CMD ["/app/devops-info-service"]
```

Build and run:

```bash
docker build -t devops-info-service:latest .
docker run -p 8080:8080 devops-info-service:latest
```

## Resources

- [Go Standard Library](https://golang.org/pkg/)
- [net/http Package](https://pkg.go.dev/net/http)
- [Go Effective Go](https://golang.org/doc/effective_go)
- [Go Module Documentation](https://go.dev/blog/using-go-modules)

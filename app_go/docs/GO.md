# Why Go? — Language Justification

## Summary

Go chosen for:
- **Single binary** (~7.5 MB vs. Python 150+ MB)
- **Fast startup** (~1ms vs. Python 100ms)
- **Standard library HTTP** (no framework needed)
- **DevOps standard** (Docker, Kubernetes, Terraform written in Go)

## Comparison

| Feature | Go | Python |
|---------|----|----|
| Binary size | 7-10 MB | Requires 150+ MB interpreter |
| Startup | ~1ms | ~100ms |
| Memory | 5-10 MB | 50-100 MB |
| Build | `go build` | venv + pip install |
| Docker image | 30 MB | 300+ MB |
| HTTP | std library | Flask/FastAPI required |

## Why Go for DevOps?

1. **Container-native**: Powers Docker, Kubernetes
2. **Self-contained**: Single binary, zero dependencies
3. **Performance**: Goroutines for concurrency
4. **Cross-compilation**: Easy `GOOS=linux GOARCH=amd64 go build`
5. **Production-ready**: Standard library sufficient for production

## Deployment

Go binary ships directly to production:
```bash
go build -o app main.go  # Creates 7 MB executable
./app                    # Runs immediately
```

Python requires interpreter + all dependencies on target system.

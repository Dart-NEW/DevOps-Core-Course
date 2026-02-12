# Multi-stage build for Go application
# Stage 1: Builder
FROM golang:1.21-alpine AS builder

# Install build dependencies
RUN apk add --no-cache git

# Set working directory
WORKDIR /build

# Copy go mod files
COPY go.mod .

# Copy source code
COPY main.go .

# Build the binary statically (no runtime dependencies needed)
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build \
    -ldflags="-w -s" \
    -o devops-info-service .

# Stage 2: Runtime (minimal)
FROM alpine:latest

# Create non-root user
RUN addgroup -g 1000 appuser && \
    adduser -D -u 1000 -G appuser appuser

# Set working directory
WORKDIR /app

# Copy only the compiled binary from builder
COPY --from=builder /build/devops-info-service .

# Set ownership to appuser
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD nc -z localhost 5000 || exit 1

# Start application
CMD ["./devops-info-service"]

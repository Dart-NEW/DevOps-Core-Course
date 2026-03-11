package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net"
	"net/http"
	"os"
	"runtime"
	"strconv"
	"strings"
	"time"
)

var startTime = time.Now()

type responseRecorder struct {
	http.ResponseWriter
	statusCode int
}

func (recorder *responseRecorder) WriteHeader(statusCode int) {
	recorder.statusCode = statusCode
	recorder.ResponseWriter.WriteHeader(statusCode)
}

func logEvent(level string, message string, fields map[string]interface{}) {
	payload := map[string]interface{}{
		"timestamp": time.Now().UTC().Format(time.RFC3339Nano),
		"level":     level,
		"message":   message,
	}

	for key, value := range fields {
		payload[key] = value
	}

	encoded, err := json.Marshal(payload)
	if err != nil {
		log.Printf("{\"timestamp\":%q,\"level\":\"ERROR\",\"message\":\"log_encoding_failed\"}", time.Now().UTC().Format(time.RFC3339Nano))
		return
	}

	log.Println(string(encoded))
}

// Service metadata
type Service struct {
	Name        string `json:"name"`
	Version     string `json:"version"`
	Description string `json:"description"`
	Framework   string `json:"framework"`
}

// System information
type System struct {
	Hostname        string `json:"hostname"`
	Platform        string `json:"platform"`
	PlatformVersion string `json:"platform_version"`
	Architecture    string `json:"architecture"`
	CPUCount        int    `json:"cpu_count"`
	PythonVersion   string `json:"python_version"`
}

// Runtime information
type Runtime struct {
	UptimeSeconds int    `json:"uptime_seconds"`
	UptimeHuman   string `json:"uptime_human"`
	CurrentTime   string `json:"current_time"`
	Timezone      string `json:"timezone"`
}

// Request information
type RequestInfo struct {
	ClientIP  string `json:"client_ip"`
	UserAgent string `json:"user_agent"`
	Method    string `json:"method"`
	Path      string `json:"path"`
}

// Endpoint information
type Endpoint struct {
	Path        string `json:"path"`
	Method      string `json:"method"`
	Description string `json:"description"`
}

// Main response
type MainResponse struct {
	Service   Service     `json:"service"`
	System    System      `json:"system"`
	Runtime   Runtime     `json:"runtime"`
	Request   RequestInfo `json:"request"`
	Endpoints []Endpoint  `json:"endpoints"`
}

// Health response
type HealthResponse struct {
	Status        string `json:"status"`
	Timestamp     string `json:"timestamp"`
	UptimeSeconds int    `json:"uptime_seconds"`
}

// Error response
type ErrorResponse struct {
	Error   string `json:"error"`
	Message string `json:"message"`
	Path    string `json:"path,omitempty"`
}

// getSystemInfo collects system information
func getSystemInfo() System {
	hostname, _ := os.Hostname()

	return System{
		Hostname:        hostname,
		Platform:        runtime.GOOS,
		PlatformVersion: getPlatformVersion(),
		Architecture:    runtime.GOARCH,
		CPUCount:        runtime.NumCPU(),
		PythonVersion:   fmt.Sprintf("3.12.3 (Go equivalent: %s)", runtime.Version()),
	}
}

// getPlatformVersion returns OS version information
func getPlatformVersion() string {
	switch runtime.GOOS {
	case "linux":
		return "Linux"
	case "darwin":
		return "macOS"
	case "windows":
		return "Windows"
	default:
		return runtime.GOOS
	}
}

// getUptimeHuman converts seconds to human-readable format
func getUptimeHuman(seconds int) string {
	hours := seconds / 3600
	minutes := (seconds % 3600) / 60

	return fmt.Sprintf("%d hour%s, %d minute%s",
		hours, pluralize(hours),
		minutes, pluralize(minutes))
}

// pluralize returns appropriate suffix for plural forms
func pluralize(count int) string {
	if count == 1 {
		return ""
	}

	return "s"
}

// getRuntimeInfo collects runtime information
func getRuntimeInfo() Runtime {
	uptime := int(time.Since(startTime).Seconds())
	now := time.Now().UTC()

	return Runtime{
		UptimeSeconds: uptime,
		UptimeHuman:   getUptimeHuman(uptime),
		CurrentTime:   now.Format("2006-01-02T15:04:05.000Z"),
		Timezone:      "UTC",
	}
}

// getClientIP extracts client IP from request
func getClientIP(r *http.Request) string {
	ip := r.Header.Get("X-Forwarded-For")
	if ip != "" {
		return strings.Split(ip, ",")[0]
	}

	if ip := r.Header.Get("X-Real-IP"); ip != "" {
		return ip
	}

	ip, _, _ = net.SplitHostPort(r.RemoteAddr)

	return ip
}

// getRequestInfo collects request information
func getRequestInfo(r *http.Request) RequestInfo {
	return RequestInfo{
		ClientIP:  getClientIP(r),
		UserAgent: r.Header.Get("User-Agent"),
		Method:    r.Method,
		Path:      r.RequestURI,
	}
}

// getEndpoints returns list of available endpoints
func getEndpoints() []Endpoint {
	return []Endpoint{
		{
			Path:        "/",
			Method:      "GET",
			Description: "Service information",
		},
		{
			Path:        "/health",
			Method:      "GET",
			Description: "Health check",
		},
	}
}

// jsonResponse writes JSON response with proper content type
func jsonResponse(w http.ResponseWriter, data interface{}, statusCode int) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(statusCode)

	encoder := json.NewEncoder(w)
	encoder.SetEscapeHTML(false)
	encoder.SetIndent("", "  ")

	if err := encoder.Encode(data); err != nil {
		logEvent("ERROR", "json_encoding_failed", map[string]interface{}{
			"event": "json_encoding_failed",
			"error": err.Error(),
		})
	}
}

// mainHandler serves the main endpoint
func mainHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		jsonResponse(w, ErrorResponse{
			Error:   "Method Not Allowed",
			Message: "Only GET method is supported",
		}, http.StatusMethodNotAllowed)

		return
	}

	response := MainResponse{
		Service: Service{
			Name:        "devops-info-service",
			Version:     "1.0.0",
			Description: "DevOps course info service",
			Framework:   "Go net/http",
		},
		System:    getSystemInfo(),
		Runtime:   getRuntimeInfo(),
		Request:   getRequestInfo(r),
		Endpoints: getEndpoints(),
	}

	jsonResponse(w, response, http.StatusOK)
}

// healthHandler serves the health check endpoint
func healthHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		jsonResponse(w, ErrorResponse{
			Error:   "Method Not Allowed",
			Message: "Only GET method is supported",
		}, http.StatusMethodNotAllowed)

		return
	}

	uptime := int(time.Since(startTime).Seconds())
	response := HealthResponse{
		Status:        "healthy",
		Timestamp:     time.Now().UTC().Format("2006-01-02T15:04:05.000Z"),
		UptimeSeconds: uptime,
	}

	jsonResponse(w, response, http.StatusOK)
}

// notFoundHandler serves 404 responses
func notFoundHandler(w http.ResponseWriter, r *http.Request) {
	jsonResponse(w, ErrorResponse{
		Error:   "Not Found",
		Message: "Endpoint does not exist",
		Path:    r.RequestURI,
	}, http.StatusNotFound)
}

// loggingMiddleware logs incoming requests
func loggingMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		logEvent("INFO", "request_started", map[string]interface{}{
			"event":     "request_started",
			"method":    r.Method,
			"path":      r.RequestURI,
			"client_ip": getClientIP(r),
		})

		recorder := &responseRecorder{ResponseWriter: w, statusCode: http.StatusOK}
		next.ServeHTTP(recorder, r)

		logEvent("INFO", "request_completed", map[string]interface{}{
			"event":       "request_completed",
			"method":      r.Method,
			"path":        r.RequestURI,
			"status_code": recorder.statusCode,
			"client_ip":   getClientIP(r),
		})
	})
}

func main() {
	// Get configuration from environment variables
	host := os.Getenv("HOST")
	if host == "" {
		host = "0.0.0.0"
	}

	portStr := os.Getenv("PORT")
	port := 8080

	if portStr != "" {
		if p, err := strconv.Atoi(portStr); err == nil {
			port = p
		}
	}

	debugStr := os.Getenv("DEBUG")
	debug := strings.ToLower(debugStr) == "true"

	if debug {
		logEvent("DEBUG", "debug_mode_enabled", map[string]interface{}{
			"event": "debug_mode_enabled",
		})
	}

	// Custom 404 handler for undefined routes
	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		switch r.URL.Path {
		case "/":
			mainHandler(w, r)
		case "/health":
			healthHandler(w, r)
		default:
			notFoundHandler(w, r)
		}
	})

	address := fmt.Sprintf("%s:%d", host, port)
	logEvent("INFO", "service_starting", map[string]interface{}{
		"event":   "startup",
		"address": address,
	})
	logEvent("INFO", "service_endpoints", map[string]interface{}{
		"event":      "configuration",
		"root_url":   fmt.Sprintf("http://%s/", address),
		"health_url": fmt.Sprintf("http://%s/health", address),
	})

	if err := http.ListenAndServe(address, loggingMiddleware(http.DefaultServeMux)); err != nil {
		logEvent("ERROR", "server_error", map[string]interface{}{
			"event": "server_error",
			"error": err.Error(),
		})
		log.Fatalf("Server error: %v", err)
	}
}

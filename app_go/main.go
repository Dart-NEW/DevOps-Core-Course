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
	encoder.Encode(data)
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
		log.Printf("%s %s %s", r.Method, r.RequestURI, r.RemoteAddr)
		next.ServeHTTP(w, r)
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
		log.Println("DEBUG mode enabled")
	}

	// Custom 404 handler for undefined routes
	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/" {
			mainHandler(w, r)
		} else if r.URL.Path == "/health" {
			healthHandler(w, r)
		} else {
			notFoundHandler(w, r)
		}
	})

	address := fmt.Sprintf("%s:%d", host, port)
	log.Printf("Starting DevOps Info Service on %s", address)
	log.Printf("Available endpoints:")
	log.Printf("  GET http://%s/", address)
	log.Printf("  GET http://%s/health", address)

	if err := http.ListenAndServe(address, loggingMiddleware(http.DefaultServeMux)); err != nil {
		log.Fatalf("Server error: %v", err)
	}
}

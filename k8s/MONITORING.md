# Kubernetes Monitoring and Init Containers

## 1. Stack Components

### Prometheus Operator
Controls the monitoring CRDs (`ServiceMonitor`, `Prometheus`, `Alertmanager`) and reconciles desired state into running workloads.

### Prometheus
Collects and stores time-series metrics from Kubernetes components and application targets.

### Alertmanager
Receives firing alerts from Prometheus, groups them, deduplicates them, and routes notifications.

### Grafana
Visualizes metrics from Prometheus with dashboards for cluster, node, pod, and workload-level observability.

### kube-state-metrics
Exports Kubernetes object state metrics (Deployments, StatefulSets, Pods, PVCs, etc.) from the API server.

### node-exporter
Exports host-level metrics from cluster nodes (CPU, memory, filesystem, network, load).

---

## 2. Installation Evidence

### Helm Installation
```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace
```

### Monitoring Resources
```bash
kubectl get po,svc -n monitoring
```

Evidence file:
- `k8s/screenshots/lab16/01-monitoring-install.txt`

Key result: all major components are `Running` in namespace `monitoring`.

---

## 3. Dashboard Answers (6 Questions)

Grafana dashboards were validated through the same Prometheus datasource queries used by those dashboards.

Evidence file:
- `k8s/screenshots/lab16/04-prometheus-answers.txt`

### Q1. Pod Resources (StatefulSet CPU/Memory)
- CPU:
  - `lab16-app-devops-info-service-0 = 0.0037459868850271616`
  - `lab16-app-devops-info-service-1 = 0.0029387161827956984`
- Memory (MiB):
  - `lab16-app-devops-info-service-0 = 29.0703125`
  - `lab16-app-devops-info-service-1 = 29.28125`

### Q2. Namespace Analysis (default namespace CPU)
- Most CPU pod: `lab16-app-devops-info-service-0 = 0.003746451325940345`
- Least CPU pod: `lab10-go-devops-info-service-go-5b99ffd484-rxxp4 = 0.000241783676974745`

### Q3. Node Metrics
- Memory usage: `68.31392675165094%`
- Memory used: `10735.05859375 MiB`
- CPU cores: `16`

### Q4. Kubelet Metrics
- Running pods: `49`
- Running containers: `93`

### Q5. Network Traffic (default namespace)
- Receive (bytes/s):
  - `lab16-app-devops-info-service-0 = 244.2192099186202`
  - `lab16-app-devops-info-service-1 = 91.02858051884483`
- Transmit (bytes/s):
  - `lab16-app-devops-info-service-0 = 785.2206931897166`
  - `lab16-app-devops-info-service-1 = 74.92145351907669`

### Q6. Active Alerts
- Prometheus firing alerts: `3`
- Alertmanager API active alerts: `3`

Evidence file:
- `k8s/screenshots/lab16/05-alerts-and-scrape.txt`

---

## 4. Init Containers

## 4.1 Implemented Patterns

Two init patterns are implemented in the chart:

1. **Download file via wget**
- init container `init-download` downloads `https://example.com` to `/work-dir/index.html`
- shared `emptyDir` volume is mounted into main container at `/init-data`

2. **Wait-for-service pattern**
- init container `wait-for-service` loops on DNS resolution of
  `monitoring-grafana.monitoring.svc.cluster.local`
- main container starts only after dependency is resolvable

### Template locations
- `k8s/devops-info-service/templates/deployment.yaml`
- `k8s/devops-info-service/templates/rollout.yaml`
- `k8s/devops-info-service/templates/statefulset.yaml`

### Values used for lab
- `k8s/devops-info-service/values-monitoring.yaml`

### Runtime Proof
Evidence file:
- `k8s/screenshots/lab16/03-init-containers.txt`

Verified:
- `init-download` log shows successful file download.
- Init statuses:
  - `init-download: Completed, exit=0`
  - `wait-for-service: Completed, exit=0`
- Main container can read shared file:
  - `cat /init-data/index.html` returns downloaded content.

---

## 5. Bonus — Custom Metrics and ServiceMonitor

## 5.1 /metrics Endpoint
The application exposes metrics at `/metrics` (Flask + `prometheus_client`).

Source:
- `app_python/app.py`

## 5.2 ServiceMonitor
Added `ServiceMonitor` template:
- `k8s/devops-info-service/templates/servicemonitor.yaml`

Configured via values:
- `monitoring.serviceMonitor.enabled: true`
- `monitoring.serviceMonitor.labels.release: monitoring`
- `monitoring.serviceMonitor.path: /metrics`

## 5.3 Scrape Verification
Application resources and ServiceMonitor:
- `k8s/screenshots/lab16/02-app-resources.txt`

Prometheus scrape evidence (`up` query on app service):
- `k8s/screenshots/lab16/05-alerts-and-scrape.txt`

---

## 6. Commands Used

### Access Grafana
```bash
kubectl port-forward svc/monitoring-grafana -n monitoring 3000:80
```

### Access Alertmanager
```bash
kubectl port-forward svc/monitoring-kube-prometheus-alertmanager -n monitoring 9093:9093
```

### Access Prometheus
```bash
kubectl port-forward svc/monitoring-kube-prometheus-prometheus -n monitoring 9090:9090
```

### Verify app monitoring resources
```bash
kubectl get po,sts,svc,pvc,servicemonitor -n default -l app.kubernetes.io/instance=lab16-app
```

---

## 7. Result

Lab 16 requirements are implemented:
- Kube-Prometheus stack installed and running.
- Dashboard questions answered with live Prometheus metrics.
- Init container download and wait-for-service patterns implemented and verified.
- Documentation and evidence collected.
- Bonus task implemented: `/metrics` exposed + `ServiceMonitor` configured and scraped.

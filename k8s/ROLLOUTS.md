# Argo Rollouts — Progressive Delivery Implementation

## Overview

This document details the implementation of progressive delivery strategies using Argo Rollouts, providing safe, automated release management with traffic shifting and automatic rollback capabilities.

---

## 1. Argo Rollouts Fundamentals

### 1.1 Installation Verification

**Argo Rollouts Controller:** Installed in the `argo-rollouts` namespace and manages Rollout custom resources.

```bash
# Install controller
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml

# Verify controller
kubectl get pods -n argo-rollouts
kubectl get crd | grep rollout
```

**kubectl Plugin:** Installed for CLI management of rollouts.

```bash
# Linux installation
curl -LO https://github.com/argoproj/argo-rollouts/releases/latest/download/kubectl-argo-rollouts-linux-amd64
chmod +x kubectl-argo-rollouts-linux-amd64
sudo mv kubectl-argo-rollouts-linux-amd64 /usr/local/bin/kubectl-argo-rollouts

# Verify
kubectl argo rollouts version
```

### 1.2 Dashboard Installation

**Argo Rollouts Dashboard:** Provides visualization of rollout progress, traffic shifting, and analysis metrics.

```bash
# Install dashboard
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/dashboard-install.yaml

# Verify
kubectl get pods -n argo-rollouts | grep dashboard

# Access (port-forward)
kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100

# Open browser: http://localhost:3100
```

### 1.3 Rollout vs Deployment: Key Differences

| Aspect | Deployment | Rollout |
|--------|-----------|---------|
| **Strategy** | RollingUpdate, Recreate only | Canary, BlueGreen, SMI, Istio |
| **Traffic Shifting** | No native support | Fine-grained control (percentages) |
| **Pauses & Analysis** | Not supported | Automated analysis & manual pauses |
| **Rollback** | Revision-based | Instant, traffic-based |
| **CRD** | Built-in resource | `argoproj.io/v1alpha1` |

**Rollout CRD Extends the Deployment spec with:**
- `strategy.canary` / `strategy.blueGreen` — Progressive delivery configuration
- `strategy.*.steps` — Traffic shifting steps with pauses and analysis
- `analysis` — Metrics-based promotion/rollback

---

## 2. Canary Deployment Strategy

### 2.1 Configuration

The canary strategy gradually shifts traffic to the new version, allowing validation before full rollout.

**Configuration File:** `values-canary.yaml`

```yaml
rollout:
  enabled: true
  strategy: canary
  revisionHistoryLimit: 3
  canary:
    pauseDuration: 30s
  analysis:
    enabled: true
    interval: 5s
    count: 2
    failureLimit: 1
    successCondition: result == "healthy"
```

**Rollout Template:** `templates/rollout.yaml`

```yaml
strategy:
  canary:
    steps:
      - setWeight: 20      # 20% traffic to canary
      - pause: {}          # Manual promotion required
      - setWeight: 40      # 40% traffic
      - pause:
          duration: 30s    # Auto-promote after 30s
      - setWeight: 60      # 60% traffic
      - pause:
          duration: 30s
      - setWeight: 80      # 80% traffic
      - pause:
          duration: 30s
      - setWeight: 100     # 100% traffic (fully promoted)
```

### 2.2 Testing Canary Deployment

**Step 1: Deploy canary rollout**

```bash
helm install devops-info-service k8s/devops-info-service \
  -f k8s/devops-info-service/values-canary.yaml \
  -n default
```

**Step 2: Verify rollout created**

```bash
# Check Rollout resource
kubectl get rollout
kubectl describe rollout devops-info-service

# Watch rollout status
kubectl argo rollouts get rollout devops-info-service -w
```

**Step 3: Verify stable version running**

```bash
# Service is running
kubectl get svc devops-info-service
kubectl port-forward svc/devops-info-service 8080:80

# Access: http://localhost:8080
# Verify version/environment: canary
```

**Step 4: Trigger rollout (update image tag)**

```bash
# Update image tag to trigger new rollout
kubectl set image rollout/devops-info-service \
  devops-info-service=devops-info-service-python:v2.0 \
  --record

# Watch Argo Rollouts dashboard (3100)
# Observe: 0% → 20% traffic shift to new version
```

**Step 5: Manual promotion**

```bash
# At 20%, promotion is paused and requires manual approval
kubectl argo rollouts promote devops-info-service

# Traffic shifts: 20% → 40%
# Automatic promotions continue every 30s
```

**Step 6: Observe traffic progression**

```bash
# Monitor in dashboard or CLI
kubectl argo rollouts get rollout devops-info-service

# 40% → 60% → 80% → 100% (automatic)
# Traffic gradually validates new version
```

**Step 7: Test rollback during canary**

```bash
# Abort rollout at any point
kubectl argo rollouts abort devops-info-service

# Traffic shifts back to stable version
# Canary pods are terminated
```

### 2.3 Canary Pros and Cons

**Advantages:**
- Gradual validation of new version
- Early detection of issues with limited blast radius
- Can rollback quickly with minimal impact
- Resource-efficient (shared pods)

**Disadvantages:**
- Requires monitoring and manual intervention
- Slower full deployment compared to blue-green
- Complex traffic splitting logic

---

## 3. Blue-Green Deployment Strategy

### 3.1 Configuration

The blue-green strategy maintains two parallel environments: one active (blue) serving production, one new (green) for testing before instant cutover.

**Configuration File:** `values-bluegreen.yaml`

```yaml
rollout:
  enabled: true
  strategy: blueGreen
  revisionHistoryLimit: 3
  blueGreen:
    autoPromotionEnabled: false    # Manual promotion
    scaleDownDelaySeconds: 30      # Keep old version running 30s before scale down
    previewService:
      type: NodePort
      nodePort: 30088
```

**Rollout Template Strategy:**

```yaml
strategy:
  blueGreen:
    activeService: devops-info-service           # Production service
    previewService: devops-info-service-preview  # Testing service
    autoPromotionEnabled: false                  # Manual promotion required
    scaleDownDelaySeconds: 30                    # Grace period
```

**Preview Service:** `templates/service-preview.yaml`

```yaml
apiVersion: v1
kind: Service
metadata:
  name: devops-info-service-preview
spec:
  type: NodePort
  selector:
    app: devops-info-service
  ports:
    - port: 80
      targetPort: http
      nodePort: 30088
```

### 3.2 Testing Blue-Green Deployment

**Step 1: Deploy blue-green rollout**

```bash
helm install devops-info-service k8s/devops-info-service \
  -f k8s/devops-info-service/values-bluegreen.yaml \
  -n default
```

**Step 2: Access active (blue) service**

```bash
# Blue service (production)
kubectl port-forward svc/devops-info-service 8080:80

# Access: http://localhost:8080
# All traffic goes to blue (v1.0)
```

**Step 3: Observe rollout status**

```bash
# Initial state: all traffic on blue
kubectl argo rollouts get rollout devops-info-service

# Replicas: 3 active (blue), 0 preview
```

**Step 4: Trigger new version deployment**

```bash
# Update image tag
kubectl set image rollout/devops-info-service \
  devops-info-service=devops-info-service-python:v2.0 \
  --record
```

**Step 5: Test preview (green) environment**

```bash
# Green service (preview/testing)
kubectl port-forward svc/devops-info-service-preview 8081:80

# Access: http://localhost:8081
# New version running here, not serving production traffic
# Test thoroughly before promotion
```

**Step 6: Verify both versions side-by-side**

```bash
# Terminal 1: Blue (active)
kubectl port-forward svc/devops-info-service 8080:80

# Terminal 2: Green (preview)
kubectl port-forward svc/devops-info-service-preview 8081:80

# Compare responses:
# http://localhost:8080 (v1.0)
# http://localhost:8081 (v2.0)
```

**Step 7: Manual promotion to active**

```bash
# Promote preview (green) to active (blue)
kubectl argo rollouts promote devops-info-service

# Instant traffic switch:
# Blue stops receiving traffic
# Green becomes active service
# Blue pods scale down after 30s (scaleDownDelaySeconds)
```

**Step 8: Verify instant cutover**

```bash
# Check rollout state
kubectl argo rollouts get rollout devops-info-service

# Status: Healthy (v2.0 is now active)
# Replicas: 3 active (v2.0), 0 preview

# Traffic on active service now goes to new version:
# curl http://active-svc → v2.0 responses
```

**Step 9: Test instant rollback (post-promotion)**

```bash
# Trigger rollback after promotion
kubectl argo rollouts abort devops-info-service

# OR manually correct by updating image back to v1.0:
kubectl set image rollout/devops-info-service \
  devops-info-service=devops-info-service-python:v1.0 \
  --record

# Instant traffic switch back to blue (v1.0)
# No gradual transition
```

### 3.3 Blue-Green Pros and Cons

**Advantages:**
- Instant cutover/rollback (all-or-nothing)
- Complete isolation between versions
- Easy A/B testing with preview environment
- No traffic mixing during deployment

**Disadvantages:**
- Requires 2x resources during deployment
- Resource waste during grace period
- Slower to detect issues (all traffic switches at once)
- No gradual validation

---

## 4. Strategy Comparison

| Aspect | Canary | Blue-Green |
|--------|--------|-----------|
| **Rollout Speed** | Gradual (~minutes) | Instant (seconds) |
| **Resource Usage** | Efficient (shared) | 2x during deployment |
| **Risk Exposure** | Low (% of users) | Medium (all-at-once) |
| **Issue Detection** | Early (continuous monitoring) | Late (after full switch) |
| **Rollback Speed** | Fast | Very fast |
| **Test Environment** | Limited (% traffic) | Full (separate service) |
| **A/B Testing** | Possible | Excellent |
| **Monitoring Required** | Continuous | Manual comparison |

### When to Use Each Strategy

**Use Canary When:**
- You need data-driven rollout decisions
- Issues need gradual user impact minimization
- You have strong monitoring/metrics
- You can tolerate slower deployments
- Example: Feature rollouts, algorithm changes

**Use Blue-Green When:**
- You need instant rollback capability
- You want complete environment isolation
- Issues are binary (works/doesn't work)
- You can afford 2x resources temporarily
- Example: Database schema updates, critical services

**Recommendation for This Course:**
- **Canary**: Best for application feature rollouts
- **Blue-Green**: Best for infrastructure and platform updates

---

## 5. Analysis-Driven Promotion (Bonus)

### 5.1 AnalysisTemplate Configuration

The `analysis-template.yaml` enables automatic promotion/rollback based on metrics.

**Configuration:**

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: devops-info-service-health
spec:
  metrics:
    - name: health-webcheck
      interval: 5s
      count: 2
      failureLimit: 1
      successCondition: result == "healthy"
      provider:
        web:
          url: http://devops-info-service.default.svc:80/health
          jsonPath: "{$.status}"
```

**Analysis Values (from `values-canary.yaml`):**

```yaml
rollout:
  analysis:
    enabled: true
    interval: 5s         # Check every 5 seconds
    count: 2             # Need 2 successful checks
    failureLimit: 1      # Fail if 1 check fails
    successCondition: result == "healthy"  # Success if status == "healthy"
```

### 5.2 Canary with Analysis Steps

The canary strategy integrates analysis at critical decision points:

```yaml
strategy:
  canary:
    steps:
      - setWeight: 20
      - pause: {}
      - analysis:          # ← Analysis check before proceeding
          templates:
            - templateName: devops-info-service-health
      - setWeight: 40
      - pause: { duration: 30s }
      - setWeight: 100
```

**Behavior:**
1. Deploy 20% canary
2. Manual promotion required
3. Run health analysis on new version
4. If analysis passes → proceed to 40%
5. If analysis fails → auto-rollback

### 5.3 Automatic Rollback Example

```bash
# If application at canary version has health endpoint
# returning unhealthy status, analysis will detect it

# Simulate failure in canary:
kubectl exec -it <canary-pod> -- \
  curl -X POST http://localhost:8080/admin/fail

# After analysis interval:
# Analysis fails → Automatic rollback triggered
# Traffic switches back to stable version
# Event logs visible in dashboard
```

---

## 6. CLI Commands Reference

### Basic Rollout Management

```bash
# Get rollout status
kubectl argo rollouts get rollout <name>
kubectl argo rollouts get rollout <name> -w  # Watch mode

# Get detailed info
kubectl describe rollout <name>
kubectl get rollout <name> -o yaml
```

### Canary Promotion & Abort

```bash
# Manual promotion to next step (canary)
kubectl argo rollouts promote <name>

# Abort current rollout
kubectl argo rollouts abort <name>

# Retry aborted rollout
kubectl argo rollouts retry rollout <name>

# Restart entire rollout (restart all replicas)
kubectl argo rollouts restart <name>
```

### Blue-Green Specific

```bash
# Promote green to blue (active service)
kubectl argo rollouts promote <name>

# Quick status check
kubectl argo rollouts status <name>
```

### Image Update (Triggers New Rollout)

```bash
# Set new image (same pattern as Deployment)
kubectl set image rollout/<name> \
  <container-name>=<new-image>:<tag> \
  --record

# View rollout history
kubectl argo rollouts history <name>

# Rollback to previous version
kubectl argo rollouts undo <name>
```

### Analysis Debugging

```bash
# View analysis results
kubectl get analysisrun <name> -n <namespace>
kubectl describe analysisrun <name>

# View analysis templates
kubectl get analysistemplate
kubectl describe analysistemplate <name>
```

### View Events

```bash
# Kubernetes events
kubectl get events --sort-by='.lastTimestamp'

# Dashboard events
# https://localhost:3100 → Select rollout → Events tab
```

---

## 7. Helm Chart Integration

### Values Files Structure

```
devops-info-service/
├── values.yaml                 # Default (Deployment-based)
├── values-canary.yaml         # Canary rollout configuration
├── values-bluegreen.yaml       # Blue-green rollout configuration
├── values-dev.yaml            # Development environment
├── values-prod.yaml           # Production environment
└── templates/
    ├── deployment.yaml        # Standard Deployment (fallback)
    ├── rollout.yaml          # Argo Rollout (conditional)
    ├── service.yaml          # Active service
    ├── service-preview.yaml  # Preview service (blue-green)
    ├── analysis-template.yaml # Analysis rules (bonus)
    └── ...
```

### Installing Different Strategies

```bash
# Standard Deployment (no progressive delivery)
helm install devops-info-service k8s/devops-info-service

# Canary Rollout
helm install devops-info-service k8s/devops-info-service \
  -f k8s/devops-info-service/values-canary.yaml

# Blue-Green Rollout
helm install devops-info-service k8s/devops-info-service \
  -f k8s/devops-info-service/values-bluegreen.yaml

# Production (with blue-green)
helm install devops-info-service k8s/devops-info-service \
  -f k8s/devops-info-service/values-prod.yaml
```

---

## 8. Common Issues & Troubleshooting

### Issue: "Rollout never completes"

```bash
# Check if all pods are ready
kubectl get pods
kubectl describe pod <pod-name>

# Check service endpoint targets
kubectl get endpoints <service-name>

# View rollout events
kubectl describe rollout <name>
```

### Issue: "Analysis always fails"

```bash
# Verify health endpoint is working
kubectl port-forward svc/<service> 8080:80
curl http://localhost:8080/health

# Check AnalysisTemplate configuration
kubectl get analysistemplate
kubectl describe analysistemplate <name>

# View analysis run logs
kubectl describe analysisrun <name>
```

### Issue: "Cannot access preview service"

```bash
# Verify preview service exists (blue-green only)
kubectl get svc | grep preview

# Verify selector matches pods
kubectl get pods --show-labels
kubectl describe svc <service-preview>

# Verify nodePort is assigned
kubectl get svc <service-preview> -o yaml | grep nodePort
```

### Reset Everything

```bash
# Delete rollout and return to clean state
helm uninstall devops-info-service

# Or scale down without deletion
kubectl scale rollout devops-info-service --replicas=0
```

---

## 9. Summary

Argo Rollouts enables sophisticated progressive delivery strategies:

- **Canary:** Gradual rollout with automatic or manual promotion steps, ideal for feature rollouts
- **Blue-Green:** Instant cutover with preview environment, ideal for critical updates
- **Analysis:** Automatic promotion/rollback based on metrics

The Helm chart is configured to support both strategies via values files, enabling flexible deployment patterns for different scenarios and risk profiles.

---

## References

- [Argo Rollouts Documentation](https://argoproj.github.io/argo-rollouts/)
- [Argo Rollouts Specification](https://argoproj.github.io/argo-rollouts/features/specification/)
- [Analysis & Progressive Delivery](https://argoproj.github.io/argo-rollouts/features/analysis/)
- [Argo Rollouts Kubectl Plugin](https://argoproj.github.io/argo-rollouts/kubectl-plugin/commands/)

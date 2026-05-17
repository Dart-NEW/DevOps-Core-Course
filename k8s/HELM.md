# Lab 10: Helm Package Manager

## Chart Overview

Helm turns the static manifests from Lab 9 into reusable, parameterized application packages.

**Why Helm is useful here:**
- One chart can serve dev and prod through values files instead of copied YAML.
- Releases are versioned, so installs, upgrades, rollbacks, and uninstalls are consistent.
- Hooks let us run validation and smoke-test logic around the release lifecycle.
- Shared helper templates reduce duplication across multiple application charts.

**Implemented chart layout:**

```text
k8s/
├── common-lib/
│   ├── Chart.yaml
│   ├── values.yaml
│   └── templates/
│       └── _helpers.tpl
├── devops-info-service/
│   ├── Chart.yaml
│   ├── values.yaml
│   ├── values-dev.yaml
│   ├── values-prod.yaml
│   └── templates/
│       ├── _helpers.tpl
│       ├── deployment.yaml
│       ├── service.yaml
│       ├── NOTES.txt
│       ├── tests/
│       │   └── test-connection.yaml
│       └── hooks/
│           ├── pre-install-job.yaml
│           └── post-install-job.yaml
└── devops-info-service-go/
    ├── Chart.yaml
    ├── values.yaml
    └── templates/
        ├── _helpers.tpl
        ├── deployment.yaml
        ├── service.yaml
        ├── NOTES.txt
        └── tests/
            └── test-connection.yaml
```

**Key files and purpose:**
- `k8s/devops-info-service/Chart.yaml`: Python app chart metadata and dependency on `common-lib`.
- `k8s/devops-info-service/templates/deployment.yaml`: templated Deployment with resources, security, probes, anti-affinity, and `/tmp` scratch volume.
- `k8s/devops-info-service/templates/service.yaml`: templated Service with configurable type, port, session affinity, and optional nodePort.
- `k8s/devops-info-service/templates/hooks/*.yaml`: Helm lifecycle Jobs for validation and smoke testing.
- `k8s/devops-info-service/values*.yaml`: defaults plus dev/prod overrides.
- `k8s/common-lib/templates/_helpers.tpl`: shared `fullname`, `labels`, and `selectorLabels` helpers.
- `k8s/devops-info-service-go/*`: second application chart used for the bonus task.
- `Chart.lock` and `charts/common-lib-0.1.0.tgz` inside each app chart: vendored dependency artifacts created by `helm dependency update`.

**Values organization strategy:**
- `values.yaml` contains safe defaults and all shared configuration structure.
- `values-dev.yaml` overrides only the fields that differ in development.
- `values-prod.yaml` overrides only the fields that differ in production.
- Nested sections are grouped by concern: `image`, `service`, `resources`, probes, pod security, and `hooks`.

## Helm Fundamentals

**Installed CLI version:**

```bash
$ helm version
version.BuildInfo{Version:"v4.0.0", GitCommit:"99cd1964357c793351be481d55abbe21c6b2f4ec", GitTreeState:"clean", GoVersion:"go1.25.3", KubeClientVersion:"v1.34"}
```

**Repository setup and exploration:**

```bash
$ helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
"prometheus-community" has been added to your repositories

$ helm repo update
...Successfully got an update from the "prometheus-community" chart repository
Update Complete. ⎈Happy Helming!⎈

$ helm search repo prometheus-community/prometheus
NAME                            CHART VERSION  APP VERSION  DESCRIPTION
prometheus-community/prometheus 28.14.1        v3.10.0      Prometheus is a monitoring system and time series database.

$ helm show chart prometheus-community/prometheus
apiVersion: v2
appVersion: v3.10.0
description: Prometheus is a monitoring system and time series database.
name: prometheus
type: application
version: 28.14.1
```

**Core concepts used in this lab:**
- **Chart**: package of Kubernetes templates and defaults.
- **Release**: installed instance of a chart in the cluster.
- **Repository**: source of published charts such as `prometheus-community`.
- **Values**: the configuration layer that makes one chart reusable across environments.

## Configuration Guide

### Main chart values

**Important values in `k8s/devops-info-service/values.yaml`:**
- `replicaCount`: controls Deployment scale.
- `image.repository` and `image.tag`: selects the container image.
- `env`: configures `HOST`, `PORT`, and `DEBUG`.
- `service.type`, `service.port`, `service.nodePort`: controls access method.
- `resources`: CPU and memory requests/limits.
- `livenessProbe`, `readinessProbe`, `startupProbe`: keep health checks configurable.
- `podSecurityContext` and `securityContext`: preserve the non-root runtime and basic hardening.
- `podAntiAffinity`: keeps replicas spread when possible.
- `hooks.*`: configures pre-install validation and post-install smoke testing.

### Environment-specific values

**Development (`values-dev.yaml`):**
- `replicaCount: 1`
- `DEBUG: "true"`
- lighter resources
- `service.type: NodePort`
- fixed `nodePort: 30081`

**Production (`values-prod.yaml`):**
- `replicaCount: 4`
- `DEBUG: "false"`
- higher resource requests and limits
- `service.type: LoadBalancer`
- `nodePort: null` in values, but Kubernetes preserved the already allocated `30081` during the live upgrade from NodePort to LoadBalancer

### Example commands

```bash
# Dev install
helm install lab10-python k8s/devops-info-service -n default \
  -f k8s/devops-info-service/values-dev.yaml

# Upgrade same release to prod
helm upgrade lab10-python k8s/devops-info-service -n default \
  -f k8s/devops-info-service/values-prod.yaml --wait

# Bonus Go chart
helm install lab10-go k8s/devops-info-service-go -n default --wait
```

## Hook Implementation

Two hook Jobs were implemented in the Python chart:

### Pre-install hook

- File: `k8s/devops-info-service/templates/hooks/pre-install-job.yaml`
- Hook type: `pre-install`
- Weight: `-5`
- Delete policy: `before-hook-creation,hook-succeeded`
- Purpose: validate the release before regular resources are created

The Job checks that:
- `replicaCount > 0`
- `service.port > 0`
- the expected image reference is resolved correctly

### Post-install hook

- File: `k8s/devops-info-service/templates/hooks/post-install-job.yaml`
- Hook type: `post-install`
- Weight: `5`
- Delete policy: `before-hook-creation,hook-succeeded`
- Purpose: run a smoke test against `http://<service>:80/health`

The Job:
- polls the Service until it answers successfully
- prints the `/health` response
- sleeps briefly on success so the Job can be inspected before Helm deletes it

### Execution order

1. `pre-install` validation runs first because of weight `-5`
2. chart resources are created
3. `post-install` smoke test runs after install because of weight `5`

### Evidence

**Pre-install Job description:**

```bash
$ kubectl describe job lab10-python-devops-info-service-pre-install -n default
Name:             lab10-python-devops-info-service-pre-install
Annotations:      helm.sh/hook: pre-install
                  helm.sh/hook-delete-policy: before-hook-creation,hook-succeeded
                  helm.sh/hook-weight: -5
Pods Statuses:    1 Active (1 Ready) / 0 Succeeded / 0 Failed
Events:
  Type    Reason            Message
  Normal  SuccessfulCreate  Created pod: lab10-python-devops-info-service-pre-install-gv4gt
```

**Post-install Job description:**

```bash
$ kubectl describe job lab10-python-devops-info-service-post-install -n default
Name:             lab10-python-devops-info-service-post-install
Annotations:      helm.sh/hook: post-install
                  helm.sh/hook-delete-policy: before-hook-creation,hook-succeeded
                  helm.sh/hook-weight: 5
Pods Statuses:    1 Active (1 Ready) / 0 Succeeded / 0 Failed
Events:
  Type    Reason            Message
  Normal  SuccessfulCreate  Created pod: lab10-python-devops-info-service-post-install-mvrnv
```

**Post-install smoke-test logs:**

```bash
$ kubectl logs -n default job/lab10-python-devops-info-service-post-install
Running smoke test against http://lab10-python-devops-info-service:80/health
wget: can't connect to remote host (10.96.158.15): Connection refused
Service not ready yet (1/20)
...
{
  "status": "healthy",
  "timestamp": "2026-03-29T14:00:49.773235+00:00",
  "uptime_seconds": 2
}
Smoke test passed on attempt 5
```

**Deletion policy verification:**

```bash
$ kubectl get jobs -n default
No resources found in default namespace.
```

## Installation Evidence

### Dev install

```bash
$ helm install lab10-python k8s/devops-info-service -n default \
  -f k8s/devops-info-service/values-dev.yaml --debug
NAME: lab10-python
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
```

**Dev release resources:**

```bash
$ kubectl get deployment,service -n default -l app.kubernetes.io/instance=lab10-python -o wide
NAME                                               READY   UP-TO-DATE   AVAILABLE   AGE   CONTAINERS            IMAGES                             SELECTOR
deployment.apps/lab10-python-devops-info-service   1/1     1            1           37s   devops-info-service   devops-info-service-python:lab10   app.kubernetes.io/instance=lab10-python,app.kubernetes.io/name=devops-info-service

NAME                                       TYPE       CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE   SELECTOR
service/lab10-python-devops-info-service   NodePort   10.96.158.15   <none>        80:30081/TCP   37s   app.kubernetes.io/instance=lab10-python,app.kubernetes.io/name=devops-info-service
```

### Prod upgrade

```bash
$ helm upgrade lab10-python k8s/devops-info-service -n default \
  -f k8s/devops-info-service/values-prod.yaml --wait --debug
Release "lab10-python" has been upgraded. Happy Helming!
STATUS: deployed
REVISION: 2
DESCRIPTION: Upgrade complete
```

**Prod release resources:**

```bash
$ kubectl get pods,service,deployment -n default -l app.kubernetes.io/instance=lab10-python -o wide
NAME                                                    READY   STATUS      RESTARTS   AGE
pod/lab10-python-devops-info-service-85b54f84d5-7bm2w   1/1     Running     0          3m28s
pod/lab10-python-devops-info-service-85b54f84d5-kbv74   1/1     Running     0          3m18s
pod/lab10-python-devops-info-service-85b54f84d5-kj6rq   1/1     Running     0          3m7s
pod/lab10-python-devops-info-service-85b54f84d5-scfmx   1/1     Running     0          2m57s

NAME                                       TYPE           CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE
service/lab10-python-devops-info-service   LoadBalancer   10.96.158.15   <pending>     80:30081/TCP   4m33s

NAME                                               READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/lab10-python-devops-info-service   4/4     4            4           4m33s
```

`<pending>` for the external IP is expected in kind because there is no cloud load balancer provider.

### Bonus release

```bash
$ helm install lab10-go k8s/devops-info-service-go -n default --wait --debug
NAME: lab10-go
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
```

```bash
$ kubectl get pods,service,deployment -n default -l app.kubernetes.io/instance=lab10-go -o wide
NAME                                                   READY   STATUS      RESTARTS   AGE
pod/lab10-go-devops-info-service-go-5b99ffd484-njzqt   1/1     Running     0          2m28s
pod/lab10-go-devops-info-service-go-5b99ffd484-rxxp4   1/1     Running     0          2m28s

NAME                                      TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)   AGE
service/lab10-go-devops-info-service-go   ClusterIP   10.96.25.191   <none>        80/TCP    2m28s

NAME                                              READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/lab10-go-devops-info-service-go   2/2     2            2           2m28s
```

### Final Helm release list

```bash
$ helm list -n default
NAME         NAMESPACE  REVISION  STATUS    CHART                        APP VERSION
lab10-go     default    1         deployed  devops-info-service-go-0.1.0 1.0.0
lab10-python default    2         deployed  devops-info-service-0.1.0    1.0.0
```

## Operations

### Install

```bash
helm dependency update k8s/devops-info-service
helm install lab10-python k8s/devops-info-service -n default \
  -f k8s/devops-info-service/values-dev.yaml
```

### Upgrade

```bash
helm upgrade lab10-python k8s/devops-info-service -n default \
  -f k8s/devops-info-service/values-prod.yaml --wait
```

### Rollback

```bash
helm history lab10-python -n default
helm rollback lab10-python 1 -n default
```

### Uninstall

```bash
helm uninstall lab10-python -n default
helm uninstall lab10-go -n default
```

## Testing & Validation

### Lint

```bash
$ helm lint k8s/devops-info-service
==> Linting k8s/devops-info-service
[INFO] Chart.yaml: icon is recommended
1 chart(s) linted, 0 chart(s) failed

$ helm lint k8s/devops-info-service-go
==> Linting k8s/devops-info-service-go
[INFO] Chart.yaml: icon is recommended
1 chart(s) linted, 0 chart(s) failed

$ helm lint k8s/common-lib
==> Linting k8s/common-lib
[INFO] Chart.yaml: icon is recommended
1 chart(s) linted, 0 chart(s) failed
```

### Template rendering

```bash
$ helm template python-dev k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml
# Rendered Service, Deployment, test Pod, and both hook Jobs successfully

$ helm template go-demo k8s/devops-info-service-go
# Rendered Service, Deployment, and test Pod successfully
```

### Dry run

```bash
$ helm install --dry-run --debug lab10-dryrun k8s/devops-info-service -n default \
  -f k8s/devops-info-service/values-dev.yaml
STATUS: pending-install
DESCRIPTION: Dry run complete
```

Helm 4 prints a warning that bare `--dry-run` is deprecated; `--dry-run=client --debug` is the modern equivalent.

### Application accessibility

**Python chart via port-forward:**

```bash
$ kubectl port-forward -n default service/lab10-python-devops-info-service 18080:80

$ curl -s http://127.0.0.1:18080/health
{
  "status": "healthy",
  "timestamp": "2026-03-29T14:03:50.609956+00:00",
  "uptime_seconds": 130
}
```

**Go chart via port-forward:**

```bash
$ kubectl port-forward -n default service/lab10-go-devops-info-service-go 18081:80

$ curl -s http://127.0.0.1:18081/health
{
  "status": "healthy",
  "timestamp": "2026-03-29T14:04:00.643Z",
  "uptime_seconds": 81
}
```

### Helm test

```bash
$ helm test lab10-python -n default --logs
TEST SUITE:     lab10-python-devops-info-service-test-connection
Phase:          Succeeded
POD LOGS: lab10-python-devops-info-service-test-connection
Connecting to lab10-python-devops-info-service:80 (10.96.158.15:80)
'index.html' saved

$ helm test lab10-go -n default --logs
TEST SUITE:     lab10-go-devops-info-service-go-test-connection
Phase:          Succeeded
POD LOGS: lab10-go-devops-info-service-go-test-connection
Connecting to lab10-go-devops-info-service-go:80 (10.96.25.191:80)
'index.html' saved
```

## Bonus: Library Chart

The bonus task is implemented with `k8s/common-lib` as a Helm library chart.

**What was extracted into the library:**
- `common-lib.name`
- `common-lib.fullname`
- `common-lib.chart`
- `common-lib.selectorLabels`
- `common-lib.labels`

**How the application charts use it:**
- `k8s/devops-info-service/Chart.yaml` depends on `file://../common-lib`
- `k8s/devops-info-service-go/Chart.yaml` depends on `file://../common-lib`
- each app chart wraps the shared helpers in its own local `_helpers.tpl` for readable includes

**Benefits of this approach:**
- DRY naming and label logic
- consistent selectors and metadata across both apps
- less duplication when adding more charts later
- easier maintenance because common behavior lives in one place

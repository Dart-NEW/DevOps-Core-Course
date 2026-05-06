# StatefulSet and Persistent Storage

## Overview

This lab converts the application chart from a shared-PVC Deployment model to a StatefulSet model with stable pod identities and per-pod persistent storage.

### Why StatefulSet

Use StatefulSets when each replica needs its own identity or its own persistent data. That includes databases, queues, and any workload that must survive pod recreation without sharing storage between replicas.

### Deployment vs StatefulSet

| Feature | Deployment | StatefulSet |
| --- | --- | --- |
| Pod name | Random suffix | Stable ordinal suffix such as `app-0` |
| Network identity | Ephemeral | Stable DNS name per pod |
| Storage | Shared or external | Per-pod PVC via `volumeClaimTemplates` |
| Scaling | Parallel | Ordered by default |
| Updates | Rolling replacement | Ordered updates, controllable strategy |

### Headless Service

A headless service uses `clusterIP: None`. Kubernetes does not load-balance through it. Instead, it publishes DNS records for each pod, which is what gives StatefulSet replicas stable pod-level names like `app-0.service.namespace.svc.cluster.local`.

---

## 1. Implementation

The chart now supports a dedicated StatefulSet path in addition to the existing Deployment path.

### Files

- `k8s/devops-info-service/templates/statefulset.yaml`
- `k8s/devops-info-service/templates/service-headless.yaml`
- `k8s/devops-info-service/templates/pvc.yaml`
- `k8s/devops-info-service/templates/deployment.yaml`
- `k8s/devops-info-service/templates/_helpers.tpl`
- `k8s/devops-info-service/values-statefulset.yaml`

### Behavior

- `deployment.yaml` renders only when both Rollout and StatefulSet are disabled.
- `pvc.yaml` renders only for the shared-PVC Deployment path.
- `statefulset.yaml` renders when `statefulset.enabled: true`.
- `service-headless.yaml` renders when `statefulset.enabled: true`.

---

## 2. Resource Verification

Deploy the StatefulSet profile with:

```bash
helm upgrade --install devops-info-service k8s/devops-info-service \
  -f k8s/devops-info-service/values-statefulset.yaml
```

Verify the resources:

```bash
kubectl get po,sts,svc,pvc
```

Expected resources:

- `StatefulSet` with ordinal pods such as `devops-info-service-0`, `devops-info-service-1`, `devops-info-service-2`
- Headless service named `devops-info-service-headless`
- External service still available for client access
- One PVC per replica, created automatically from `volumeClaimTemplates`

---

## 3. Network Identity

The headless service gives each pod a stable DNS name.

### DNS Pattern

```text
<pod-name>.<headless-service>.<namespace>.svc.cluster.local
```

For example:

```text
devops-info-service-0.devops-info-service-headless.default.svc.cluster.local
```

### Resolution Test

Run this from one pod:

```bash
kubectl exec -it devops-info-service-0 -- /bin/sh
nslookup devops-info-service-1.devops-info-service-headless
```

You should see the peer pod resolve to a stable cluster IP.

---

## 4. Per-Pod Storage Evidence

Each pod gets its own PVC because the StatefulSet uses `volumeClaimTemplates`.

### Verify PVCs

```bash
kubectl get pvc
```

You should see separate claims such as:

- `data-volume-devops-info-service-0`
- `data-volume-devops-info-service-1`
- `data-volume-devops-info-service-2`

### Verify Independent Visit Counts

Port-forward individual pods and compare visit counts:

```bash
kubectl port-forward pod/devops-info-service-0 8080:5000
kubectl port-forward pod/devops-info-service-1 8081:5000
curl http://localhost:8080/visits
curl http://localhost:8081/visits
```

If you increment one pod, the other pod should keep its own counter.

---

## 5. Persistence Test

StatefulSet storage survives pod deletion.

### Procedure

1. Read the visit count from a pod.
2. Delete only that pod, not the StatefulSet.
3. Wait for Kubernetes to recreate the same ordinal pod.
4. Read the visit count again.

### Commands

```bash
kubectl exec devops-info-service-0 -- cat /data/visits
kubectl delete pod devops-info-service-0
kubectl exec devops-info-service-0 -- cat /data/visits
```

The value should remain the same after the restart because the pod reattaches the same PVC.

---

## 6. Ordered vs Parallel Pod Management

The chart exposes `statefulset.podManagementPolicy`.

- `OrderedReady` starts and terminates pods one by one.
- `Parallel` lets Kubernetes manage pod transitions concurrently.

For applications with startup dependencies or strict ordering requirements, keep `OrderedReady`. For simpler workloads, `Parallel` may reduce rollout time.

---

## 7. Update Strategies

### Rolling Update with Partition

The chart supports partitioned rolling updates via:

```yaml
statefulset:
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      partition: 2
```

With `partition: 2`, only pods with ordinal `>= 2` update automatically.

### OnDelete

The chart also supports manual updates:

```yaml
statefulset:
  updateStrategy:
    type: OnDelete
```

Pods only pick up the new spec after they are deleted manually.

### Use Cases

- `RollingUpdate + partition`: staged upgrades for clustered services
- `OnDelete`: controlled upgrades for data-sensitive systems where you want manual approval between pod restarts

---

## 8. Reference Commands

```bash
# Resources
kubectl get statefulset
kubectl get pods
kubectl get pvc

# Details
kubectl describe statefulset devops-info-service
kubectl describe pod devops-info-service-0

# DNS
kubectl exec -it devops-info-service-0 -- /bin/sh
nslookup devops-info-service-1.devops-info-service-headless

# Persistence
kubectl exec devops-info-service-0 -- cat /data/visits
kubectl delete pod devops-info-service-0

# Update strategy experiments
helm upgrade devops-info-service k8s/devops-info-service \
  -f k8s/devops-info-service/values-statefulset.yaml \
  --set statefulset.updateStrategy.type=OnDelete
```

---

## Summary

StatefulSets are the correct Kubernetes controller when each replica needs a stable identity and dedicated storage. This chart now supports:

- a StatefulSet deployment path,
- a headless service for stable DNS,
- per-pod PVCs via `volumeClaimTemplates`,
- and configurable update strategies for the bonus task.

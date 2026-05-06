# Lab 13 - GitOps with ArgoCD

## 1. ArgoCD setup

ArgoCD was installed into the dedicated `argocd` namespace with the official Helm chart:

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update argo
kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -
helm upgrade --install argocd argo/argo-cd \
  --version 9.5.4 \
  --namespace argocd \
  --set configs.params.server\\.insecure=true \
  --set server.service.type=ClusterIP
```

The chart version used was `argo-cd-9.5.4`, which installs ArgoCD `v3.3.8`.

The default Redis image from the chart used `ecr-public.aws.com`, which was slow from the lab environment. The release was upgraded to use Docker Hub Redis instead:

```bash
helm upgrade argocd argo/argo-cd \
  --version 9.5.4 \
  --namespace argocd \
  --reuse-values \
  --set redis.image.repository=redis \
  --set redis.image.tag=8.2.3-alpine
```

Access method:

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:80
```

Admin password:

```bash
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath='{.data.password}' | base64 -d
```

CLI was installed locally as `.tools/argocd` and excluded from Git via `.git/info/exclude`.

Evidence:

- `k8s/screenshots/lab13/01-argocd-install-cli.txt`
- `k8s/screenshots/lab13/01-argocd-install-cli.png`
- `k8s/screenshots/lab13/ui-01-applications.png`

## 2. Application configuration

Application manifests are stored in `k8s/argocd/`:

- `application.yaml` - single manual-sync application deployed to `lab13`
- `application-dev.yaml` - dev application deployed to `dev`
- `application-prod.yaml` - prod application deployed to `prod`
- `applicationset.yaml` - bonus ApplicationSet pattern

The applications deploy the Helm chart from:

```text
repoURL: https://github.com/Dart-NEW/DevOps-Core-Course.git
targetRevision: lab12
path: k8s/devops-info-service
```

`targetRevision` is `lab12` for the actual cluster run because the current `lab13` branch is local and not pushed yet. After committing and pushing lab13, change the manifests to `targetRevision: lab13` and sync again.

The deployed applications:

```text
devops-info-service       -> namespace lab13, values.yaml, manual sync
devops-info-service-dev   -> namespace dev, values-dev.yaml, auto sync
devops-info-service-prod  -> namespace prod, values-prod.yaml, manual sync
```

For kind compatibility, prod overrides `service.type=NodePort` and `service.nodePort=30085`; otherwise a `LoadBalancer` service stays with `<pending>` external IP and ArgoCD health remains `Progressing`.

Evidence:

- `k8s/screenshots/lab13/02-argocd-app-list.txt`
- `k8s/screenshots/lab13/03-dev-app-details.txt`
- `k8s/screenshots/lab13/07-dev-prod-resources.txt`
- `k8s/screenshots/lab13/09-app-access.txt`

## 3. Multi-environment deployment

Dev and prod are separated by namespace:

```bash
kubectl create namespace dev
kubectl create namespace prod
```

Dev uses:

- `values-dev.yaml`
- `replicaCount: 1`
- smaller CPU/memory requests and limits
- automated sync with `prune: true` and `selfHeal: true`

Prod uses:

- `values-prod.yaml`
- `replicaCount: 4`
- larger CPU/memory requests and limits
- manual sync

Rationale:

- Dev can auto-sync because fast feedback and self-healing are useful.
- Prod stays manual so release timing, review, and rollback planning remain controlled.

Current app state:

```text
devops-info-service       Synced Healthy Manual
devops-info-service-dev   Synced Healthy Auto-Prune
devops-info-service-prod  Synced Healthy Manual
```

## 4. Self-healing evidence

### 4.1 Manual scale drift

Command:

```bash
kubectl scale deployment/devops-info-service-dev -n dev --replicas=5
```

Observed behavior:

- ArgoCD detected `Deployment` as `OutOfSync`.
- Dev auto-sync/selfHeal restored the desired Git state.
- Replicas returned from `desired=5` to `desired=1`.

Evidence:

- `k8s/screenshots/lab13/04-self-heal-scale.txt`
- `k8s/screenshots/lab13/04-self-heal-scale.png`

### 4.2 Pod deletion

Command:

```bash
kubectl delete pod -n dev <pod-name>
```

Observed behavior:

- Kubernetes recreated/maintained the pod via Deployment/ReplicaSet.
- This is Kubernetes self-healing, not ArgoCD self-healing, because the desired Deployment spec did not drift from Git.

Evidence:

- `k8s/screenshots/lab13/05-pod-deletion.txt`
- `k8s/screenshots/lab13/05-pod-deletion.png`

### 4.3 ConfigMap drift

Command:

```bash
kubectl patch configmap -n dev devops-info-service-dev-env \
  --type merge \
  -p '{"data":{"LOG_LEVEL":"trace"}}'
```

Observed behavior:

- ArgoCD detected the env ConfigMap as `OutOfSync`.
- Auto-sync/selfHeal restored `LOG_LEVEL=debug` from Git.

Evidence:

- `k8s/screenshots/lab13/06-config-drift-configmap.txt`
- `k8s/screenshots/lab13/06-config-drift-configmap.png`

## 5. Sync behavior

ArgoCD syncs when:

- a user manually triggers sync;
- automated sync is enabled and Git/cluster state differs;
- self-heal is enabled and live cluster drift is detected;
- a refresh discovers a new revision or changed live state.

Kubernetes heals workload availability when:

- a pod is deleted;
- a container exits;
- the Deployment/ReplicaSet desired pod count is not met.

Default ArgoCD Git polling is about every 3 minutes. Webhooks or manual refresh/sync can make detection immediate.

## 6. Bonus - ApplicationSet

`k8s/argocd/applicationset.yaml` implements a List generator for dev and prod.

It captures the shared application template once and varies:

- environment name;
- namespace;
- Helm values file;
- NodePort;
- sync policy.

The ApplicationSet was validated with:

```bash
kubectl apply --dry-run=server -f k8s/argocd/applicationset.yaml
```

It was not applied to the live cluster to avoid creating duplicate demo applications in the same `dev` and `prod` namespaces.

Evidence:

- `k8s/screenshots/lab13/08-applicationset-dry-run.txt`
- `k8s/screenshots/lab13/08-applicationset-dry-run.png`

ApplicationSet is useful when the same app must be deployed repeatedly across environments, clusters, or tenants. Individual Application manifests are simpler for one or two deployments; ApplicationSet scales better when the environment list grows.

## 7. Screenshots

Required UI screenshots:

- `k8s/screenshots/lab13/ui-01-applications.png`
- `k8s/screenshots/lab13/ui-02-dev-details.png`

All generated lab13 artifacts are indexed in:

- `k8s/screenshots/lab13/99-index.txt`

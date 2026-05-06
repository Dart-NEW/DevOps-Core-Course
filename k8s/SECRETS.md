# Lab 11 - Kubernetes Secrets и HashiCorp Vault

## 1. Kubernetes Secrets Fundamentals

### 1.1 Создание секрета через kubectl (фактический вывод)

```bash
kubectl delete secret app-credentials --ignore-not-found
kubectl create secret generic app-credentials \
  --from-literal=username=admin \
  --from-literal=password=secret123
kubectl get secret app-credentials -o yaml
```

```text
secret/app-credentials created
apiVersion: v1
data:
  password: c2VjcmV0MTIz
  username: YWRtaW4=
kind: Secret
metadata:
  name: app-credentials
  namespace: default
type: Opaque
```

### 1.2 Декодирование base64 (фактический вывод)

```bash
echo 'YWRtaW4=' | base64 -d
echo 'c2VjcmV0MTIz' | base64 -d
```

```text
admin
secret123
```

### 1.3 Base64 vs encryption

- `Secret.data` хранится в base64 (это кодирование, не шифрование).
- Для защиты at-rest в production нужно включать шифрование etcd (encryption provider config).
- Доступ к секретам ограничивается RBAC, иначе любой субъект с `get secrets` может прочитать и декодировать значения.

## 2. Helm Secret Integration

### 2.1 Изменения в chart

- Добавлен `k8s/devops-info-service/templates/secrets.yaml`.
- Обновлен `k8s/devops-info-service/templates/deployment.yaml` (`envFrom.secretRef`, Vault annotations, named template include).
- Обновлены `k8s/devops-info-service/values.yaml`, `k8s/devops-info-service/values-dev.yaml`, `k8s/devops-info-service/values-prod.yaml`.

### 2.2 Проверка рендера

```bash
helm lint k8s/devops-info-service
helm template devops k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml
```

`helm lint` проходит без ошибок.

### 2.3 Проверка инъекции секретов в Pod (фактический вывод)

```bash
kubectl exec -n lab11 <pod> -c devops-info-service -- sh -lc 'printenv | grep -E "^(username|password|api_key)="'
```

```text
username=dev-user
password=dev-password
api_key=dev-api-key
```

### 2.4 Проверка, что значения не раскрываются в describe (фактический вывод)

```bash
kubectl describe pod <pod> -n lab11
```

```text
Environment Variables from:
  lab11-app-devops-info-service-app-secrets  Secret  Optional: false
Environment:
  APP_ENV:    development
  LOG_LEVEL:  debug
  HOST:       0.0.0.0
  PORT:       5000
  DEBUG:      true
```

Значения `username/password/api_key` напрямую не печатаются, только ссылка на Secret.

## 3. Resource Management

### 3.1 Конфигурация

`requests/limits` задаются в values и применяются в deployment.

Пример (`values-dev.yaml`):

```yaml
resources:
  requests:
    cpu: 50m
    memory: 64Mi
  limits:
    cpu: 100m
    memory: 128Mi
```

### 3.2 Requests vs limits

- `requests` - гарантированный минимум, учитывается scheduler.
- `limits` - верхний потолок, после которого начинается throttling (CPU) или OOMKill (memory).

## 4. Vault Integration

### 4.1 Установка Vault (фактический вывод)

```bash
kubectl create namespace lab11 --dry-run=client -o yaml | kubectl apply -f -
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update
helm upgrade --install vault hashicorp/vault \
  --namespace lab11 \
  --set "server.dev.enabled=true" \
  --set "injector.enabled=true"
kubectl get pods -n lab11
```

```text
NAME                                    READY   STATUS    RESTARTS   AGE
vault-0                                 1/1     Running   0          28s
vault-agent-injector-598fbb767b-phhl5   1/1     Running   0          28s
```

### 4.2 Настройка KV v2, policy и role (фактический вывод)

```bash
kubectl exec -n lab11 vault-0 -- sh -lc '<vault commands>'
kubectl exec -n lab11 vault-0 -- sh -lc 'vault policy read devops-info-service'
kubectl exec -n lab11 vault-0 -- sh -lc 'vault read auth/kubernetes/role/devops-info-service'
kubectl exec -n lab11 vault-0 -- sh -lc 'vault kv get secret/devops-info-service/config'
```

```text
path "secret/data/devops-info-service/config" {
  capabilities = ["read"]
}

bound_service_account_namespaces            [lab11]
policies                                    [devops-info-service]

====== Data ======
api_key     vault-api-key
password    vault-pass
username    vault-user
```

Важно по путям:

- В policy для KV v2 используется путь с `/data/`: `secret/data/devops-info-service/config`.
- В аннотации injector используется путь без `/data/`: `secret/devops-info-service/config`.

### 4.3 Проверка Vault Agent Injection (фактический вывод)

```bash
kubectl describe pod <pod> -n lab11
kubectl exec -n lab11 <pod> -c devops-info-service -- sh -lc 'cat -n /vault/secrets/config'
```

```text
Annotations:
  vault.hashicorp.com/agent-inject: true
  vault.hashicorp.com/agent-inject-secret-config: secret/devops-info-service/config
  vault.hashicorp.com/agent-inject-status: injected

     1  APP_USERNAME=vault-user
     2  APP_PASSWORD=vault-pass
     3  APP_API_KEY=vault-api-key
```

## 5. Security Analysis

| Критерий | Kubernetes Secrets | HashiCorp Vault |
|---|---|---|
| Хранение | etcd, данные в API как base64 | Централизованное защищенное хранилище |
| Шифрование | Нужно явно включать etcd encryption | Нативные механизмы и политики |
| Ротация | Обычно вручную/внешними средствами | TTL/lease, автообновление, динамические секреты |
| Аудит | K8s audit logs | Развитый аудит-доступ и политики |
| Сложность | Проще старт | Сложнее, но безопаснее для production |

Рекомендации для production:

- Включить encryption at rest для etcd.
- Настроить strict RBAC и отдельные service accounts.
- Не хранить реальные секреты в Git.
- Включить аудит и ротацию.

## 6. Bonus - Vault Agent Templates

### 6.1 Template annotation

Используется `vault.hashicorp.com/agent-inject-template-config` для рендера нескольких секретов в один файл `config`.

### 6.2 Ротация и обновления

Vault Agent периодически обновляет секреты (в зависимости от TTL/lease). Для реакции приложения можно использовать:

- `vault.hashicorp.com/agent-inject-command`

Например: отправить `SIGHUP` процессу после перезаписи файла секрета.

### 6.3 Named template в Helm

В `_helpers.tpl` добавлен `devops-info-service.commonEnv`, который переиспользуется в `deployment.yaml` через `include`.

Это реализует DRY-подход для общих non-secret переменных окружения.

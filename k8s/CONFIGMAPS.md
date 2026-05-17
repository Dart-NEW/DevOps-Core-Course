# Lab 12 - ConfigMaps & Persistent Volumes

## 0. Важный порядок деплоя

Перед любыми действиями в Kubernetes сначала переключаемся с рабочего конфига на учебный:

```bash
kubectl config use-context kind-lab09
kubectl config current-context
```

Фактический вывод:

```text
Switched to context "kind-lab09".
kind-lab09
```

---

## 1. Изменения в приложении

### 1.1 Что реализовано

В Python-сервисе реализован файловый счетчик визитов:

- На `GET /` счетчик увеличивается на 1.
- Счетчик хранится в файле `VISITS_FILE` (по умолчанию `data/visits`, в Kubernetes `/data/visits`).
- Добавлен endpoint `GET /visits`, который возвращает текущее значение.
- Реализована потокобезопасность через `threading.Lock`.
- Запись в файл атомарная (`.tmp` + `os.replace`).

### 1.2 Локальная проверка (Docker Compose)

Compose уже настроен на volume:

```yaml
volumes:
  - ./data:/app/data
```

Проверка:

```bash
mkdir -p data
docker compose up -d
curl http://localhost:5000/
curl http://localhost:5000/visits
cat ./data/visits
docker compose restart
curl http://localhost:5000/visits
```

В текущем окружении порт `5000` занят локальным registry, поэтому фактическая проверка выполнена тем же compose-сервисом на host-порту `5001`. Скриншот и вывод: `k8s/screenshots/lab12/00-local-compose.png` и `00-local-compose.txt`.

### 1.3 Проверка тестами

```bash
cd app_python
/home/dart/Programming/DevOps-Core-Course/.venv/bin/python -m pytest -q
```

Фактический вывод:

```text
7 passed in 0.79s
Total coverage: 90.17%
```

---

## 2. Реализация ConfigMap

### 2.1 Что добавлено в Helm chart

- `k8s/devops-info-service/files/config.json` - файловая конфигурация.
- `k8s/devops-info-service/templates/configmap-file.yaml` - ConfigMap с `config.json` через `.Files.Get`.
- `k8s/devops-info-service/templates/configmap-env.yaml` - ConfigMap c env-переменными (`APP_ENV`, `LOG_LEVEL`, `APP_CONFIG_PATH`, `VISITS_FILE`, `FEATURE_VISITS_COUNTER`).
- `k8s/devops-info-service/templates/deployment.yaml`:
  - `envFrom.configMapRef` для env ConfigMap.
  - Монтирование файлового ConfigMap в `/config`.

### 2.2 Проверка рендера Helm

```bash
helm lint k8s/devops-info-service
helm template devops-lab12 k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml
```

Фактический вывод lint:

```text
1 chart(s) linted, 0 chart(s) failed
```

### 2.3 Проверка в Pod

```bash
POD=$(kubectl get pod -n lab12 -l app.kubernetes.io/instance=lab12-devops -o jsonpath='{.items[0].metadata.name}')
kubectl exec -n lab12 "$POD" -- cat /config/config.json
kubectl exec -n lab12 "$POD" -- sh -lc 'printenv | grep -E "^(APP_ENV|LOG_LEVEL|APP_CONFIG_PATH|VISITS_FILE|FEATURE_VISITS_COUNTER)="'
```

Фактический вывод:

```text
{
  "appName": "devops-info-service",
  "environment": "kubernetes",
  "features": {
    "visitsCounter": true,
    "metricsEnabled": true,
    "structuredLogging": true
  },
  "settings": {
    "welcomeMessage": "DevOps Info Service is running",
    "runtimeTimezone": "UTC"
  }
}
LOG_LEVEL=debug
APP_CONFIG_PATH=/config/config.json
FEATURE_VISITS_COUNTER=true
VISITS_FILE=/data/visits
APP_ENV=development
```

---

## 3. Persistent Volume (PVC)

### 3.1 Что добавлено

- `k8s/devops-info-service/templates/pvc.yaml`.
- В `values.yaml`/`values-dev.yaml`/`values-prod.yaml` добавлен блок `persistence`:
  - `enabled`
  - `size`
  - `accessMode`
  - `storageClass`
  - `mountPath`
  - `visitsFile`
- В deployment:
  - volume `data-volume` (через PVC)
  - mount в `/data`

### 3.2 Применение

```bash
kubectl create namespace lab12 --dry-run=client -o yaml | kubectl apply -f -
helm upgrade --install lab12-devops ./k8s/devops-info-service -n lab12 -f k8s/devops-info-service/values-dev.yaml --set service.nodePort=30082
kubectl rollout status deployment/lab12-devops-devops-info-service -n lab12 --timeout=180s
```

### 3.3 Проверка ресурсов

```bash
kubectl get configmap,pvc -n lab12
```

Фактический вывод:

```text
NAME                                                DATA   AGE
configmap/kube-root-ca.crt                          1      4d21h
configmap/lab12-devops-devops-info-service-config   1      4d21h
configmap/lab12-devops-devops-info-service-env      5      4d21h

NAME                                                          STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
persistentvolumeclaim/lab12-devops-devops-info-service-data   Bound    pvc-8ce15048-3fcc-4d90-8706-c97019dd939a   100Mi      RWO            standard       <unset>                 4d21h
```

### 3.4 Доказательство сохранения данных

Проверка до удаления pod:

```bash
# Генерируем визиты
kubectl exec -n lab12 "$POD" -- sh -lc 'python - <<"PY"
from urllib.request import urlopen
for _ in range(3):
    urlopen("http://127.0.0.1:5000/").read()
print(urlopen("http://127.0.0.1:5000/visits").read().decode())
PY'

kubectl exec -n lab12 "$POD" -- cat /data/visits
```

Фактический вывод:

```text
{
  "visits": 9,
  "path": "/data/visits"
}
BEFORE=9
```

Удаление pod и проверка после пересоздания:

```bash
kubectl delete pod -n lab12 <pod-name>
kubectl wait --for=condition=ready pod -n lab12 -l app.kubernetes.io/instance=lab12-devops --timeout=180s
NEW_POD=$(kubectl get pod -n lab12 -l app.kubernetes.io/instance=lab12-devops -o jsonpath='{.items[0].metadata.name}')
kubectl exec -n lab12 "$NEW_POD" -- cat /data/visits
```

Фактический вывод:

```text
NEW_POD=lab12-devops-devops-info-service-666b4d8b78-z5xfz
AFTER=9
```

Данные сохранились после удаления pod.

---

## 4. Bonus - Hot Reload и поведение обновлений

### 4.1 Задержка обновления mounted ConfigMap

Измерение через marker в `config.json` и polling внутри pod:

```text
MARKER=reloaded-1776789601
UPDATE_DELAY_SECONDS=35
"welcomeMessage": "reloaded-1776789601"
```

Итог: обновление файла в mounted ConfigMap произошло примерно за 35 секунд.

### 4.2 Почему `subPath` не подходит для auto-update

- При `subPath` файл монтируется как отдельная bind-монтажная точка.
- Обновление исходного ConfigMap не переотражается в уже смонтированный `subPath`-файл.
- Для автообновления нужен mount директории целиком (как сделано: `/config`).

### 4.3 Реализованный подход перезагрузки

Реализован checksum pattern в Pod template annotations:

- `checksum/config-file`
- `checksum/config-env`

При изменении конфигурации (`files/config.json`, `appEnv`, `logLevel`, `VISITS_FILE`, feature-флаг) меняется шаблон Pod и Deployment делает rollout.

---

## 5. ConfigMap vs Secret

### Когда использовать ConfigMap

- Нечувствительные настройки:
  - имя приложения
  - feature flags
  - log level
  - пути к файлам

### Когда использовать Secret

- Любые секретные данные:
  - пароли
  - API keys
  - токены
  - сертификаты

### Ключевые различия

- `ConfigMap` - для обычной конфигурации.
- `Secret` - для чувствительных данных (в Kubernetes хранится base64, для production рекомендуется encryption at rest + RBAC).
- В этом проекте Secret уже используется для `username/password/api_key`, ConfigMap - для операционных настроек.

---

## 6. Измененные файлы

- `k8s/devops-info-service/files/config.json`
- `k8s/devops-info-service/templates/configmap-file.yaml`
- `k8s/devops-info-service/templates/configmap-env.yaml`
- `k8s/devops-info-service/templates/pvc.yaml`
- `k8s/devops-info-service/templates/deployment.yaml`
- `k8s/devops-info-service/templates/_helpers.tpl`
- `k8s/devops-info-service/values.yaml`
- `k8s/devops-info-service/values-dev.yaml`
- `k8s/devops-info-service/values-prod.yaml`
- `k8s/CONFIGMAPS.md`

---

## 7. Готовые артефакты для отчета

Автоматически собранные доказательства находятся в директории:

- `k8s/screenshots/lab12/`

Ключевые файлы:

- `00-local-compose.png`
- `01-get-configmap-pvc.png`
- `04-config-in-pod.png`
- `05-env-in-pod.png`
- `13-persistence-before-after.png`
- `01-get-configmap-pvc.txt`
- `04-config-in-pod.json`
- `05-env-in-pod.txt`
- `07-before-delete-counter.txt`
- `08-delete-pod.txt`
- `09-wait-new-pod.txt`
- `11-after-delete-counter.txt`

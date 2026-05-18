# Lab12 Evidence Package

This directory contains auto-collected verification artifacts for Lab12.

## Screenshot Status

Direct desktop capture is not available in this environment, so the required command outputs were captured as text and rendered into PNG screenshots.

PNG screenshots:

- `00-local-compose.png`
- `01-get-configmap-pvc.png`
- `04-config-in-pod.png`
- `05-env-in-pod.png`
- `13-persistence-before-after.png`

## Required Lab12 Evidence

- `01-get-configmap-pvc.txt`: `kubectl get configmap,pvc -n lab12`
- `04-config-in-pod.json`: `cat /config/config.json` inside pod
- `05-env-in-pod.txt`: `printenv` filtered for `APP_*`, `LOG_LEVEL`, `VISITS_FILE`
- `07-before-delete-counter.txt`: visit counter before pod deletion
- `08-delete-pod.txt`: pod deletion command output
- `09-wait-new-pod.txt`: readiness of replacement pod
- `10-new-pod-name.txt`: replacement pod name
- `11-after-delete-counter.txt`: visit counter after replacement pod started
- `13-persistence-before-after.txt`: combined before/delete/wait/after proof used for the PNG screenshot

## Supporting Files

- `02-get-pods-svc.txt`: pods and service state
- `03-pod-name.txt`: initial pod name used for checks
- `06-visits-endpoint-before-delete.txt`: `/visits` endpoint response before deletion
- `12-new-pod-wide.txt`: replacement pod details
- `98-metadata.txt`: collection timestamp and kube context
- `99-index.txt`: directory index

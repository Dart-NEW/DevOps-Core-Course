{{/*
Wrap the shared library helpers so the application templates stay readable.
*/}}
{{- define "devops-info-service.fullname" -}}
{{- include "common-lib.fullname" . -}}
{{- end -}}

{{- define "devops-info-service.labels" -}}
{{- include "common-lib.labels" . -}}
{{- end -}}

{{- define "devops-info-service.selectorLabels" -}}
{{- include "common-lib.selectorLabels" . -}}
{{- end -}}

{{/*
Common non-secret environment variables (bonus task DRY template).
*/}}
{{- define "devops-info-service.commonEnv" -}}
- name: APP_ENV
  value: {{ .Values.appEnv | quote }}
- name: LOG_LEVEL
  value: {{ .Values.logLevel | quote }}
{{- end -}}

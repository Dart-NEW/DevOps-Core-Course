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
Name for the file-backed ConfigMap.
*/}}
{{- define "devops-info-service.configFileName" -}}
{{- printf "%s-config" (include "devops-info-service.fullname" .) -}}
{{- end -}}

{{/*
Name for the env ConfigMap.
*/}}
{{- define "devops-info-service.configEnvName" -}}
{{- printf "%s-env" (include "devops-info-service.fullname" .) -}}
{{- end -}}

{{/*
Name for the PVC used by the visit counter.
*/}}
{{- define "devops-info-service.pvcName" -}}
{{- printf "%s-data" (include "devops-info-service.fullname" .) -}}
{{- end -}}

{{/*
Name for the headless service used by StatefulSet pods.
*/}}
{{- define "devops-info-service.headlessServiceName" -}}
{{- printf "%s-headless" (include "devops-info-service.fullname" .) -}}
{{- end -}}

{{/*
Name for the blue-green preview service.
*/}}
{{- define "devops-info-service.previewServiceName" -}}
{{- printf "%s-preview" (include "devops-info-service.fullname" .) -}}
{{- end -}}

{{/*
Name for the canary AnalysisTemplate.
*/}}
{{- define "devops-info-service.analysisTemplateName" -}}
{{- printf "%s-health" (include "devops-info-service.fullname" .) -}}
{{- end -}}

{{/*
Common non-secret environment variables used by the application.
*/}}
{{- define "devops-info-service.commonEnv" -}}
- name: APP_ENV
  value: {{ .Values.appEnv | quote }}
- name: LOG_LEVEL
  value: {{ .Values.logLevel | quote }}
{{- end -}}

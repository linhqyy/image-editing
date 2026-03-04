{{- define "comfyui-api.name" -}}
{{- .Chart.Name }}
{{- end }}

{{- define "comfyui-api.labels" -}}
app: {{ include "comfyui-api.name" . }}
app.kubernetes.io/name: {{ include "comfyui-api.name" . }}
app.kubernetes.io/version: {{ .Chart.AppVersion }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
{{- end }}

{{- define "comfyui-api.selectorLabels" -}}
app: {{ include "comfyui-api.name" . }}
{{- end }}

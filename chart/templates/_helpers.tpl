{{/* Full name definition */}}
{{- define "argocd-custom-exporter.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := default .Chart.Name .Values.nameOverride -}}
{{- if contains $name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
{{- end -}}

{{/* ServiceAccount name definition */}}
{{- define "argocd-custom-exporter.serviceAccountName" -}}
{{- if .Values.serviceAccount.create -}}
{{- default (include "argocd-custom-exporter.fullname" .) .Values.serviceAccount.name -}}
{{- else -}}
{{- default "default" .Values.serviceAccount.name -}}
{{- end -}}
{{- end -}}

{{/* Name definition */}}
{{- define "argocd-custom-exporter.name" -}}
{{- default .Chart.Name .Values.nameOverride -}}
{{- end -}}

{{/* Common labels definition */}}
{{- define "argocd-custom-exporter.labels" -}}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version | replace "+" "_" }}
app.kubernetes.io/name: {{ include "argocd-custom-exporter.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- if .Values.customLabels }}
{{- toYaml .Values.customLabels }}
{{- end -}}
{{- end -}}

{{/* Selector labels definition */}}
{{- define "argocd-custom-exporter.selectorLabels" -}}
app.kubernetes.io/name: {{ include "argocd-custom-exporter.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

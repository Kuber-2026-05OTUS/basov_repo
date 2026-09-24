#!/usr/bin/env bash
# Local/CI helper: run every static K8s/Helm validation that does not need a
# live cluster. Exits non-zero on the first failing tool so CI stops early.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "== yamllint =="
yamllint -c .yamllint.yaml k8s airflow monitoring

echo "== kubeconform (schema validation, no cluster needed) =="
if command -v kubeconform >/dev/null 2>&1; then
  find k8s -name '*.yaml' -print0 | xargs -0 kubeconform -strict -summary
else
  echo "kubeconform not installed -- skipping (see docs/cloud/README.md 'Local validation tools')"
fi

echo "== helm lint (Airflow chart with our values) =="
if command -v helm >/dev/null 2>&1; then
  helm repo add apache-airflow https://airflow.apache.org >/dev/null 2>&1 || true
  helm repo update >/dev/null
  helm lint apache-airflow/airflow -f airflow/values.yaml -f airflow/values-dev.yaml
else
  echo "helm not installed -- skipping (see docs/cloud/README.md 'Local validation tools')"
fi

echo "All available K8s/Helm validations passed."

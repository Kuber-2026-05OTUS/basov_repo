#!/usr/bin/env bash
set -Eeuo pipefail
TF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$TF_DIR"
need(){ command -v "$1" >/dev/null 2>&1 || { echo "ERROR: '$1' is required" >&2; exit 1; }; }
need terraform
need kubectl
need helm

kubectl delete -f ../../kubernetes-demo/k8s/airflow/servicemonitor.yaml --ignore-not-found || true
helm uninstall kube-prometheus-stack -n monitoring 2>/dev/null || true
helm uninstall airflow -n airflow 2>/dev/null || true
kubectl delete -f ../../kubernetes-demo/k8s/network-policies/ --ignore-not-found || true
kubectl delete -f ../../kubernetes-demo/k8s/airflow/networkpolicy.yaml --ignore-not-found || true
kubectl delete -f ../../kubernetes-demo/k8s/streamlit/networkpolicy.yaml --ignore-not-found || true
kubectl delete -f ../../kubernetes-demo/k8s/mongodb/networkpolicy.yaml --ignore-not-found || true
kubectl delete -f ../../kubernetes-demo/k8s/streamlit/ --ignore-not-found || true
kubectl delete -f ../../kubernetes-demo/k8s/rbac/ --ignore-not-found || true
kubectl delete -f ../../kubernetes-demo/k8s/mongodb/ --ignore-not-found || true
kubectl delete -f ../../kubernetes-demo/k8s/namespaces.yaml --ignore-not-found || true

terraform destroy

#!/usr/bin/env bash
set -Eeuo pipefail

TF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_ROOT="$(cd "$TF_DIR/../.." && pwd)"
cd "$TF_DIR"

need() { command -v "$1" >/dev/null 2>&1 || { echo "ERROR: '$1' is required" >&2; exit 1; }; }
for bin in terraform yc kubectl helm docker git; do need "$bin"; done

: "${GRAFANA_ADMIN_PASSWORD:=${TF_VAR_grafana_admin_password:-}}"
if [[ -z "$GRAFANA_ADMIN_PASSWORD" ]]; then
  echo "ERROR: set GRAFANA_ADMIN_PASSWORD before running deploy.sh" >&2
  exit 1
fi

CLUSTER_ID="$(terraform output -raw cluster_id)"
REGISTRY_ID="$(terraform output -raw registry_id)"
IMAGE_TAG="$(terraform output -json 2>/dev/null | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get("streamlit_image",{}).get("value","").rsplit(":",1)[-1])')"
IMAGE_TAG="${IMAGE_TAG:-1.0.0}"
STREAMLIT_IMAGE="cr.yandex/${REGISTRY_ID}/streamlit:${IMAGE_TAG}"
SPARK_IMAGE="cr.yandex/${REGISTRY_ID}/spark-job:${IMAGE_TAG}"

printf '\n==> Configure Docker for Yandex Container Registry\n'
yc container registry configure-docker

printf '\n==> Build and push Streamlit image: %s\n' "$STREAMLIT_IMAGE"
docker build -f "$REPO_ROOT/kubernetes-demo/streamlit_app/Dockerfile" -t "$STREAMLIT_IMAGE" "$REPO_ROOT/kubernetes-demo"
docker push "$STREAMLIT_IMAGE"

printf '\n==> Build and push Spark image: %s\n' "$SPARK_IMAGE"
docker build -f "$TF_DIR/docker/spark-job.Dockerfile" -t "$SPARK_IMAGE" "$REPO_ROOT"
docker push "$SPARK_IMAGE"

printf '\n==> Get external Kubernetes credentials\n'
yc managed-kubernetes cluster get-credentials --id "$CLUSTER_ID" --external --force
kubectl config current-context
kubectl get nodes

printf '\n==> Namespaces and secrets\n'
kubectl apply -f "$REPO_ROOT/kubernetes-demo/k8s/namespaces.yaml"

MONGO_USER="${MONGO_ROOT_USER:-admin}"
MONGO_PASSWORD="${MONGO_ROOT_PASSWORD:-$(openssl rand -hex 20)}"
MONGO_URI="mongodb://${MONGO_USER}:${MONGO_PASSWORD}@mongodb.data-platform.svc.cluster.local:27017/?authSource=admin"

kubectl -n data-platform create secret generic mongodb-admin-credentials \
  --from-literal=MONGO_INITDB_ROOT_USERNAME="$MONGO_USER" \
  --from-literal=MONGO_INITDB_ROOT_PASSWORD="$MONGO_PASSWORD" \
  --dry-run=client -o yaml | kubectl apply -f -

kubectl -n data-platform create secret generic mongodb-credentials \
  --from-literal=MONGODB_URI="$MONGO_URI" \
  --from-literal=MONGODB_USERNAME="$MONGO_USER" \
  --from-literal=MONGODB_PASSWORD="$MONGO_PASSWORD" \
  --dry-run=client -o yaml | kubectl apply -f -

FERNET_KEY="${AIRFLOW_FERNET_KEY:-$(python3 -c 'import base64,secrets; print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())')}"
AIRFLOW_SECRET_KEY="${AIRFLOW_SECRET_KEY:-$(python3 -c 'import secrets; print(secrets.token_hex(32))')}"

kubectl -n airflow create secret generic airflow-fernet-secret \
  --from-literal=AIRFLOW_FERNET_KEY="$FERNET_KEY" \
  --from-literal=AIRFLOW_SECRET_KEY="$AIRFLOW_SECRET_KEY" \
  --dry-run=client -o yaml | kubectl apply -f -

cat > /tmp/airflow-terraform-values.yaml <<EOF2
# Generated on the Beget administration VPS; never commit this file.
dags:
  gitSync:
    repo: "https://github.com/Kuber-2026-05OTUS/basov_repo.git"
    branch: "kubernetes-demo"
    subPath: "kubernetes-demo/dags"
    depth: 1
extraEnv: |
  - name: SPARK_JOB_IMAGE
    value: "${SPARK_IMAGE}"
  - name: AIRFLOW_TASK_NAMESPACE
    value: "data-platform"
  - name: MONGODB_DATABASE
    value: "currency"
  - name: MONGODB_COLLECTION
    value: "rates"
EOF2

printf '\n==> MongoDB\n'
kubectl apply -f "$REPO_ROOT/kubernetes-demo/k8s/mongodb/"
kubectl -n data-platform rollout status statefulset/mongodb --timeout=10m

printf '\n==> Airflow\n'
helm repo add apache-airflow https://airflow.apache.org >/dev/null 2>&1 || true
helm repo update >/dev/null
helm upgrade --install airflow apache-airflow/airflow \
  --namespace airflow --create-namespace \
  --version 1.15.0 \
  -f "$REPO_ROOT/kubernetes-demo/airflow/values.yaml" \
  -f "$REPO_ROOT/kubernetes-demo/airflow/values-dev.yaml" \
  -f /tmp/airflow-terraform-values.yaml

kubectl apply -f "$REPO_ROOT/kubernetes-demo/k8s/rbac/"
kubectl apply -f "$REPO_ROOT/kubernetes-demo/k8s/network-policies/"
kubectl apply -f "$REPO_ROOT/kubernetes-demo/k8s/airflow/networkpolicy.yaml"
kubectl apply -f "$REPO_ROOT/kubernetes-demo/k8s/streamlit/networkpolicy.yaml"
kubectl apply -f "$REPO_ROOT/kubernetes-demo/k8s/mongodb/networkpolicy.yaml"

printf '\n==> Streamlit\n'
kubectl apply -f "$REPO_ROOT/kubernetes-demo/k8s/streamlit/"
kubectl -n data-platform set image deployment/streamlit streamlit="$STREAMLIT_IMAGE"
kubectl -n data-platform rollout status deployment/streamlit --timeout=10m

if [[ "${ENABLE_MONITORING:-true}" == "true" ]]; then
  printf '\n==> Monitoring\n'
  helm repo add prometheus-community https://prometheus-community.github.io/helm-charts >/dev/null 2>&1 || true
  helm repo update >/dev/null
  helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
    --namespace monitoring --create-namespace \
    -f "$REPO_ROOT/kubernetes-demo/monitoring/prometheus-values.yaml" \
    --set-string "grafana.adminPassword=$GRAFANA_ADMIN_PASSWORD"
  kubectl apply -f "$REPO_ROOT/kubernetes-demo/k8s/airflow/servicemonitor.yaml"
fi

printf '\n==> Verification\n'
kubectl get nodes
kubectl get pods -A
printf '\nStreamlit: kubectl port-forward -n data-platform svc/streamlit 8501:8501\n'
printf 'Airflow:   kubectl port-forward -n airflow svc/airflow-webserver 8080:8080\n'
printf 'Grafana:   kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3000:80\n'
printf '\nAirflow DAG list:\n'
kubectl -n airflow exec deploy/airflow-webserver -- airflow dags list | grep -E 'cbr_rates_pipeline|Dag ID' || true

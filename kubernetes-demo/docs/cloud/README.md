# Yandex Cloud administrator guide

Step-by-step guide for standing up the real infrastructure this project
targets. None of these steps were executed by the agent that wrote this
repository -- see `../../IMPLEMENTATION_REPORT.md` for exactly what was and
was not verified against a live cloud account.

## 1. Prerequisites

- Yandex Cloud account with billing enabled.
- `yc` CLI installed and authenticated (`yc init`).
- `kubectl`, `helm` (>=3.14) installed locally.
- A registered domain (or subdomain) if you want HTTPS ingress for the
  Streamlit app.

## 2. Create a Managed Service for Kubernetes cluster

```bash
yc managed-kubernetes cluster create \
  --name kubernetes-demo \
  --network-name default \
  --zone ru-central1-a \
  --service-account-name kubernetes-demo-sa \
  --node-service-account-name kubernetes-demo-node-sa \
  --public-ip \
  --release-channel stable \
  --version 1.29

yc managed-kubernetes node-group create \
  --name kubernetes-demo-workers \
  --cluster-name kubernetes-demo \
  --platform-id standard-v3 \
  --cores 4 --memory 8 \
  --disk-type network-ssd --disk-size 64 \
  --fixed-size 3 \
  --location zone=ru-central1-a
```

Prefer a 3-node minimum for real HA (Airflow scheduler + webserver
replicas, MongoDB, Streamlit replicas, and Prometheus/Grafana all need to be
schedulable simultaneously without evicting each other).

```bash
yc managed-kubernetes cluster get-credentials kubernetes-demo --external
```

## 3. Namespaces

```bash
kubectl apply -f ../../k8s/namespaces.yaml
```

## 4. Secrets

**Never commit real secret values.** Two supported approaches:

### 4a. Direct kubectl (fastest, fine for a coursework demo)

```bash
kubectl create secret generic mongodb-credentials \
  --namespace data-platform \
  --from-literal=MONGODB_URI="mongodb://<user>:<password>@<host>:27017/?authSource=admin" \
  --from-literal=MONGODB_USERNAME="<user>" \
  --from-literal=MONGODB_PASSWORD="<password>"

kubectl create secret generic airflow-fernet-secret \
  --namespace airflow \
  --from-literal=AIRFLOW_FERNET_KEY="$(python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')" \
  --from-literal=AIRFLOW_SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
```

### 4b. Yandex Lockbox + External Secrets Operator (recommended for real use)

1. Store the same key/value pairs in a Yandex Lockbox secret.
2. Install the External Secrets Operator (`helm install external-secrets ...`).
3. Create a `SecretStore` pointing at Lockbox and an `ExternalSecret` that
   syncs into `mongodb-credentials` / `airflow-fernet-secret`. This keeps the
   secret's source of truth outside the cluster and outside git entirely.

Either way, `../../k8s/secrets/secret.example.yaml` documents the exact
keys each Secret must contain -- copy its structure, never its placeholder
values, into whichever mechanism you choose.

## 5. MongoDB

Two options:

- **In-cluster (this repo's default):** `kubectl apply -f ../../k8s/mongodb/`.
  Fine for a demo; a single-replica StatefulSet is not HA.
- **Managed (recommended for production):** provision Yandex Managed Service
  for MongoDB instead, and point `MONGODB_URI` in the Secret at its
  connection string. Skip applying `k8s/mongodb/*` in that case.

## 6. Airflow

```bash
helm repo add apache-airflow https://airflow.apache.org
helm repo update
helm upgrade --install airflow apache-airflow/airflow \
  --namespace airflow --create-namespace \
  --version 1.15.0 \
  -f ../../airflow/values.yaml \
  -f ../../airflow/values-prod.yaml
```

Wait for `kubectl get pods -n airflow` to show all pods `Running`/`Ready`
before applying RBAC/NetworkPolicy (some CRDs from the chart must exist
first).

## 7. RBAC and NetworkPolicy

```bash
kubectl apply -f ../../k8s/rbac/
kubectl apply -f ../../k8s/network-policies/
kubectl apply -f ../../k8s/airflow/networkpolicy.yaml
kubectl apply -f ../../k8s/streamlit/networkpolicy.yaml
kubectl apply -f ../../k8s/mongodb/networkpolicy.yaml
```

Yandex Cloud Managed Kubernetes uses Calico by default, which enforces
`NetworkPolicy` resources natively -- no extra CNI plugin installation
needed.

## 8. Streamlit app

```bash
docker build -f ../../streamlit_app/Dockerfile -t <your-registry>/kubernetes-demo/streamlit:1.0.0 ../..
docker push <your-registry>/kubernetes-demo/streamlit:1.0.0
# update image: in k8s/streamlit/deployment.yaml to the pushed tag, then:
kubectl apply -f ../../k8s/streamlit/
```

Push to Yandex Container Registry:

```bash
yc container registry create --name kubernetes-demo
yc container registry configure-docker
docker tag kubernetes-demo/streamlit:1.0.0 cr.yandex/<registry-id>/streamlit:1.0.0
docker push cr.yandex/<registry-id>/streamlit:1.0.0
```

## 9. Monitoring

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace \
  -f ../../monitoring/prometheus-values.yaml
kubectl apply -f ../../k8s/airflow/servicemonitor.yaml
```

Import `../../monitoring/grafana-dashboard-kubernetes-demo.json` into
Grafana (`kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3000:80`).

## 10. DAG deployment

The Airflow chart is configured with `dags.gitSync` pointing at this fork's
`kubernetes-demo` branch, `kubernetes-demo/dags` subpath (see
`../../airflow/values.yaml`). Once the branch is pushed, git-sync picks up
`cbr_rates_dag.py` automatically -- no manual DAG upload needed.

## 11. Local validation tools

Some CI tools (`helm`, `yamllint`, `trivy`, `gitleaks`, a JVM for real
PySpark execution) may not be preinstalled in every environment. Install
them with your OS package manager / `asdf` / the tool's official installer;
`scripts/validate_k8s.sh` skips gracefully with a clear message when a tool
is missing rather than failing silently.

## 12. Teardown

```bash
helm uninstall airflow -n airflow
helm uninstall kube-prometheus-stack -n monitoring
kubectl delete -f ../../k8s/
yc managed-kubernetes cluster delete kubernetes-demo
```

Delete the cluster promptly after grading/demo to avoid ongoing Yandex
Cloud charges.

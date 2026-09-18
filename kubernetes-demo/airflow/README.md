# Airflow deployment (kubernetes-demo)

Deployed with the official Apache Airflow Helm chart, pinned to a stable
release, running in HA mode on Yandex Cloud Managed Kubernetes.

## Pinned versions

| Component | Version |
| --- | --- |
| Apache Airflow Helm chart | `1.15.0` |
| Airflow image | `apache/airflow:2.9.3-python3.11` |
| Python | 3.11 |
| Java (Spark tasks) | 17 (Temurin) |
| PySpark | 3.5.1 |
| MongoDB Spark Connector | 10.3.0 |

No `latest` tags are used anywhere.

## Install

```bash
helm repo add apache-airflow https://airflow.apache.org
helm repo update

kubectl create namespace airflow --dry-run=client -o yaml | kubectl apply -f -

# Create the Secret first -- see ../k8s/secrets/secret.example.yaml and
# ../docs/cloud/README.md "Secrets" section. Never commit the real Secret.
kubectl apply -n airflow -f ../k8s/secrets/airflow-secrets.yaml   # created by you, gitignored

helm upgrade --install airflow apache-airflow/airflow \
  --namespace airflow \
  --version 1.15.0 \
  -f values.yaml \
  -f values-prod.yaml   # or values-dev.yaml for a lighter local/dev cluster
```

## HA configuration

- `webserver.replicas: 2` (values.yaml) -- meets the "minimum 2 replicas" requirement.
- `scheduler.replicas: 2` with `executor: KubernetesExecutor` -- each DAG task
  runs in its own pod, so scheduler HA does not depend on a shared local
  worker pool.
- `postgresql.enabled: false` in `values-prod.yaml` -- production points at an
  external, HA-managed Postgres via the `data.metadataConnection` secret,
  not the chart's bundled single-instance Postgres.
- `redis` is not required under `KubernetesExecutor` (no Celery queue).

## Executor choice

`KubernetesExecutor` was chosen over `CeleryExecutor` because:
- No persistent worker pool to keep patched/HA -- Kubernetes schedules a pod
  per task and reclaims it when done.
- Matches the "Kubernetes-native" requirement of the assignment: task
  isolation, resource limits, and security context are configured per pod
  via `pod_template_file` / `KubernetesPodOperator`, not chart-wide worker
  settings.

## Config precedence

- `values.yaml` -- shared, environment-agnostic base (image tag, executor,
  HA replica counts, security context, resources shape).
- `values-dev.yaml` -- smaller resource requests/limits, single Postgres,
  `LOG_LEVEL=DEBUG`, for a lightweight cluster.
- `values-prod.yaml` -- HA replica counts, larger resources, external
  Postgres and Secret references. Contains **placeholders only** -- no real
  secret values.

## Where to look for problems

- DAG logs: Airflow UI -> DAG -> task -> Logs, or `kubectl logs` on the task pod.
- Scheduler/webserver logs: `kubectl logs -n airflow deploy/airflow-scheduler` / `deploy/airflow-webserver`.
- Metrics: see `../monitoring/README.md` and `k8s/airflow/servicemonitor.yaml`.

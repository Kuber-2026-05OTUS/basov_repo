# Checklist

Self-assessment against the assignment's requirements. `Verified` means
proven in this sandbox (tests ran, files exist, lint passed). `Not
verified` means it requires a real Yandex Cloud account, real MongoDB, or a
tool unavailable in the build sandbox -- see `../../IMPLEMENTATION_REPORT.md`
for details on each.

| # | Requirement | Status | Evidence |
| --- | --- | --- | --- |
| 1 | HA Apache Airflow via official Helm chart, pinned versions | Written, not verified | `airflow/values*.yaml`, `airflow/README.md` |
| 2 | DAG: fetch USD/EUR/CNY from CBR, retries, validation, idempotent upsert | Verified (unit+integration tests) | `dags/cbr_rates_dag.py`, `src/cbr_client.py`, `tests/unit/test_cbr_client.py`, `tests/integration/` |
| 3 | PySpark processing, explicit schema, MongoDB Spark Connector write | Written, not verified (no JVM/Spark cluster in sandbox) | `src/spark_job.py` |
| 4 | MongoDB persistence, unique (date, currency) index | Verified (mongomock tests) | `src/mongo_repository.py`, `tests/unit/test_mongo_repository.py` |
| 5 | Kubernetes Secrets, no real secrets committed, secret.example.yaml | Verified (static secret scan test) | `k8s/secrets/secret.example.yaml`, `tests/security/test_no_hardcoded_secrets.py` |
| 6 | RBAC least privilege, no cluster-admin | Verified (manifest test) | `k8s/rbac/*.yaml`, `tests/k8s/test_manifests.py::test_no_cluster_admin_or_cluster_role_bindings` |
| 7 | SecurityContext: non-root, no privileged, drop ALL capabilities | Verified (manifest test) | `tests/k8s/test_manifests.py` |
| 8 | NetworkPolicy: default-deny + explicit allow | Verified (manifest presence test) | `k8s/*/networkpolicy.yaml` |
| 9 | Resource requests/limits on every container | Verified (manifest test) | `tests/k8s/test_manifests.py::test_containers_declare_resource_limits` |
| 10 | Health probes (liveness/readiness/startup) | Written, not verified on a live cluster | `k8s/streamlit/deployment.yaml`, `airflow/values.yaml` |
| 11 | Streamlit: CPU-only, 0.0.0.0:8501, Service:8501, 2 replicas, current rates + naive forecast | Verified (unit tests for forecast logic; UI not screenshotted against real data) | `streamlit_app/app.py`, `src/forecast.py`, `tests/unit/test_forecast.py` |
| 12 | Forecast: 5-working-day average, "insufficient data" message, no ML claims | Verified (unit tests) | `src/forecast.py` |
| 13 | Prometheus/Grafana monitoring incl. Airflow metrics | Written, not verified (no live Prometheus instance) | `monitoring/`, `k8s/airflow/servicemonitor.yaml` |
| 14 | Structured logging, no secrets logged | Verified (formatter redacts sensitive keys) | `src/logging_config.py` |
| 15 | Error handling for CBR/Mongo failures | Verified (unit tests raise typed exceptions) | `src/cbr_client.py`, `src/mongo_repository.py` |
| 16 | Helm values.yaml / values-dev.yaml / values-prod.yaml | Written, `helm lint` not run (helm unavailable in sandbox) | `airflow/values*.yaml` |
| 17 | CI: ruff, pytest, mypy, yamllint, helm lint, Trivy, pip-audit, Bandit, gitleaks | Workflow written, not executed by GitHub Actions yet | `.github/workflows/kubernetes-demo-ci.yml` |
| 18 | Full test suite: unit/integration/security/k8s | Verified (ran locally, see IMPLEMENTATION_REPORT.md) | `tests/` |
| 19 | README with architecture diagram, demo video script | Verified (file exists) | `README.md` |
| 20 | docs/cloud/README.md admin guide | Verified (file exists) | `docs/cloud/README.md` |
| 21 | No `latest` tags anywhere | Verified (manifest test + Dockerfile pin) | `tests/k8s/test_manifests.py::test_no_latest_image_tags` |
| 22 | No root/privileged containers, no GPU | Verified | `tests/k8s/test_manifests.py`, no GPU resource requests anywhere in `k8s/` |

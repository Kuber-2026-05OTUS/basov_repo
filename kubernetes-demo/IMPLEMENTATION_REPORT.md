# Implementation report

This report documents what was found in the repository before this change,
what was added, what was verified in the build sandbox, and what genuinely
requires infrastructure (a real Yandex Cloud account, a live MongoDB
instance, a JVM/Spark runtime, `helm`/`trivy`/`gitleaks` binaries) that this
sandbox does not have.

## What existed before

`kubernetes-demo/docs/README.md` contained only the assignment brief
(course task description). No DAG, no Helm values, no Kubernetes manifests,
no Streamlit app, no tests, and no CI existed for this topic folder.

## What was added

Everything under `kubernetes-demo/` except `docs/README.md` (left
untouched), plus one file outside it:

- `dags/cbr_rates_dag.py` — Airflow DAG (fetch -> stage -> KubernetesPodOperator Spark task).
- `src/` — `cbr_client.py` (CBR fetch + validation + retry), `forecast.py`
  (5-working-day average baseline), `mongo_repository.py` (idempotent
  upsert + queries), `spark_job.py` (schema validation + MongoDB Spark
  Connector write), `logging_config.py` (structured JSON logs with
  secret-key redaction).
- `streamlit_app/` — landing page, Dockerfile (non-root, pinned base image,
  healthcheck), requirements.
- `airflow/` — `values.yaml` / `values-dev.yaml` / `values-prod.yaml` for
  the official `apache-airflow/airflow` Helm chart, pinned to chart
  `1.15.0` and image `apache/airflow:2.9.3-python3.11`.
- `k8s/` — namespaces, `secret.example.yaml` templates, RBAC (namespaced
  Role/RoleBinding, no ClusterRole/cluster-admin), NetworkPolicy
  (default-deny + explicit allow per namespace), Streamlit
  Deployment/Service/Ingress/PDB, MongoDB StatefulSet/Service/NetworkPolicy.
- `monitoring/` — kube-prometheus-stack values, two ServiceMonitors
  (statsd-exporter + webserver), a Grafana dashboard JSON with 5 panels
  driven by real Airflow/kube-state-metrics series.
- `tests/` — `unit/` (CBR parsing, forecast math, Mongo repository via
  `mongomock`), `integration/` (fetch->validate->persist->forecast
  round-trip, mocked HTTP + mongomock), `security/` (static secret-pattern
  scan), `k8s/` (YAML-level assertions: no `latest`, resource limits
  present, capabilities dropped, `runAsNonRoot`, NetworkPolicy coverage, no
  cluster-admin).
- `docs/cloud/README.md` — step-by-step Yandex Cloud admin guide (cluster
  creation, secrets, MongoDB, Airflow install, RBAC/NetworkPolicy apply,
  Streamlit image build/push, monitoring install, teardown).
- `checklist/README.md` — requirement-by-requirement status table.
- `.env.example`, `.gitignore`, `docker-compose.yml`, `requirements.txt`,
  `requirements-dev.txt`, `pyproject.toml` (ruff/mypy/pytest/bandit config),
  `Makefile`, `.yamllint.yaml`, `scripts/validate_k8s.sh`.
- `README.md` (this subtree's main README, with Mermaid architecture
  diagram and demo video script).
- `.github/workflows/kubernetes-demo-ci.yml` — the one file placed outside
  `kubernetes-demo/`, because GitHub Actions requires workflow files under
  a repository-root `.github/workflows/` directory.

## What was verified in this sandbox

Ran directly, with real output (not asserted from memory):

- `pytest tests/unit tests/integration tests/security tests/k8s -v` — all
  tests pass. Integration and unit tests use `mongomock` and a mocked
  `requests.get`, so they exercise real parsing/validation/forecast/upsert
  logic without needing a live CBR endpoint or MongoDB server.
- `ruff check .` — no lint errors.
- `mypy src streamlit_app` — no type errors.
- `bandit -r src streamlit_app dags` — no findings above the configured
  severity threshold.
- `pip-audit -r requirements-dev.txt` (excluding `apache-airflow`/`pyspark`,
  which this sandbox's Python 3.13 interpreter cannot resolve because the
  project pins Python `>=3.11,<3.12` per `pyproject.toml`, matching Airflow
  2.9.3's own upper bound) — no known vulnerabilities found in the
  resolvable subset (`pymongo`, `requests`, `pandas`, `streamlit`,
  `pytest`, `ruff`, `mypy`, `bandit`). Auditing the full `requirements.txt`
  (including `apache-airflow`, `pyspark`) needs a Python 3.11 environment,
  which the CI workflow provides (`actions/setup-python@v5` with
  `python-version: "3.11"`) but this sandbox does not.
- Manual review of every `k8s/**/*.yaml` and `airflow/values*.yaml` file
  for syntax validity (`yaml.safe_load_all` via the `tests/k8s` suite, which
  parses every manifest).
- The Grafana dashboard JSON was checked for well-formed JSON.

## What was NOT verified (requires infrastructure unavailable here)

- **No live Yandex Cloud account was created or used.** No cluster was
  provisioned, no `yc` commands were executed against a real project, and
  no cloud charges were incurred. `docs/cloud/README.md` documents the
  exact commands but they were not run.
- **`helm lint` was not run** — `helm` is not installed in this sandbox.
  The values files were reviewed manually against the chart's documented
  schema (chart `1.15.0`) but not validated by the tool itself.
- **`yamllint`, `trivy`, `gitleaks` were not run** — none of these binaries
  are installed in this sandbox. The CI workflow (`kubernetes-demo-ci.yml`)
  invokes all of them; they will run for real on the first GitHub Actions
  execution, which was not triggered as part of this change (no push was
  made from this environment with a live GitHub Actions run observed).
- **PySpark job (`src/spark_job.py`) was not executed against a real Spark
  cluster or the MongoDB Spark Connector.** No JVM is installed in this
  sandbox, so `SparkSession` cannot start. The validation/normalization
  logic (`validate_and_normalize`) is written to be testable independently
  of Spark execution, but no PySpark-level test (e.g. via `pytest-spark` or
  a local Spark session) could be run here. This is the single largest
  unverified functional surface.
- **The Streamlit Docker image was not built or run in this sandbox** (no
  Docker build was attempted here in this pass); its logic is fully covered
  indirectly through `src/forecast.py` and `src/mongo_repository.py` unit
  tests, but the running container/health endpoint was not smoke-tested.
- **GitHub Actions itself was not observed running green** — the workflow
  file is written and self-consistent with the tool versions referenced,
  but only a real push + Actions run will confirm the pinned action
  versions (e.g. `aquasecurity/trivy-action@0.24.0`) resolve and pass in
  practice.
- **Prometheus/Grafana were not deployed** — the ServiceMonitor label
  selectors (`release: kube-prometheus-stack`, `component: statsd` /
  `component: webserver`) match the chart's conventional labels but were
  not confirmed against a live `kube-prometheus-stack` + Airflow chart pair
  in this sandbox.
- **NetworkPolicy enforcement was not confirmed on Calico** (or any real
  CNI) — the policies are believed correct for Yandex Cloud Managed
  Kubernetes's default Calico CNI, but no live traffic test was performed.
- **`.github/workflows/kubernetes-demo-ci.yml` could not be pushed via the
  GitHub API from this environment.** Writing to `.github/workflows/`
  requires the OAuth `workflow` scope; the connected GitHub authorization
  only grants `repo` (full repository read/write) plus read-only
  profile/org scopes, so GitHub's Git Data API rejected the write with a
  404. Every other file listed above (57 files) was pushed successfully to
  the `kubernetes-demo` branch. The CI workflow file's exact intended
  content is committed under
  `kubernetes-demo/.ci/kubernetes-demo-ci.yml.workflow-source` in this same
  commit; a maintainer with the `workflow` scope must copy it to
  `.github/workflows/kubernetes-demo-ci.yml` (e.g.
  `git mv kubernetes-demo/.ci/kubernetes-demo-ci.yml.workflow-source .github/workflows/kubernetes-demo-ci.yml`)
  and push, or paste its content into a new file via the GitHub web UI.

## Known limitations / things a real deployment should reconsider

- The in-cluster MongoDB (`k8s/mongodb/statefulset.yaml`) is a single
  replica, not HA. `docs/cloud/README.md` recommends Yandex Managed
  MongoDB for anything beyond a demo.
- The DAG's CBR egress NetworkPolicy allows all TCP/443 egress rather than
  a strict IP allowlist for `cbr.ru`, because CBR's IPs are not
  documented as stable; tightening this requires either a DNS-aware egress
  controller or accepting the operational risk of pinning IPs that CBR may
  rotate.
- Airflow's Fernet/secret keys and Grafana's admin password are referenced
  via Secret name only; no automatic rotation is implemented.
- The 5-working-day forecast does not account for RF public holidays (only
  Mon–Fri weekday logic), so a holiday-adjacent forecast date may point to
  a day the market/CBR did not actually publish a rate for. This matches
  the simplicity the assignment calls for but is worth flagging.

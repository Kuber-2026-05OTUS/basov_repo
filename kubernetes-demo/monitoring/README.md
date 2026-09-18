# Monitoring

## Metrics chain

```
Airflow (StatsD emitter)
      |
      v
statsd-exporter sidecar  --(Prometheus text format, :9102/metrics)-->
      |
      v
Prometheus (kube-prometheus-stack, scraping via k8s/airflow/servicemonitor.yaml)
      |
      v
Grafana dashboard (grafana-dashboard-kubernetes-demo.json)
```

Airflow's native metrics are emitted over StatsD (`config.metrics.statsd_on:
"True"` is the chart default once `statsd.enabled: true` is set -- see
`../airflow/values.yaml`). The bundled `statsd-exporter` sidecar converts
them to Prometheus's text exposition format; nothing in this pipeline
fabricates or hand-writes metric values.

## Install kube-prometheus-stack

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace \
  -f prometheus-values.yaml
```

Then apply the ServiceMonitors:

```bash
kubectl apply -f ../k8s/airflow/servicemonitor.yaml
```

## Dashboard

Import `grafana-dashboard-kubernetes-demo.json` into Grafana (Dashboards ->
Import -> Upload JSON). Panels:

1. DAG run success/failure rate (`airflow_dag_run_duration_success_count`,
   `airflow_dag_run_duration_failed_count`)
2. Task duration p95 (`airflow_task_duration`)
3. Scheduler heartbeat / liveness (`airflow_scheduler_heartbeat`)
4. Webserver HTTP 5xx rate (`airflow_http_response_code`)
5. Pod restarts for `airflow` and `data-platform` namespaces
   (`kube_pod_container_status_restarts_total`, from kube-state-metrics,
   already bundled in kube-prometheus-stack)

## What is NOT included

- No custom exporter that fabricates business metrics (e.g. "current USD
  rate" as a Prometheus gauge) -- that would blur the line between
  monitoring and the actual data pipeline. Business data lives in MongoDB
  and is shown by the Streamlit app; monitoring covers platform health only.
- Alertmanager rules are not included; add them once real on-call routing
  (Slack/Telegram/email) is decided -- see `docs/cloud/README.md` for the
  placeholder.

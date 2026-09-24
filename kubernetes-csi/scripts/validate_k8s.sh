#!/usr/bin/env bash
# Static validation for kubernetes-csi manifests. Skips a tool gracefully
# (with a clear message) instead of failing silently when it isn't
# installed -- mirrors kubernetes-demo/scripts/validate_k8s.sh.
set -euo pipefail
cd "$(dirname "$0")/.."

status=0

echo "== yamllint =="
if command -v yamllint >/dev/null 2>&1; then
  yamllint -c ../.yamllint.yaml . || status=1
else
  echo "yamllint not installed -- skipping (install with: pip install yamllint)"
fi

echo "== kubeconform (schema validation) =="
if command -v kubeconform >/dev/null 2>&1; then
  find k8s -name '*.yaml' -print0 | xargs -0 kubeconform -strict -summary \
    -schema-location default \
    -schema-location 'https://raw.githubusercontent.com/yannh/kubernetes-json-schema/master/{{.NormalizedKubernetesVersion}}-standalone{{.StrictSuffix}}/{{.ResourceKind}}{{.KindSuffix}}.json' \
    || status=1
else
  echo "kubeconform not installed -- skipping (install: https://github.com/yannh/kubeconform)"
fi

echo "== python manifest checks =="
if command -v python3 >/dev/null 2>&1; then
  python3 -m pytest tests -q || status=1
else
  echo "python3 not available -- skipping pytest manifest checks"
fi

exit $status

"""Structural sanity checks for the kubernetes-debug manifests.

These confirm the YAML is well-formed and matches the assignment's
constraints (pinned distroless image, no exec-based probes, resources
set). They cannot confirm live debugging behavior -- see
IMPLEMENTATION_REPORT.md for why that needs a real cluster.
"""
import pathlib

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _load_all(path):
    with open(path, encoding="utf-8") as f:
        return [doc for doc in yaml.safe_load_all(f) if doc]


def test_all_manifests_parse_as_valid_yaml():
    for path in (ROOT / "k8s").glob("*.yaml"):
        docs = _load_all(path)
        assert docs, f"{path} produced no documents"
        for doc in docs:
            assert "apiVersion" in doc, f"{path}: missing apiVersion"
            assert "kind" in doc, f"{path}: missing kind"


def test_target_pod_uses_pinned_distroless_image():
    docs = _load_all(ROOT / "k8s" / "pod-distroless-nginx.yaml")
    pod = next(d for d in docs if d["kind"] == "Pod")
    image = pod["spec"]["containers"][0]["image"]
    assert image.startswith("kyos0109/nginx-distroless:")
    assert not image.endswith(":latest"), "must pin a concrete tag, not latest"


def test_target_pod_has_no_exec_probes():
    # kyos0109/nginx-distroless has no shell, so any exec-based probe would
    # fail outright -- only network probes are valid here.
    docs = _load_all(ROOT / "k8s" / "pod-distroless-nginx.yaml")
    pod = next(d for d in docs if d["kind"] == "Pod")
    container = pod["spec"]["containers"][0]
    for probe_name in ("readinessProbe", "livenessProbe"):
        probe = container.get(probe_name)
        if probe:
            assert "exec" not in probe, f"{probe_name} must not use exec on a distroless image"


def test_target_pod_declares_resources():
    docs = _load_all(ROOT / "k8s" / "pod-distroless-nginx.yaml")
    pod = next(d for d in docs if d["kind"] == "Pod")
    resources = pod["spec"]["containers"][0]["resources"]
    assert "requests" in resources and "limits" in resources


def test_service_selector_matches_pod_labels():
    docs = _load_all(ROOT / "k8s" / "pod-distroless-nginx.yaml")
    pod = next(d for d in docs if d["kind"] == "Pod")
    svc = next(d for d in docs if d["kind"] == "Service")
    assert svc["spec"]["selector"] == pod["metadata"]["labels"]


def test_debug_session_script_covers_required_steps():
    script = (ROOT / "scripts" / "debug_session.sh").read_text(encoding="utf-8")
    required_snippets = [
        "kubectl apply",
        "kubectl debug -it distroless-nginx",
        "--target=nginx",
        "ls -la /proc/1/root/etc/nginx",
        "tcpdump -nn -i any -e port 80",
        "strace -p 1",
        "--profile=sysadmin",
        "kubectl debug node/",
        "/var/log/pods/",
    ]
    for snippet in required_snippets:
        assert snippet in script, f"debug_session.sh is missing required step: {snippet}"

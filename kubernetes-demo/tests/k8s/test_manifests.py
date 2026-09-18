"""Static assertions over the Kubernetes YAML manifests in this subtree.

Does not require a running cluster or `kubectl`/`helm` -- parses the YAML
directly and checks the security/resource invariants the assignment
requires (no privileged/root containers, no `latest` tags, resource
limits present, NetworkPolicies present).
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import yaml

K8S_ROOT = Path(__file__).resolve().parents[1].parent / "k8s"


def _iter_manifests() -> Iterator[dict[str, Any]]:
    for path in sorted(K8S_ROOT.rglob("*.yaml")):
        for doc in yaml.safe_load_all(path.read_text(encoding="utf-8")):
            if doc:
                yield doc


def _iter_containers(doc: dict[str, Any]) -> Iterator[dict[str, Any]]:
    spec = doc.get("spec", {})
    template = spec.get("template", {}) if isinstance(spec, dict) else {}
    pod_spec = template.get("spec", {}) if isinstance(template, dict) else {}
    for key in ("containers", "initContainers"):
        for container in pod_spec.get(key, []) or []:
            yield container
    # StatefulSet/Deployment share the same shape; also handle bare Pod specs.
    if doc.get("kind") == "Pod":
        for container in spec.get("containers", []) or []:
            yield container


def test_no_latest_image_tags() -> None:
    offenders = []
    for doc in _iter_manifests():
        for container in _iter_containers(doc):
            image = container.get("image", "")
            if image.endswith(":latest") or (":" not in image and image):
                offenders.append((doc.get("kind"), doc.get("metadata", {}).get("name"), image))
    assert not offenders, f"Found `latest`/untagged images: {offenders}"


def test_containers_declare_resource_limits() -> None:
    offenders = []
    for doc in _iter_manifests():
        for container in _iter_containers(doc):
            resources = container.get("resources", {})
            if not resources.get("limits") or not resources.get("requests"):
                offenders.append(
                    (doc.get("kind"), doc.get("metadata", {}).get("name"), container.get("name"))
                )
    assert not offenders, f"Containers missing resource requests/limits: {offenders}"


def test_containers_drop_all_capabilities_and_no_privilege_escalation() -> None:
    offenders = []
    for doc in _iter_manifests():
        for container in _iter_containers(doc):
            security_context = container.get("securityContext", {})
            capabilities = security_context.get("capabilities", {})
            if "ALL" not in (capabilities.get("drop") or []):
                offenders.append(
                    (doc.get("kind"), doc.get("metadata", {}).get("name"), container.get("name"))
                )
            if security_context.get("allowPrivilegeEscalation") is not False:
                offenders.append(
                    (doc.get("kind"), doc.get("metadata", {}).get("name"), container.get("name"))
                )
            if security_context.get("privileged"):
                offenders.append(
                    (doc.get("kind"), doc.get("metadata", {}).get("name"), container.get("name"))
                )
    assert not offenders, f"Containers with unsafe securityContext: {offenders}"


def test_pod_specs_run_as_non_root() -> None:
    offenders = []
    for doc in _iter_manifests():
        spec = doc.get("spec", {})
        template = spec.get("template", {}) if isinstance(spec, dict) else {}
        pod_spec = template.get("spec", {}) if isinstance(template, dict) else {}
        if not pod_spec.get("containers"):
            continue
        if pod_spec.get("securityContext", {}).get("runAsNonRoot") is not True:
            offenders.append((doc.get("kind"), doc.get("metadata", {}).get("name")))
    assert not offenders, f"Pod specs not enforcing runAsNonRoot: {offenders}"


def test_network_policies_exist_for_each_namespace_with_workloads() -> None:
    namespaces_with_policies = set()
    namespaces_with_workloads = set()
    for doc in _iter_manifests():
        namespace = doc.get("metadata", {}).get("namespace")
        if doc.get("kind") == "NetworkPolicy" and namespace:
            namespaces_with_policies.add(namespace)
        if doc.get("kind") in {"Deployment", "StatefulSet"} and namespace:
            namespaces_with_workloads.add(namespace)
    missing = namespaces_with_workloads - namespaces_with_policies
    assert not missing, f"Namespaces with workloads but no NetworkPolicy: {missing}"


def test_no_cluster_admin_or_cluster_role_bindings() -> None:
    for doc in _iter_manifests():
        if doc.get("kind") in {"ClusterRole", "ClusterRoleBinding"}:
            role_ref = doc.get("roleRef", {})
            assert role_ref.get("name") != "cluster-admin", "cluster-admin must never be bound"

"""Static checks against the kubernetes-csi manifests.

These do not require a live cluster or a real Yandex Cloud account -- they
parse the YAML and assert structural properties the assignment calls for
(storage class provisioner, PVC access mode/class, secret keys, workload
hardening). See ../IMPLEMENTATION_REPORT.md for what still needs a real
cluster to verify (the driver actually mounting, and writes landing in the
Object Storage bucket).
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

K8S_DIR = Path(__file__).resolve().parents[1] / "k8s"


def load(name: str):
    with open(K8S_DIR / name, encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_namespace_manifest():
    doc = load("namespace.yaml")
    assert doc["kind"] == "Namespace"
    assert doc["metadata"]["name"] == "csi-s3-demo"


def test_secret_example_has_required_keys_and_no_real_secret():
    doc = load("secret.example.yaml")
    assert doc["kind"] == "Secret"
    keys = doc["stringData"]
    for required in ("accessKeyID", "secretAccessKey", "endpoint"):
        assert required in keys
    # This is an example file: values must be placeholders, never real keys.
    assert keys["accessKeyID"].startswith("<") and keys["accessKeyID"].endswith(">")
    assert keys["secretAccessKey"].startswith("<") and keys["secretAccessKey"].endswith(">")


def test_storageclass_uses_csi_s3_provisioner_and_references_secret():
    doc = load("storageclass.yaml")
    assert doc["kind"] == "StorageClass"
    assert doc["provisioner"] == "ru.yandex.s3.csi"
    params = doc["parameters"]
    # autoProvisioning: no fixed `bucket` parameter -- csi-s3 creates one per volume
    assert "bucket" not in params
    for key in (
        "csi.storage.k8s.io/provisioner-secret-name",
        "csi.storage.k8s.io/node-publish-secret-name",
    ):
        assert params[key] == "csi-s3-secret"


def test_pvc_uses_storageclass_and_dynamic_provisioning():
    doc = load("pvc.yaml")
    assert doc["kind"] == "PersistentVolumeClaim"
    spec = doc["spec"]
    assert spec["storageClassName"] == "csi-s3"
    assert "ReadWriteMany" in spec["accessModes"]
    # Dynamic provisioning: no pre-bound volumeName / selector.
    assert "volumeName" not in spec
    assert "selector" not in spec


def test_deployment_mounts_pvc_at_arbitrary_path():
    doc = load("deployment.yaml")
    assert doc["kind"] == "Deployment"
    pod_spec = doc["spec"]["template"]["spec"]
    volumes = {v["name"]: v for v in pod_spec["volumes"]}
    assert "s3-data" in volumes
    assert volumes["s3-data"]["persistentVolumeClaim"]["claimName"] == "csi-s3-pvc"

    container = pod_spec["containers"][0]
    mounts = {m["name"]: m for m in container["volumeMounts"]}
    assert "s3-data" in mounts
    assert mounts["s3-data"]["mountPath"] == "/data/s3"


def test_deployment_is_hardened():
    doc = load("deployment.yaml")
    pod_spec = doc["spec"]["template"]["spec"]
    pod_sc = pod_spec["securityContext"]
    assert pod_sc["runAsNonRoot"] is True

    container = pod_spec["containers"][0]
    csc = container["securityContext"]
    assert csc["allowPrivilegeEscalation"] is False
    assert csc["capabilities"]["drop"] == ["ALL"]
    assert "requests" in container["resources"]
    assert "limits" in container["resources"]


def test_no_latest_image_tags():
    for name in ("deployment.yaml",):
        doc = load(name)
        for container in doc["spec"]["template"]["spec"]["containers"]:
            image = container["image"]
            assert ":" in image, f"{image} has no explicit tag"
            assert not image.endswith(":latest"), f"{image} uses the latest tag"


def test_all_manifests_parse_as_valid_yaml():
    for path in K8S_DIR.glob("*.yaml"):
        with open(path, encoding="utf-8") as f:
            docs = list(yaml.safe_load_all(f))
        assert docs, f"{path} produced no YAML documents"
        for doc in docs:
            assert "kind" in doc, f"{path} missing 'kind'"
            assert "apiVersion" in doc, f"{path} missing 'apiVersion'"

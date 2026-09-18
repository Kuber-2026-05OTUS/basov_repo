# Checklist

Self-assessment against `docs/README.md`'s requirements. `Verified` means
proven in this sandbox (structural/static tests, files exist). `Not
verified` means it needs a real Yandex Cloud account and a live Managed
Kubernetes cluster -- see `../IMPLEMENTATION_REPORT.md`.

| # | Requirement | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Managed Kubernetes cluster in Yandex Cloud (any node config) | Documented, not created | `docs/cloud/README.md` §3 |
| 2 | Object Storage bucket for mounting into pods | Documented (auto-provisioned per volume by design; a pre-created bucket is also documented as an option) | `docs/cloud/README.md` §3, `k8s/storageclass.yaml` |
| 3 | IAM service account with bucket access rights + generated static access key | Documented (role `storage.editor`, `yc iam` commands) | `docs/cloud/README.md` §4 |
| 4 | Secret with the access keys, manifest attached | Verified structurally (required keys present, values are placeholders, not real secrets) | `k8s/secret.example.yaml`, `tests/test_manifests.py::test_secret_example_has_required_keys_and_no_real_secret` |
| 5 | StorageClass manifest, attached | Verified structurally (provisioner `ru.yandex.s3.csi`, references the secret) | `k8s/storageclass.yaml`, `tests/test_manifests.py::test_storageclass_uses_csi_s3_provisioner_and_references_secret` |
| 6 | CSI driver installed from the upstream repository | Documented (Helm chart + manual manifest install), not run against a live cluster | `docs/cloud/README.md` §5, `helm/csi-s3-values.yaml` |
| 7 | PVC manifest using the StorageClass with autoProvisioning, attached | Verified structurally (no fixed `bucket`, no `volumeName`/`selector` -- dynamic provisioning) | `k8s/pvc.yaml`, `tests/test_manifests.py::test_pvc_uses_storageclass_and_dynamic_provisioning` |
| 8 | Pod/Deployment manifest mounting the PVC at an arbitrary path, attached | Verified structurally (mounts `csi-s3-pvc` at `/data/s3`) | `k8s/deployment.yaml`, `tests/test_manifests.py::test_deployment_mounts_pvc_at_arbitrary_path` |
| 9 | Pod writes to the mounted directory; files are confirmed to land in Object Storage | Written (heartbeat writer loop), **not verified** -- needs a live cluster + bucket to confirm objects actually appear | `k8s/deployment.yaml`, `README.md` demo script step 4-5 |
| 10 | No `latest` image tags in manifests authored here | Verified | `tests/test_manifests.py::test_no_latest_image_tags` |
| 11 | Workload hardening (non-root, dropped capabilities, resource limits) beyond the assignment's letter but consistent with the rest of the project | Verified | `k8s/deployment.yaml`, `tests/test_manifests.py::test_deployment_is_hardened` |
| 12 | All manifests are syntactically valid Kubernetes YAML | Verified | `tests/test_manifests.py::test_all_manifests_parse_as_valid_yaml` |

## Known limitation: the driver's own node plugin needs `privileged`

The upstream `csi-s3` node DaemonSet (not authored in this repo -- it comes
from the official Helm chart / `deploy/kubernetes/*.yaml`) runs privileged
in `kube-system` because FUSE mounting requires it. That is an upstream
constraint of every FUSE-based CSI driver, not something this folder's own
manifests (`k8s/*.yaml`) do -- those stay non-root, non-privileged, with
capabilities dropped.

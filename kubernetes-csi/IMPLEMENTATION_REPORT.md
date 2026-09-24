# Implementation report -- kubernetes-csi

Honest account of what was actually verified while preparing this folder,
versus what is written correctly but unverified because there is no live
Yandex Cloud account or Kubernetes cluster available in this build
sandbox.

## Verified in this sandbox

- All YAML manifests under `k8s/` parse as valid YAML and contain the
  required `apiVersion`/`kind` (`tests/test_manifests.py::test_all_manifests_parse_as_valid_yaml`).
- `k8s/storageclass.yaml` uses the exact upstream provisioner name
  `ru.yandex.s3.csi` and references the `csi-s3-secret` secret for every
  CSI secret slot the driver checks (provisioner/controller-publish/node-stage/node-publish).
- `k8s/pvc.yaml` requests the `csi-s3` storage class with `ReadWriteMany`
  and no `volumeName`/`selector`/fixed `bucket` -- i.e. it is wired for
  dynamic (auto-) provisioning, not static/pre-bound provisioning.
- `k8s/secret.example.yaml` contains only placeholder values (`<...>`),
  confirmed programmatically so no real credential can silently end up in
  this file.
- `k8s/deployment.yaml` mounts `csi-s3-pvc` at `/data/s3`, runs as a
  non-root user, drops all Linux capabilities, disables privilege
  escalation, sets a read-only root filesystem, and declares CPU/memory
  requests and limits. Pinned to `busybox:1.36.1`, not `latest`.
- `pytest tests` passes locally (8/8) against a `pyyaml`-only virtualenv --
  see the command output referenced in this repo's CI workflow.

## Written but NOT verified (needs a live Yandex Cloud account + cluster)

- That a real Managed Kubernetes cluster can be created with the exact `yc`
  commands in `docs/cloud/README.md` -- these follow the documented `yc`
  CLI syntax and the Yandex Cloud console flow, but were not executed
  against a real account.
- That the IAM service account, `storage.editor` role grant, and static
  access key creation steps work exactly as described -- not run.
- That the `csi-s3` driver (Helm chart or manual `kubectl apply` from
  `deploy/kubernetes/*.yaml` in the upstream repo) actually installs and
  its pods reach `Running` in `kube-system` on a real cluster.
- That `k8s/pvc.yaml` actually binds (`STATUS: Bound`) once the driver is
  running, and that a bucket is auto-created in Yandex Object Storage.
- That `csi-s3-writer`'s heartbeat writes are visible as real objects in
  the bucket via the Yandex Cloud console or `yc storage s3api
  list-objects-v2` -- this is the core acceptance criterion of the
  assignment ("Под в процессе работы должен производить запись в
  примонтированную директорию. Убедитесь, что файлы действительно
  сохраняются в ObjectStorage") and it requires a live cluster + bucket to
  confirm.
- That deleting the PVC deletes the auto-provisioned bucket
  (`reclaimPolicy: Delete`) -- documented driver behavior, not observed.
- `helm lint` / `kubeconform` against the manifests -- neither tool is
  installed in this sandbox; `scripts/validate_k8s.sh` skips them with an
  explicit message instead of pretending they ran.

## Why the driver's own manifests aren't reproduced here

The assignment says "Установите CSI driver из репозитория" (install the
CSI driver from the repository) -- it does not ask for the driver's
controller/DaemonSet manifests to be rewritten in this folder. Those come
from `yandex-cloud/k8s-csi-s3` (Helm chart or `deploy/kubernetes/*.yaml`)
and, unlike the workload in `k8s/deployment.yaml`, must run privileged in
`kube-system` for the GeeseFS FUSE mount to work -- that's an upstream
constraint of the driver, not a choice this repo makes. `docs/cloud/README.md`
§5 gives the exact install commands instead of vendoring a copy of the
upstream YAML that would drift out of date.

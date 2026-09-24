# Implementation report -- kubernetes-prod

## Why this folder ships scripts and a runbook instead of captured cluster output

The assignment's required evidence is `kubectl get nodes -o wide` output
captured before and after a real kubeadm cluster upgrade, running on 4
real VMs (9 for the bonus). That can only come from real virtual
machines with SSH access, a real containerd/kubeadm install, and a real
multi-hour-safe upgrade sequence -- it is fundamentally different from
the earlier assignments in this repo (`kubernetes-demo`, `kubernetes-csi`,
`kubernetes-debug`), which centered on Kubernetes manifests that at least
parse and structurally validate offline.

This build sandbox has no VMs, no SSH access to any host, and no
container runtime capable of running `kubeadm` realistically:

- `kubeadm init` needs a real systemd-managed OS with a real kubelet
  service, real cgroups, and (for multi-node) real networking between
  independent hosts -- not achievable with plain Docker containers here.
- The `kind`/Docker-in-Docker route already failed in this sandbox for
  the `kubernetes-debug` assignment (`mount sysfs: operation not
  permitted`, read-only `/lib/modules`) and would fail identically here;
  it also wouldn't exercise the actual assignment (kubeadm on VMs, not
  a Docker-simulated cluster).
- No cloud credentials or VM provisioning access exist in this sandbox to
  create real Yandex Cloud Compute instances.

Fabricating `kubectl get nodes -o wide` output would misrepresent this
sandbox as having built and upgraded a real cluster it never touched.
Instead, this folder ships exact, ordered, parameterized scripts for
every step and a Russian admin guide for provisioning the VMs, so running
them against real Yandex Cloud VMs reproduces the assignment faithfully.

## Verified in this sandbox

- Every shell script passes `bash -n` (syntax-checked, no execution).
- `scripts/00-common-prep.sh` through `04-upgrade-worker.sh` reference a
  single consistent `K8S_MINOR`/`TARGET_MINOR` variable convention, and
  the upgrade scripts never touch more than one worker node at a time
  (checked structurally in `tests/test_prod.py`).
- The pinned starting version (`K8S_MINOR=1.35`) is genuinely one minor
  below the latest actively supported series (`1.36`) as of the
  upstream Kubernetes release page checked while writing this
  (`kubernetes.io/releases`), matching the assignment's requirement to
  install one minor below current and then upgrade to current.
- `kubespray/inventory/hosts.yaml` parses as valid YAML and its
  `kube_control_plane`/`kube_node`/`etcd`/`k8s_cluster` groups match the
  group names kubespray's `cluster.yml` playbook actually expects (cross-
  checked against the kubespray sample inventory structure, not
  invented) -- 3 hosts under `kube_control_plane`/`etcd` and 2 under
  `kube_node`, satisfying the bonus task's minimum node counts.
- `pytest tests` passes locally.

## NOT verified -- needs real Yandex Cloud VMs

- That `00-common-prep.sh` actually installs containerd/kubeadm cleanly
  on a real Ubuntu 22.04 VM (package names/repo URLs are correct as of
  writing, per Kubernetes' own `pkgs.k8s.io` documentation, but apt
  repository contents can change).
- That `kubeadm init` succeeds and Flannel brings all nodes to `Ready` --
  the actual `kubectl get nodes -o wide` output the assignment asks for.
- That the upgrade sequence (`03-upgrade-master.sh` then
  `04-upgrade-worker.sh` per worker) actually moves the cluster from one
  minor to the next without breaking scheduling -- the second required
  `kubectl get nodes -o wide` output.
- That the kubespray playbook run against `kubespray/inventory/hosts.yaml`
  (with real IPs substituted) actually produces a 3-master/2-worker `Ready`
  cluster -- this needs 5 more real VMs and was not run.

To produce the real evidence the assignment asks for, provision the VMs
per `docs/cloud/README.md`, run the scripts in `scripts/` in order, and
capture the `kubectl get nodes -o wide` output at each required point.

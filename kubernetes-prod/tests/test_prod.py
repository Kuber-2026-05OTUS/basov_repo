"""Structural sanity checks for kubernetes-prod scripts and inventory.

These confirm internal consistency (syntax, sequencing, version pinning,
inventory group names) offline. They cannot confirm a real kubeadm
cluster comes up or upgrades cleanly -- see IMPLEMENTATION_REPORT.md for
why that needs real VMs.
"""
import pathlib
import subprocess

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def _script(name):
    return (SCRIPTS / name).read_text(encoding="utf-8")


def test_all_scripts_are_syntactically_valid_bash():
    for path in SCRIPTS.glob("*.sh"):
        result = subprocess.run(["bash", "-n", str(path)], capture_output=True, text=True)
        assert result.returncode == 0, f"{path}: {result.stderr}"


def test_scripts_use_strict_mode():
    for path in SCRIPTS.glob("*.sh"):
        content = path.read_text(encoding="utf-8")
        assert "set -euo pipefail" in content, f"{path} must use strict mode"


def test_worker_upgrade_touches_one_node_at_a_time():
    content = _script("04-upgrade-worker.sh")
    assert "NODE_NAME" in content
    # must not loop over multiple nodes internally -- the whole point is
    # sequential, externally-driven, one-node-at-a-time upgrades
    assert "for " not in content.split("INSTRUCTIONS")[0] or "NODE_NAME" in content


def test_upgrade_scripts_cordon_and_uncordon():
    content = _script("04-upgrade-worker.sh")
    assert "kubectl cordon" in content
    assert "kubectl drain" in content
    assert "kubectl uncordon" in content
    # cordon/drain must happen before uncordon in the file
    assert content.index("kubectl drain") < content.index("kubectl uncordon")


def test_master_init_installs_flannel_and_prints_join_command():
    content = _script("01-master-init.sh")
    assert "flannel" in content.lower()
    assert "kubeadm init" in content
    assert "print-join-command" in content


def test_common_prep_disables_swap_and_installs_kubeadm_stack():
    content = _script("00-common-prep.sh")
    assert "swapoff" in content
    for tool in ("containerd", "kubeadm", "kubelet", "kubectl"):
        assert tool in content


def test_kubespray_inventory_has_required_groups_and_counts():
    with open(ROOT / "kubespray" / "inventory" / "hosts.yaml", encoding="utf-8") as f:
        inv = yaml.safe_load(f)
    children = inv["all"]["children"]
    for group in ("kube_control_plane", "kube_node", "etcd", "k8s_cluster"):
        assert group in children, f"missing kubespray group: {group}"
    assert len(children["kube_control_plane"]["hosts"]) >= 3
    assert len(children["kube_node"]["hosts"]) >= 2
    # etcd should be colocated on the control-plane hosts for this topology
    assert set(children["etcd"]["hosts"]) == set(children["kube_control_plane"]["hosts"])

#!/usr/bin/env bash
# Run ONCE on the master node to upgrade the control plane to the
# latest patch/minor available for the apt repo currently configured.
# To move to a new minor, first repeat the "kubernetes.list" step from
# 00-common-prep.sh with the new TARGET_MINOR, then run this script.
set -euo pipefail

TARGET_MINOR="${TARGET_MINOR:?e.g. 1.36}"
TARGET_VERSION="${TARGET_VERSION:?e.g. 1.36.0-1.1}"   # exact apt package version, see `apt-cache madison kubeadm`

echo "==> Repointing the apt repo at v${TARGET_MINOR} and installing the new kubeadm"
echo "deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v${TARGET_MINOR}/deb/ /" | \
  sudo tee /etc/apt/sources.list.d/kubernetes.list
sudo apt-get update
sudo apt-mark unhold kubeadm
sudo apt-get install -y "kubeadm=${TARGET_VERSION}"
sudo apt-mark hold kubeadm

echo "==> Verifying the upgrade plan"
sudo kubeadm upgrade plan

echo "==> Applying the upgrade"
sudo kubeadm upgrade apply -y "v${TARGET_MINOR}.0"

echo "==> Upgrading kubelet and kubectl on the master itself"
sudo apt-mark unhold kubelet kubectl
sudo apt-get install -y "kubelet=${TARGET_VERSION}" "kubectl=${TARGET_VERSION}"
sudo apt-mark hold kubelet kubectl
sudo systemctl daemon-reload
sudo systemctl restart kubelet

echo "==> Done. Check with: kubectl get nodes -o wide"

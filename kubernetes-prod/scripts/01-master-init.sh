#!/usr/bin/env bash
# Run ONCE on the master node, after 00-common-prep.sh.
set -euo pipefail

K8S_MINOR="${K8S_MINOR:-1.35}"
POD_CIDR="${POD_CIDR:-10.244.0.0/16}"   # matches Flannel's default
MASTER_ADVERTISE_IP="${MASTER_ADVERTISE_IP:?set to this VM internal IP}"

echo "==> kubeadm init"
sudo kubeadm init \
  --pod-network-cidr="${POD_CIDR}" \
  --apiserver-advertise-address="${MASTER_ADVERTISE_IP}" \
  --kubernetes-version="v${K8S_MINOR}.0"

echo "==> Configuring kubectl for the current user"
mkdir -p "$HOME/.kube"
sudo cp -f /etc/kubernetes/admin.conf "$HOME/.kube/config"
sudo chown "$(id -u):$(id -g)" "$HOME/.kube/config"

echo "==> Installing the Flannel CNI"
kubectl apply -f https://github.com/flannel-io/flannel/releases/latest/download/kube-flannel.yml

echo "==> Waiting for the master node to become Ready"
kubectl wait --for=condition=Ready node --all --timeout=180s || true

echo "==> Save this join command -- run it on every worker node (as root):"
kubeadm token create --print-join-command

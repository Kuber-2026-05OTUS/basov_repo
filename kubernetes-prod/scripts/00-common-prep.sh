#!/usr/bin/env bash
# Run on EVERY node (master and workers) before kubeadm init/join.
# Target OS: Ubuntu 22.04 (matches the Yandex Cloud VM image used in
# ../docs/cloud/README.md). Must run as root (or via sudo).
#
# Pin the same Kubernetes minor version on every node and keep it one
# minor below whatever is current on the day you run this -- check
# https://kubernetes.io/releases/ first and edit K8S_MINOR below.
set -euo pipefail

K8S_MINOR="${K8S_MINOR:-1.35}"   # one minor below the latest stable series
CONTAINERD_VERSION="${CONTAINERD_VERSION:-1.7.24}"

echo "==> Disabling swap"
sudo swapoff -a
sudo sed -ri '/\sswap\s/s/^#?/#/' /etc/fstab

echo "==> Loading kernel modules required by the CNI and kube-proxy"
cat <<EOF | sudo tee /etc/modules-load.d/k8s.conf
overlay
br_netfilter
EOF
sudo modprobe overlay
sudo modprobe br_netfilter

echo "==> Enabling IPv4 forwarding and bridged traffic through iptables"
cat <<EOF | sudo tee /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward                 = 1
EOF
sudo sysctl --system

echo "==> Installing containerd"
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg apt-transport-https
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y "containerd.io=${CONTAINERD_VERSION}-1"

echo "==> Configuring containerd to use the systemd cgroup driver"
sudo mkdir -p /etc/containerd
containerd config default | sudo tee /etc/containerd/config.toml > /dev/null
sudo sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' /etc/containerd/config.toml
sudo systemctl restart containerd
sudo systemctl enable containerd

echo "==> Installing kubeadm, kubelet, kubectl (pinned to ${K8S_MINOR})"
curl -fsSL "https://pkgs.k8s.io/core:/stable:/v${K8S_MINOR}/deb/Release.key" | \
  sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
echo "deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v${K8S_MINOR}/deb/ /" | \
  sudo tee /etc/apt/sources.list.d/kubernetes.list
sudo apt-get update
sudo apt-get install -y kubelet kubeadm kubectl
sudo apt-mark hold kubelet kubeadm kubectl

echo "==> Done. kubeadm/kubelet/kubectl versions:"
kubeadm version -o short
kubelet --version
kubectl version --client -o yaml | grep gitVersion

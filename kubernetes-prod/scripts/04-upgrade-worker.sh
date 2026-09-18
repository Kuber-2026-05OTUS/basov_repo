#!/usr/bin/env bash
# Run once PER WORKER, one at a time (never in parallel -- that's the
# whole point of the sequential cordon/drain/upgrade/uncordon dance).
# Run the `kubectl cordon`/`drain`/`uncordon` parts from the MASTER;
# run the apt/kubeadm parts on the WORKER itself, over SSH.
set -euo pipefail

NODE_NAME="${NODE_NAME:?e.g. worker-1}"
TARGET_MINOR="${TARGET_MINOR:?e.g. 1.36}"
TARGET_VERSION="${TARGET_VERSION:?e.g. 1.36.0-1.1}"

echo "==> [master] Cordoning and draining ${NODE_NAME}"
kubectl cordon "${NODE_NAME}"
kubectl drain "${NODE_NAME}" --ignore-daemonsets --delete-emptydir-data --force

echo "==> [worker ${NODE_NAME}, run over SSH] Upgrading kubeadm and running node upgrade"
cat <<'INSTRUCTIONS'
  echo "deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v${TARGET_MINOR}/deb/ /" | \
    sudo tee /etc/apt/sources.list.d/kubernetes.list
  sudo apt-get update
  sudo apt-mark unhold kubeadm
  sudo apt-get install -y kubeadm=${TARGET_VERSION}
  sudo apt-mark hold kubeadm
  sudo kubeadm upgrade node
  sudo apt-mark unhold kubelet kubectl
  sudo apt-get install -y kubelet=${TARGET_VERSION} kubectl=${TARGET_VERSION}
  sudo apt-mark hold kubelet kubectl
  sudo systemctl daemon-reload
  sudo systemctl restart kubelet
INSTRUCTIONS

echo "==> [master] Uncordoning ${NODE_NAME} once the worker-side steps above are confirmed done"
read -r -p "Press Enter once the worker-side steps have completed... "
kubectl uncordon "${NODE_NAME}"

echo "==> Done. Repeat this whole script for the next worker, one at a time."

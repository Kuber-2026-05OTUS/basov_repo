#!/usr/bin/env bash
# Run on EVERY worker node, after 00-common-prep.sh.
# Paste the exact `kubeadm join ...` command printed at the end of
# 01-master-init.sh (or re-print it on the master with
# `kubeadm token create --print-join-command`) as JOIN_COMMAND.
set -euo pipefail

JOIN_COMMAND="${JOIN_COMMAND:?set to the full 'kubeadm join ...' command from the master}"

echo "==> Joining the cluster"
sudo ${JOIN_COMMAND}

echo "==> Done. Verify from the master with: kubectl get nodes -o wide"

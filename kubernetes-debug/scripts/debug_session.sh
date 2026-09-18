#!/usr/bin/env bash
# Reference runbook for the kubernetes-debug assignment. Requires kubectl
# 1.25+ (for ephemeral-container --profile support) and a real cluster
# (minikube or Yandex Managed Kubernetes both work per docs/README.md).
#
# This script is meant to be read and run step-by-step, not executed
# blindly end-to-end -- several steps are interactive (`-it`) or need you
# to substitute a PID/node name captured from a previous step's output.
# See ../IMPLEMENTATION_REPORT.md for why this repo ships the runbook
# rather than captured output.
set -euo pipefail

echo "1) Deploy the distroless target pod"
kubectl apply -f ../k8s/namespace.yaml -f ../k8s/pod-distroless-nginx.yaml
kubectl wait --for=condition=Ready pod/distroless-nginx -n debug-demo --timeout=60s

echo "2) Attach an ephemeral debug container sharing the nginx container's PID namespace"
# --target=nginx makes the ephemeral container join that container's PID
# namespace (this is what lets it see/signal/strace the nginx process)
# without editing the pod spec or restarting it.
kubectl debug -it distroless-nginx -n debug-demo \
  --image=nicolaka/netshoot \
  --target=nginx \
  -- bash

# --- run inside the ephemeral container ---
echo "3) Read the distroless container's filesystem from the ephemeral container"
echo '   ls -la /proc/1/root/etc/nginx   # PID 1 in the shared namespace is the nginx process'

echo "4) Capture traffic on port 80 (ephemeral containers share the pod network namespace automatically)"
echo '   tcpdump -nn -i any -e port 80'

echo "5) In a second terminal, generate some traffic against the pod"
echo '   kubectl run -n debug-demo curl-client --rm -it --image=curlimages/curl --restart=Never -- \'
echo '     curl -s -o /dev/null -w "%{http_code}\n" http://distroless-nginx.debug-demo.svc.cluster.local/'

echo "6) (bonus, *) strace the nginx master process from the same ephemeral container"
echo '   Needs the sysadmin debug profile for CAP_SYS_PTRACE, otherwise strace -p fails with EPERM:'
echo '   kubectl debug -it distroless-nginx -n debug-demo --image=nicolaka/netshoot --target=nginx --profile=sysadmin -- bash'
echo '   # then inside: strace -p 1'

echo "7) Debug the node that is running the pod"
NODE=$(kubectl get pod distroless-nginx -n debug-demo -o jsonpath='{.spec.nodeName}')
echo "   kubectl debug node/${NODE} -it --image=busybox"
echo "   # this schedules a privileged pod on \$NODE with the host filesystem mounted at /host"

echo "8) From the node debug pod, read the distroless pod's log file directly off the node"
POD_UID=$(kubectl get pod distroless-nginx -n debug-demo -o jsonpath='{.metadata.uid}')
echo "   ls -la /host/var/log/pods/debug-demo_distroless-nginx_${POD_UID}/nginx/"
echo "   cat /host/var/log/pods/debug-demo_distroless-nginx_${POD_UID}/nginx/0.log"
echo "   # (path depends on the container runtime; for containerd this is the standard kubelet log layout)"

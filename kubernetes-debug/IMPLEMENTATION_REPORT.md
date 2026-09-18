# Implementation report -- kubernetes-debug

## Why this folder ships a runbook instead of captured terminal output

Every step of this assignment asks for real captured evidence from a live
cluster: the pod manifest applied, `ls -la` output from inside an
ephemeral container, `tcpdump` packet captures, and pod logs read off a
node via a node-debug pod. That evidence can only come from a real
Kubernetes cluster with a real distroless nginx pod actually running and
receiving traffic -- it cannot be reproduced honestly without one.

This build sandbox has no Kubernetes cluster and no way to stand one up:

- `kubectl` is not installed and no cluster credentials exist.
- Docker itself works (`docker run hello-world` succeeds), so a
  Docker-based local cluster (`kind`) was attempted. It fails: `kind`'s
  node containers need `--privileged` with a writable `/lib/modules`
  mount and the ability to mount `sysfs` inside the container, and this
  sandbox's container runtime rejects both (`mkdir /lib/modules: read-only
  file system`, `mount src=sysfs ... operation not permitted`). This is a
  deliberate sandbox restriction, not a missing package, so no retries or
  alternate flags fix it.
- `minikube` has the same requirement (Docker driver still needs a
  privileged node container, or a full VM driver, neither available here).

Given that, fabricating `ls -la` output, tcpdump packet lines, or log
lines would misrepresent this sandbox as having tested something it
cannot test. Instead, `scripts/debug_session.sh` gives the exact,
ordered, copy-pasteable commands for every step (including the bonus `*`
task), and this report says plainly what was and wasn't verified.

## Verified in this sandbox

- `k8s/pod-distroless-nginx.yaml` parses as valid YAML, pins the image to
  `kyos0109/nginx-distroless:1.18.0` (confirmed this tag exists on Docker
  Hub, not just `latest`), sets resource requests/limits, and uses only
  `tcpSocket` probes (the image has no shell, so `exec` probes would fail).
- `kyos0109/nginx-distroless` genuinely has no shell/coreutils: this
  matches the assignment's premise and is why `kubectl debug --target=`
  (ephemeral containers), not `kubectl exec`, is the documented approach.
- The `kubectl debug --target=<container>` mechanism for sharing the PID
  namespace of a running container, and the fact that all containers in a
  pod already share the network namespace (so a debug ephemeral container
  can `tcpdump` the pod's traffic without extra flags), are documented,
  stable `kubectl` behaviors -- confirmed against the Kubernetes docs
  referenced in `docs/README.md`'s "Рекомендуемые источники", not assumed.
- The `--profile=sysadmin` requirement for `strace -p` to succeed (needs
  `CAP_SYS_PTRACE`, which the default ephemeral-container profile does not
  grant) is documented `kubectl debug` behavior, not guessed.
- `pytest tests` passes locally against the manifest structure.

## NOT verified -- needs a real cluster (minikube or Yandex Managed Kubernetes)

- That `kubectl apply -f k8s/` actually brings up `distroless-nginx` as `Running`.
- The actual `ls -la /proc/1/root/etc/nginx` output from inside the ephemeral container.
- Actual `tcpdump` packet capture output for real HTTP requests to the pod.
- The bonus `strace -p 1` output against the real nginx master process.
- Locating and reading the actual pod log file from the node's
  `/var/log/pods/...` path via a node-debug pod -- the exact directory
  name depends on the pod UID and container runtime layout of the real
  cluster, so `scripts/debug_session.sh` computes it from `kubectl get
  pod -o jsonpath` rather than hardcoding a path.

To produce the real evidence the assignment asks for, run
`scripts/debug_session.sh` step by step against a minikube cluster or a
Yandex Managed Kubernetes cluster and capture the terminal output.

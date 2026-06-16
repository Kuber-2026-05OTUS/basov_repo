### A. kubernetes-intro-v2

```bash
kubectl create -f ./kubernetes-intro-v2/namespace.yaml
```

```bash
kubectl config set-context --current --namespace=homework
```

```bash
kubectl config view --minify | grep namespace
```

```bash
kubectl apply -f ./kubernetes-intro-v2/pod.yaml
```


```bash
kubectl get pods
```

```bash
kubectl describe pod basov
```

```bash
kubectl logs basov
```

```bash
kubectl exec -it basov -- sh
```

```bash
kubectl delete pod basov -n homework
kubectl apply -f ./kubernetes-intro-v2/pod.yaml
```

```bash
kubectl exec -n homework basov -- basov -T
```


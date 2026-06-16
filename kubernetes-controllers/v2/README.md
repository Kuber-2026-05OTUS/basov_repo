### B. kubernetes-controlers

```bash
kubectl get nodes --show-labels
```

```bash
kubectl label node minikube homework=true
```

```bash
kubectl apply -f ./kubernetes-controllers
```

```bash
kubectl rollout status deployment basov-deployment
```

```bash
kubectl get pods -l app=basov -w
```

```bash
kubectl get deployment basov-deployment -o yaml | grep -A5 strategy
```


```bash
kubectl describe deployment basov-deployment
```


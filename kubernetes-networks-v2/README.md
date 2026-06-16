### C. kubernetes-networks

- `minikube delete && minikube start`
- `cd kubernetes-networks`
- `kubectl apply -f namespace.yaml`
- `kubectl config set-context --current --namespace=homework`
- `kubectl apply -f ./additional/manifests/configMap.yaml`
- `kubectl apply -f deployment.yaml`
- `kubectl get gatewayclass`

```bash
ubuntu@ubuntu-YO.HONOR:~/otus/basov_repo/kubernetes-networks$ kubectl get gatewayclass
error: the server doesn't have a resource type "gatewayclass"
```

- `kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.5.1/standard-install.yaml`

```bash
ubuntu@ubuntu-YO.HONOR:~/otus/basov_repo/kubernetes-networks$ kubectl get gatewayclass
No resources found

```


-   ```bash
    helm repo add traefik https://traefik.github.io/charts && helm repo update && \
    helm install traefik traefik/traefik --namespace traefik --create-namespace -f ./additional/helm/traefic-values.yaml
    ```


```bash
ubuntu@ubuntu-YO.HONOR:~/otus/basov_repo/kubernetes-networks$ helm repo add traefik https://traefik.github.io/charts && helm repo update && \
helm install traefik traefik/traefik --namespace traefik --create-namespace -f ./additional/helm/traefic-values.yaml
"traefik" already exists with the same configuration, skipping
Hang tight while we grab the latest from your chart repositories...
...Successfully got an update from the "longhorn" chart repository
...Successfully got an update from the "traefik" chart repository
...Successfully got an update from the "grafana" chart repository
...Successfully got an update from the "prometheus-community" chart repository
Update Complete. ⎈Happy Helming!⎈
NAME: traefik
LAST DEPLOYED: Sat Jun 13 12:55:38 2026
NAMESPACE: traefik
STATUS: deployed
REVISION: 1
TEST SUITE: None
NOTES:
traefik with docker.io/traefik:v3.7.4 has been deployed successfully on traefik namespace!

⚠️ DEPRECATION WARNING: Gateway API CRDs will no longer be shipped with this chart in a future major version.
You will need to install them yourself before deploying Traefik v3.7:
  kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.5.1/standard-install.yaml

```

```bash
ubuntu@ubuntu-YO.HONOR:~/otus/basov_repo/kubernetes-networks$ kubectl get gatewayclass
NAME      CONTROLLER                      ACCEPTED   AGE
traefik   traefik.io/gateway-controller   True       81s
```


- `kubectl apply -f gateway.yaml`

```bash
ubuntu@ubuntu-YO.HONOR:~/otus/basov_repo/kubernetes-networks$ kubectl apply -f gateway.yaml 
gateway.gateway.networking.k8s.io/homework-gateway created
ubuntu@ubuntu-YO.HONOR:~/otus/basov_repo/kubernetes-networks$ kubectl get gateway
NAME               CLASS     ADDRESS   PROGRAMMED   AGE
homework-gateway   traefik                          12s
```

- `kubectl apply -f service.yaml`

```bash
ubuntu@ubuntu-YO.HONOR:~/otus/basov_repo/kubernetes-networks$ kubectl apply -f service.yaml 
service/basov-service created
ubuntu@ubuntu-YO.HONOR:~/otus/basov_repo/kubernetes-networks$ kubectl get svc
NAME            TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)    AGE
basov-service   ClusterIP   10.108.71.217   <none>        8000/TCP   2s
```


- `kubectl apply -f httpRoute.yaml`

```bash
ubuntu@ubuntu-YO.HONOR:~/otus/basov_repo/kubernetes-networks$ kubectl apply -f httpRoute.yaml 
httproute.gateway.networking.k8s.io/homework-route created
ubuntu@ubuntu-YO.HONOR:~/otus/basov_repo/kubernetes-networks$ kubectl get httproute
NAME             HOSTNAMES           AGE
homework-route   ["homework.otus"]   5s
```

```bash
helm upgrade --install traefik traefik/traefik \
  -n traefik \
  -f ./additional/helm/traefic-values.yaml
```

`kubectl get gateway -n homework`

```bash
ubuntu@ubuntu-YO.HONOR:~$ kubectl get gateway -n homework
NAME               CLASS     ADDRESS        PROGRAMMED   AGE
homework-gateway   traefik   10.99.131.10   True         34m
```


```bash
echo "10.99.131.10 homework.otus" | sudo tee -a /etc/hosts
```


- `kubectl port-forward -n traefik service/traefik 8000:8000`

- `curl http://homework.otus/index.html`
```

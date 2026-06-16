### D. kubernetes-volumes

- `minikube delete && minikube start`
- `cd kubernetes-volumes`
- `kubectl config set-context --current --namespace=homework`
- `kubectl apply -f namespace.yaml && kubectl apply -f cm.yaml && kubectl apply -f pvc.yaml && kubectl apply -f deployment.yaml`

`kubectl get pods`

```bash
NAME                                READY   STATUS    RESTARTS   AGE
basov-deployment-6f9d677887-fvppv   1/1     Running   0          11m
basov-deployment-6f9d677887-qv5r6   1/1     Running   0          11m
basov-deployment-6f9d677887-tg742   1/1     Running   0          11m
```

```
kubectl exec -it basov-deployment-6f9d677887-fvppv -- sh -c "wget -qO- http://127.0.0.1:8000/conf/basov-default.conf"
```


```bash
ubuntu@ubuntu-YO.HONOR:~/otus/basov_repo/kubernetes-volumes$ kubectl exec -it basov-deployment-6f9d677887-fvppv -- sh -c "wget -qO- http://127.0.0.1:8000/conf/basov-default.conf"
Defaulted container "nginx-fork" out of: nginx-fork, wget-index-html (init)
server {
    listen 8000;

    root /homework;
    index index.html;

    location / {
        try_files $uri $uri/ =404;
    }
    
}
```

```bash
kubectl exec -it basov-deployment-74789cf9f-7mlhk -- sh -c "echo 'The new episode 8 of From airs on June 14, 2026.' > /homework/test-pvc"
```

```bash
kubectl delete pod basov-deployment-74789cf9f-7mlhk
pod "basov-deployment-74789cf9f-7mlhk" deleted from homework namespace
```

```bash
ubuntu@ubuntu-YO.HONOR:~/otus/basov_repo/kubernetes-volumes$ kubectl get pods
NAME                               READY   STATUS    RESTARTS   AGE
basov-deployment-74789cf9f-jr999   1/1     Running   0          14m
basov-deployment-74789cf9f-kmldh   1/1     Running   0          16s
basov-deployment-74789cf9f-mhrks   1/1     Running   0          14m
```

```bash
ubuntu@ubuntu-YO.HONOR:~/otus/basov_repo/kubernetes-volumes$ kubectl exec -it basov-deployment-74789cf9f-kmldh -- sh -c "cat /homework/test-pvc"
Defaulted container "nginx-fork" out of: nginx-fork, wget-index-html (init)
The new episode 8 of From airs on June 14, 2026.
```

```bash
ubuntu@ubuntu-YO.HONOR:~/otus/basov_repo/kubernetes-volumes$ kubectl delete deployment basov-deployment
deployment.apps "basov-deployment" deleted from homework namespace
ubuntu@ubuntu-YO.HONOR:~/otus/basov_repo/kubernetes-volumes$ kubectl get deployments
No resources found in homework namespace.
ubuntu@ubuntu-YO.HONOR:~/otus/basov_repo/kubernetes-volumes$ kubectl get pvc
NAME           STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS        VOLUMEATTRIBUTESCLASS   AGE
homework-pvc   Bound    pvc-b5b9fadd-9cfe-416f-bb9a-2d0381f685b6   1Gi        RWO            homework-hostpath   <unset>                 3m53s
ubuntu@ubuntu-YO.HONOR:~/otus/basov_repo/kubernetes-volumes$ kubectl apply -f deployment.yaml 
deployment.apps/basov-deployment created
ubuntu@ubuntu-YO.HONOR:~/otus/basov_repo/kubernetes-volumes$ kubectl get pods
NAME                               READY   STATUS    RESTARTS   AGE
basov-deployment-74789cf9f-42nk2   1/1     Running   0          16s
basov-deployment-74789cf9f-62xzr   1/1     Running   0          16s
basov-deployment-74789cf9f-gsknl   1/1     Running   0          16s
ubuntu@ubuntu-YO.HONOR:~/otus/basov_repo/kubernetes-volumes$  kubectl exec -it basov-deployment-74789cf9f-62xzr -- sh -c "cat /homework/test-pvc"
Defaulted container "nginx-fork" out of: nginx-fork, wget-index-html (init)
The new episode 8 of From airs on June 14, 2026.
```

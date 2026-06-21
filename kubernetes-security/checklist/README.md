Основное ДЗ
Задание со *

В процессе сделано:
Создан второй init-контейнер на основе busybox для `basov-deployment`, который обращается к `/metrics` и сохраняет ответ в `/init/metrics.html`.
Файл сохраняется в `emptyDir`-том, который разделяется между init-контейнерами и основным контейнером.
Аутентификация выполняется сервисным токеном в заголовке `Authorization: Bearer ...`.

Сгенерирован `cd.kubeconfig` для `kubectl`, настроенный для ServiceAccount `cd` с проверкой сертификата сервера.

Как запустить проект:

```powershell
minikube delete
minikube start

cd kubernetes-security
kubectl apply -f namespace.yaml
kubectl apply -f security.yaml
kubectl apply -f config-map.yaml
kubectl apply -f deployment.yaml
```

Часть с генерацией kubeconfig (после применения манифестов):

```powershell
kubectl create token cd -n homework --duration 24h > token
$API_SERVER = kubectl config view --minify -o jsonpath='{.clusters[0].cluster.server}'
kubectl get configmap kube-root-ca.crt -n kube-public -o jsonpath='{.data.ca\.crt}' > cluster-ca.crt

kubectl config set-cluster homework-cluster --server=$API_SERVER --certificate-authority=cluster-ca.crt --embed-certs=true --kubeconfig=cd.kubeconfig
kubectl config set-credentials cd --token=(Get-Content token) --kubeconfig=cd.kubeconfig
kubectl config set-context cd-context --cluster=homework-cluster --user=cd --namespace=homework --kubeconfig=cd.kubeconfig
kubectl config use-context cd-context --kubeconfig=cd.kubeconfig
```

Как проверить работоспособность:

```powershell
kubectl port-forward -n homework deployment/basov-deployment 8080:8000
curl http://127.0.0.1:8080/metrics.html
kubectl --kubeconfig=cd.kubeconfig get pods -n homework
```

PR checklist:
Выставлен label с темой домашнего задания.

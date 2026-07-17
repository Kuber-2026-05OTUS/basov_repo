# Выполнено ДЗ №9

 - [X] Основное ДЗ

## В процессе сделано:
 - Развернут локальный кластер Kubernetes (1-мастер, 2 воркера)
 - Воркер2 лейблирован как `infra` и добавлен соответствующий taint
 - Подготовлен файл `kubernetes-logging/minio/pvc.yaml`
 - Подготовлен файл `kubernetes-logging/minio/deployment.yaml`
 - Подготовлен файл `kubernetes-logging/minio/svc.yaml`
 - Подготовлен файл `kubernetes-logging/charts/grafana-loki/values.yaml`
 - Подготовлен файл `kubernetes-logging/charts/grafana-promtail/values.yaml`
 - Подготовлен файл `kubernetes-logging/charts/grafana/ns.yaml`
 - Подготовлен файл `kubernetes-logging/charts/grafana/pvc.yaml`
 - Подготовлен файл `kubernetes-logging/charts/grafana/values.yaml`
 - Подготовлен файл `kubernetes-logging/README.md`
 - Минио подключено к Loki (как бекенд), Loki — к Grafana

## Как запустить проект:

### Пометить ноду taintом
```
kubectl label node worker2 node-role=infra
kubectl taint node worker2 node-role=infra:NoSchedule
```

### Minio deploy standalone
```
cd kubernetes-logging
kubectl create namespace minio
kubectl apply -f ./minio/pvc.yaml
kubectl apply -f ./minio/deployment.yaml
kubectl apply -f ./minio/svc.yaml
```

### Loki install
```
helm repo add grafana-community https://grafana-community.github.io/helm-charts
helm repo update
helm install loki grafana-community/loki -f ./charts/grafana-loki/values.yaml -n loki --create-namespace
```

### Promtail install
```
helm install promtail grafana/promtail -n promtail --create-namespace -f ./charts/grafana-promtail/values.yaml
```

### Grafana install
```
kubectl apply -f ./charts/grafana/ns.yaml
kubectl apply -f ./charts/grafana/pvc.yaml
helm install grafana grafana/grafana -n grafana -f ./charts/grafana/values.yaml
```

## Как проверить работоспособность:
 - Проверить ноды: `kubectl get node -o wide --show-labels`
 - Проверить taints: `kubectl get nodes -o custom-columns=NAME:.metadata.name,TAINTS:.spec.taints`
 - Проверить helm релизы: `helm list -A`
 - Проверить порты: `kubectl -n minio port-forward svc/minio 9001:9001`
 - Открыть Grafana и проверить Explore по datasource Loki

## PR checklist:
 - [X] Выставлен label с темой домашнего задания

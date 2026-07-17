# Разбор домашнего задания: Kubernetes Logging

## 0. Подготовка кластера Kubernetes

### Сетап: 1 мастер + 2 воркера

Кластер развернут локально. Один из воркеров (`worker2`) выделен под инфраструктурные сервисы:

```bash
kubectl label node worker2 node-role=infra
kubectl taint node worker2 node-role=infra:NoSchedule
```

Проверка:

```bash
kubectl get node -o wide --show-labels
```

```text
NAME      STATUS   ROLES           AGE   VERSION   INTERNAL-IP       EXTERNAL-IP   OS-IMAGE                         KERNEL-VERSION           CONTAINER-RUNTIME     LABELS
master    Ready    control-plane   22h   v1.36.2   192.168.122.201   <none>        Debian GNU/Linux 12 (bookworm)   6.1.0-49-amd64 (amd64)   containerd://1.6.20   ...
worker1   Ready    <none>          21h   v1.36.2   192.168.122.202   <none>        Debian GNU/Linux 12 (bookworm)   6.1.0-49-amd64 (amd64)   containerd://1.6.20   ...
worker2   Ready    <none>          21h   v1.36.2   192.168.122.203   <none>        Debian GNU/Linux 12 (bookworm)   6.1.0-49-amd64 (amd64)   containerd://1.6.20   ...node-role=infra
```

```bash
kubectl get nodes -o custom-columns=NAME:.metadata.name,TAINTS:.spec.taints
```

```text
NAME      TAINTS
master    [map[effect:NoSchedule key:node-role.kubernetes.io/control-plane]]
worker1   <none>
worker2   [map[effect:NoSchedule key:node-role value:infra]]
```

## 1. Установка Minio (S3-хранилище для Loki)

Minio используется как S3-бекенд для хранения логов. Разворачивается на infra-ноду.

```bash
kubectl create namespace minio
kubectl apply -f ./minio/pvc.yaml
kubectl apply -f ./minio/deployment.yaml
kubectl apply -f ./minio/svc.yaml
```

Проверка порта:

```bash
kubectl -n minio port-forward svc/minio 9001:9001
```

Логин: `admin`, пароль: `admin123`.

## 2. Установка Loki

Loki — система индексации и хранения логов. Установлена через Helm-чарт в режиме Monolithic.

```bash
helm repo add grafana-community https://grafana-community.github.io/helm-charts
helm repo update
helm install loki grafana-community/loki -f ./charts/grafana-loki/values.yaml -n loki --create-namespace
```

Ключевые параметры в `values.yaml`:
- `deploymentMode: Monolithic` — один под обрабатывает чтение и запись
- `auth_enabled: false` — отключена аутентификация
- S3-бекенд указывает на Minio (`minio.minio.svc.cluster.local:9000`)
- `nodeSelector` и `tolerations` направляют поды на infra-ноду

Адрес для отправки логов внутри кластера:

```
http://loki-gateway.loki.svc.cluster.local/loki/api/v1/push
```

## 3. Установка Promtail

Promtail — агент сбора логов с нод. Развернут на всех нодах кластера (включая infra).

```bash
helm install promtail grafana/promtail -n promtail --create-namespace -f ./charts/grafana-promtail/values.yaml
```

Ключевые параметры в `values.yaml`:
- `tolerations: [{operator: Exists}]` — игнорирует любой тейнт, чтобы ставиться на все ноды
- Клиенты отправляют логи в Loki: `http://loki-gateway.loki.svc.cluster.local/loki/api/v1/push`
- Включен CRI pipeline stage

## 4. Установка Grafana

Grafana — платформа визуализации. Установлена на infra-ноду с подключенным datasource Loki.

```bash
kubectl apply -f ./charts/grafana/ns.yaml
kubectl apply -f ./charts/grafana/pvc.yaml
helm install grafana grafana/grafana -n grafana -f ./charts/grafana/values.yaml
```

Ключевые параметры в `values.yaml`:
- `nodeSelector` и `tolerations` — планирование на infra-ноду
- Datasource Loki настроен через `datasources.datasources.yaml`
- Адрес Loki: `http://loki-gateway.loki.svc.cluster.local`
- Логин: `admin`, пароль: `admin123`

## 5. Запуск всего решения

Из каталога `kubernetes-logging`:

```bash
# Пометить ноду
kubectl label node worker2 node-role=infra
kubectl taint node worker2 node-role=infra:NoSchedule

# Minio
kubectl create namespace minio
kubectl apply -f ./minio/pvc.yaml
kubectl apply -f ./minio/deployment.yaml
kubectl apply -f ./minio/svc.yaml

# Loki
helm repo add grafana-community https://grafana-community.github.io/helm-charts
helm repo update
helm install loki grafana-community/loki -f ./charts/grafana-loki/values.yaml -n loki --create-namespace

# Promtail
helm install promtail grafana/promtail -n promtail --create-namespace -f ./charts/grafana-promtail/values.yaml

# Grafana
kubectl apply -f ./charts/grafana/ns.yaml
kubectl apply -f ./charts/grafana/pvc.yaml
helm install grafana grafana/grafana -n grafana -f ./charts/grafana/values.yaml
```

## 6. Проверка работоспособности

Проверка helm релизов:

```bash
helm list -A
```

```text
NAME            NAMESPACE       REVISION        UPDATED                                 STATUS          CHART           APP VERSION
grafana         grafana         1               ...                                     deployed        grafana-10.5.15 12.3.1
loki            loki            1               ...                                     deployed        loki-18.4.0     3.7.3
promtail        promtail        1               ...                                     deployed        promtail-6.17.1 3.5.1
```

Проверка порта Minio:

```bash
kubectl -n minio port-forward svc/minio 9001:9001
```

В Grafana:
1. Открыть Grafana (port-forward или через ingress).
2. Перейти в **Configuration -> Data Sources**.
3. Убедиться, что datasource **Loki** добавлен и работает.
4. Перейти в **Explore**, выбрать datasource Loki.
5. Выполнить запрос (например, `{job=~".+"}`) и убедиться, что логи отображаются.

## 7. Полезные команды администратора

```bash
# Проверка подов
kubectl get pods -n minio
kubectl get pods -n loki
kubectl get pods -n promtail
kubectl get pods -n grafana

# Логи
kubectl logs -n minio <pod-name>
kubectl logs -n loki <pod-name>
kubectl logs -n promtail <pod-name> -f
kubectl logs -n grafana <pod-name>

# Описание ресурсов
kubectl describe pod -n minio <pod-name>
kubectl describe pod -n loki <pod-name>

# Удаление
helm uninstall grafana -n grafana
helm uninstall promtail -n promtail
helm uninstall loki -n loki
kubectl delete -f ./minio/svc.yaml
kubectl delete -f ./minio/deployment.yaml
kubectl delete -f ./minio/pvc.yaml
kubectl delete namespace minio
```

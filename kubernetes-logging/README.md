# Разбор домашнего задания: kubernetes-logging

## 1. Подготовка инфраструктуры (Yandex Cloud)

В Yandex Cloud развернут Managed Kubernetes кластер с двумя пулами узлов:
- Пул для рабочей нагрузки (`workload-pool`) - 1 нода
- Пул для инфраструктурных сервисов (`infra-pool`) - 1 нода

Инфраструктурной ноде добавлен taint для предотвращения планирования подов с рабочей нагрузкой:
```powershell
kubectl taint nodes <infra-node-name> node-role=infra:NoSchedule
```

Пример вывода конфигурации нод:
```powershell
kubectl get nodes -o custom-columns=NAME:.metadata.name,TAINTS:.spec.taints
```

Был создан S3 бакет в Yandex Object Storage и сгенерированы ключи доступа (Service Account) для Loki.

## 2. Установка Loki

Loki устанавливается на инфраструктурную ноду в режиме SingleBinary. Используется S3 как хранилище.

Применение:
```powershell
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update
helm install loki grafana/loki -f loki-values.yaml -n logging --create-namespace
```

## 3. Установка Promtail

Promtail устанавливается как DaemonSet на все ноды кластера (добавлен toleration для infra-ноды), чтобы собирать логи со всего кластера и отправлять в Loki.

Применение:
```powershell
helm install promtail grafana/promtail -f promtail-values.yaml -n logging
```

## 4. Установка Grafana

Grafana устанавливается на инфраструктурную ноду. В конфигурации (values.yaml) сразу прописан data source для подключения к Loki.

Применение:
```powershell
helm install grafana grafana/grafana -f grafana-values.yaml -n logging
```

## 5. Проверка работоспособности

1. Убедиться, что поды запустились:
```powershell
kubectl get pods -n logging -o wide
```

2. Получить пароль от Grafana (пользователь `admin`):
```powershell
kubectl get secret --namespace logging grafana -o jsonpath="{.data.admin-password}" | [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($input))
```

3. Пробросить порт:
```powershell
kubectl port-forward svc/grafana 8080:80 -n logging
```

4. Открыть в браузере `http://localhost:8080`, авторизоваться и перейти в раздел Explore -> DataSource `Loki`, выполнить тестовый запрос (например, `{namespace="logging"}`). Логи должны успешно отображаться. Скриншот успешного запроса можно найти в репозитории (при наличии).

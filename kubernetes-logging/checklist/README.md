# Выполнено ДЗ: kubernetes-logging

 - [X] Основное ДЗ

## В процессе сделано:
 - Созданы 2 пула нод в Managed Kubernetes (Yandex Cloud): для рабочей и инфраструктурной нагрузки.
 - Настроен taint `node-role=infra:NoSchedule` для infra-ноды.
 - Создан S3 бакет для хранения логов Loki.
 - Подготовлен файл `loki-values.yaml` для установки Loki (на infra-ноду, `auth_enabled: false`, S3-storage).
 - Подготовлен файл `promtail-values.yaml` для установки агентов на все ноды кластера.
 - Подготовлен файл `grafana-values.yaml` для установки Grafana (на infra-ноду, сконфигурирован data source).

## Как запустить проект:
 - Развернуть кластер в Yandex Cloud.
 - Настроить бакет и прописать ключи доступа в `loki-values.yaml`.
 - Выполнить установку через helm:
   - `helm install loki grafana/loki -f loki-values.yaml -n logging --create-namespace`
   - `helm install promtail grafana/promtail -f promtail-values.yaml -n logging`
   - `helm install grafana grafana/grafana -f grafana-values.yaml -n logging`

## Как проверить работоспособность:
 - Выполнить `kubectl port-forward svc/grafana 8080:80 -n logging`.
 - Открыть localhost:8080, зайти в Grafana под админом.
 - Перейти в раздел Explore, выбрать источник данных Loki.
 - Выполнить LogQL-запрос для проверки получения логов (например, по namespace).

## PR checklist:
 - [X] Выставлен label с темой домашнего задания

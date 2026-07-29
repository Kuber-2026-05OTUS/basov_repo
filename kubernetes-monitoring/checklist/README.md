# Выполнено ДЗ №8

 - [V] Основное ДЗ

## В процессе сделано:
 - Подготовлен файл `kubernetes-monitoring/namespace.yaml`
 - Подготовлен файл `kubernetes-monitoring/configmap.yaml`
 - Подготовлен файл `kubernetes-monitoring/deployment.yaml`
 - Подготовлен файл `kubernetes-monitoring/service.yaml`
 - Подготовлен файл `kubernetes-monitoring/serviceMonitor.yaml`
 - Подготовлен файл `kubernetes-monitoring/README.md`

## Как запустить проект:
 - Выполнить в директории `kubernetes-monitoring` команды `kubectl apply -f namespace.yaml`, `kubectl apply -f configmap.yaml`, `kubectl apply -f deployment.yaml`, `kubectl apply -f service.yaml`, `kubectl apply -f serviceMonitor.yaml`

## Как проверить работоспособность:
 - Проверить ресурсы: `kubectl get pods -n homework`, `kubectl get svc -n homework`
 - Проверить метрики через Prometheus: `kubectl port-forward -n monitoring svc/prometheus-operated 9091:9090` и затем в интерфейсе Prometheus выбрать запрос `nginx_up`

## PR checklist:
 - [V] Выставлен label с темой домашнего задания

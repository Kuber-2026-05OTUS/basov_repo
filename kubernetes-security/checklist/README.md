# Выполнено ДЗ №5

 - [V] Основное ДЗ
 - [V] Задание со *

## В процессе сделано:
 - Подготовлен файл `kubernetes-security/namespace.yaml`
 - Подготовлен файл `kubernetes-security/monitoring-rbac.yaml`
 - Подготовлен файл `kubernetes-security/cd-rbac.yaml`
 - Подготовлен файл `kubernetes-security/deployment.yaml`
 - Подготовлен файл `kubernetes-security/service.yaml`
 - Подготовлены инструкции в `kubernetes-security/README.md`

## Как запустить проект:
 - Выполнить `kubectl apply -f namespace.yaml`, `kubectl apply -f monitoring-rbac.yaml`, `kubectl apply -f cd-rbac.yaml`, `kubectl apply -f deployment.yaml`, `kubectl apply -f service.yaml` из директории `kubernetes-security`

## Как проверить работоспособность:
 - Выполнить `kubectl auth can-i --as=system:serviceaccount:homework:monitoring get /metrics`
 - Выполнить `kubectl get pods,svc -n homework`
 - Выполнить `kubectl -n homework create token cd --duration=24h`
 - Выполнить `kubectl -n homework port-forward svc/homework-service 8080:80` и проверить `curl http://127.0.0.1:8080/metrics.html`

## PR checklist:
 - [V] Выставлен label с темой домашнего задания

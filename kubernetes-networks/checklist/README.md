# Выполнено ДЗ №3

 - [V] Основное ДЗ
 - [V] Задание со *

## В процессе сделано:
 - Подготовлен файл kubernetes-networks/namespace.yaml
 - Подготовлен файл kubernetes-networks/deployment.yaml (readinessProbe через httpGet /index.html)
 - Подготовлен файл kubernetes-networks/service.yaml (ClusterIP)
 - Подготовлен файл kubernetes-networks/gateway.yaml
 - Подготовлен файл kubernetes-networks/httpRoute.yaml (включая rewrite /homepage -> /index.html)
 - Подготовлен файл kubernetes-networks/README.md

## Как запустить проект:
 - Например, выполнить `kubectl apply -f namespace.yaml`, `kubectl apply -f deployment.yaml`, `kubectl apply -f service.yaml`, `kubectl apply -f gateway.yaml`, `kubectl apply -f httpRoute.yaml` в директории kubernetes-networks
 - Установить Traefik Gateway API controller через Helm chart `traefik/traefik` с включением `providers.kubernetesGateway.enabled=true`

## Как проверить работоспособность:
 - Например, запустить команды `kubectl get all -n homework`, `kubectl get gateway -n homework`, `kubectl get httproute -n homework`
 - Для проверки с Windows-хоста добавить `homework.otus` в hosts, выполнить `kubectl -n traefik port-forward svc/traefik 80:80` и проверить `curl http://homework.otus/index.html` и `curl http://homework.otus/homepage`

## PR checklist:
 - [V] Выставлен label с темой домашнего задания

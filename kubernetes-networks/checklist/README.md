# Выполнено ДЗ №3

- [V] Основное ДЗ
- [V] Задание со *

## В процессе сделано:
- Изменена readiness-проба в deployment.yaml с `exec` на `httpGet` по URL `/index.html` на порту `8000`
- Подготовлен файл `kubernetes-networks/namespace.yaml`
- Подготовлен файл `kubernetes-networks/deployment.yaml`
- Подготовлен файл `kubernetes-networks/service.yaml` (`ClusterIP`)
- Подготовлен файл `kubernetes-networks/gateway.yaml`
- Подготовлен файл `kubernetes-networks/httpRoute.yaml` (включая rewrite `/homepage` -> `/index.html`)
- Подготовлен файл `kubernetes-networks/README.md`

## Как запустить проект:
- Установить Kubernetes кластер без Ingress-контроллера
- До установки Traefik применить Gateway API CRD: `kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.5.1/standard-install.yaml`
- Установить Traefik Gateway API controller через Helm chart `traefik/traefik` с включением `providers.kubernetesGateway.enabled=true`
- Применить манифесты в директории `kubernetes-networks`: `namespace.yaml`, `deployment.yaml`, `service.yaml`, `gateway.yaml`, `httpRoute.yaml`

## Как проверить работоспособность:
- Проверить ресурсы: `kubectl get pods,svc,gateway,httproute -n homework`
- Для проверки через Gateway IP добавить в `hosts` запись `<gateway-ip> homework.otus`
- Проверить маршрутизацию: `curl http://homework.otus/index.html`
- Проверить rewrite-правило задания со *: `curl http://homework.otus/homepage`

## PR checklist:
- [V] Выставлен label с темой домашнего задания

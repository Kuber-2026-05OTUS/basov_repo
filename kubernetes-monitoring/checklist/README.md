# Выполнено ДЗ № 8

- [x] Основное ДЗ

## В процессе сделано:
- Подготовлен кастомный образ nginx (`build/Dockerfile` + `build/nginx.conf`), отдающий метрики через `stub_status` на эндпоинте `/stub_status`
- Установлен в кластер Prometheus Operator (через helm-чарт `kube-prometheus-stack`)
- Создан `namespace.yaml` для namespace `monitoring-hw`
- Создан `deployment.yaml` с Deployment (контейнеры: кастомный nginx и nginx-prometheus-exporter) и Service
- Создан `servicemonitor.yaml`, описывающий сбор метрик с созданного Service

## Как запустить проект:
Выполнить в директории `kubernetes-monitoring`:
1. Собрать образ внутри minikube: `minikube image build -t custom-nginx:v1 ./build`
2. Установить Prometheus Operator (если еще не установлен): `helm install prometheus prometheus-community/kube-prometheus-stack --namespace monitoring --create-namespace`
3. Применить манифесты:
   - `kubectl apply -f namespace.yaml`
   - `kubectl apply -f deployment.yaml`
   - `kubectl apply -f servicemonitor.yaml`

## Как проверить работоспособность:
- Убедиться, что поды запущены: `kubectl get pods -n monitoring-hw`
- Пробросить порт к Prometheus: `kubectl port-forward svc/prometheus-kube-prometheus-prometheus 9090:9090 -n monitoring`
- Перейти по ссылке http://localhost:9090/targets и убедиться, что таргет `nginx-service-monitor` находится в статусе `UP`
- Выполнить в Prometheus запрос `nginx_up` и увидеть собранные метрики

## PR checklist:
- [x] Выставлен label с темой домашнего задания

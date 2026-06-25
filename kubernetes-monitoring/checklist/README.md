# Выполнено ДЗ: Мониторинг приложения в кластере

 - [V] Установлен в кластер Prometheus Operator
 - [V] Инструментировано приложение и настроен сбор с него метрик в Prometheus-формате

## В процессе сделано:
 - Подготовлен файл `build/nginx.conf` с конфигурацией `stub_status`
 - Подготовлен файл `build/Dockerfile` для сборки кастомного образа nginx
 - Подготовлен файл `namespace.yaml` для создания namespace `monitoring-hw`
 - Подготовлен файл `deployment.yaml` для создания Deployment (с двумя контейнерами: кастомным nginx и nginx-prometheus-exporter) и Service
 - Подготовлен файл `servicemonitor.yaml` описывающий сбор метрик с созданного Service

## Как запустить проект:
 1. Собрать образ внутри minikube: `minikube image build -t custom-nginx:v1 ./build`
 2. Установить Prometheus Operator через helm (если еще не установлен): `helm install prometheus prometheus-community/kube-prometheus-stack --namespace monitoring --create-namespace`
 3. Развернуть манифесты:
    `kubectl apply -f namespace.yaml`
    `kubectl apply -f deployment.yaml`
    `kubectl apply -f servicemonitor.yaml`

## Как проверить работоспособность:
 - Убедиться, что поды запущены: `kubectl get pods -n monitoring-hw`
 - Проверить наличие ServiceMonitor: `kubectl get servicemonitor -n monitoring-hw`
 - Пробросить порт к Prometheus: `kubectl port-forward svc/prometheus-kube-prometheus-prometheus 9090:9090 -n monitoring`
 - Открыть http://localhost:9090/targets и убедиться, что таргет `nginx-service-monitor` находится в статусе `UP`
 - Посмотреть метрику (например `nginx_up`) в интерфейсе Prometheus.

## PR checklist:
 - [V] Создан branch `kubernetes-monitoring`
 - [V] Все файлы добавлены в папку `kubernetes-monitoring`
 - [V] Выставлен label `Review Required` (при необходимости)
 - [V] PR не смерджен самостоятельно
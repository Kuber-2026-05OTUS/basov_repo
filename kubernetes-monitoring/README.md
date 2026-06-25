# Разбор домашнего задания: Мониторинг приложения в кластере

## 0. Подготовка окружения и установка Prometheus Operator

### Предварительные требования

У вас должен быть запущен кластер (например, Minikube) и установлен пакетный менеджер Helm. Если Helm не установлен, его можно установить через winget:

```powershell
winget install Helm.Helm
```

Не забудьте перезапустить терминал, чтобы путь к Helm применился.

### Добавление Helm репозитория Prometheus

Выполните следующие команды в PowerShell (или Git Bash):

```powershell
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
```

### Установка Prometheus Operator в кластер

Установим kube-prometheus-stack (который включает Prometheus Operator, Prometheus, Alertmanager, Grafana и набор стандартных экспортеров):

```powershell
helm install prometheus prometheus-community/kube-prometheus-stack --namespace monitoring --create-namespace
```

Убедитесь, что все pod'ы успешно запустились (это может занять несколько минут):

```powershell
kubectl get pods -n monitoring
```

## 1. Сборка кастомного образа nginx

Мы создадим образ `nginx`, который отдает метрики через `stub_status` на эндпоинте `/stub_status`. Файлы для сборки лежат в папке `build/`.

Чтобы образ был доступен внутри Minikube, выполните сборку прямо в его docker daemon:

```powershell
minikube image build -t custom-nginx:v1 ./build
```

*(Альтернативный вариант: собрать образ обычным docker build и загрузить его командой `minikube image load custom-nginx:v1`)*

## 2. Развертывание приложения с exporter'ом

### Создание namespace

```powershell
kubectl apply -f namespace.yaml
```

### Создание Deployment и Service

В файле `deployment.yaml` описан pod с двумя контейнерами: нашим кастомным `nginx` и `nginx-prometheus-exporter`, который собирает метрики из `nginx` (по адресу `http://localhost:80/stub_status`) и отдает их в формате Prometheus на порту `9113`.

```powershell
kubectl apply -f deployment.yaml
```

Проверим, что приложение запустилось:

```powershell
kubectl get pods -n monitoring-hw
```

## 3. Создание ServiceMonitor для автоматического сбора метрик

Файл `servicemonitor.yaml` создает CRD (Custom Resource Definition) типа `ServiceMonitor`. Prometheus Operator автоматически найдет его по метке `release: prometheus` и начнет собирать метрики с нашего Service по порту `metrics` (9113).

```powershell
kubectl apply -f servicemonitor.yaml
```

## 4. Проверка работы мониторинга

### Проверка отдачи метрик самим exporter'ом

Сначала можно убедиться, что метрики доступны напрямую из нашего Pod'а. Пробросим порт с сервиса на локальную машину:

```powershell
kubectl port-forward svc/nginx-exporter-svc 9113:9113 -n monitoring-hw
```

Откройте в браузере http://127.0.0.1:9113/metrics - вы должны увидеть метрики nginx (начинаются на `nginx_`). Нажмите `Ctrl+C` в терминале для остановки проброса.

### Проверка в Prometheus

Сделаем проброс порта для Prometheus:

```powershell
kubectl port-forward svc/prometheus-kube-prometheus-prometheus 9090:9090 -n monitoring
```

1. Откройте браузер и перейдите по адресу http://127.0.0.1:9090
2. Перейдите в меню **Status -> Targets**
3. В списке таргетов найдите `monitoring-hw/nginx-service-monitor/...`. Его статус должен быть `UP`.
4. Перейдите на вкладку **Graph**, введите в строку поиска `nginx_up` или `nginx_connections_active` и нажмите **Execute**. Вы увидите собранные метрики с вашего кастомного nginx.
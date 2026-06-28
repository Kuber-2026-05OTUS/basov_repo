# Разбор домашнего задания: Мониторинг приложения в кластере

## 0. Запускаю minikube с управлением через kube-cli

### Подготовка Windows ПК

### Чтобы minikube мог запуститься, надо:

1. Перезагрузить компьютер и зайти в BIOS/UEFI (Fn+F2, Fn+DEL или F12 при старте нажать).
2. Найти настройку виртуализации: она может называться Intel Virtualization Technology, VT-x, AMD-V, SVM Mode или Secure Virtual Machine.
3. Включить её, сохранить изменения и перезагрузить ПК.
4. Чтобы отключить быстрый запуск в Windows, надо открыть Панель управления → Электропитание → Действия кнопок питания, нажать «Изменение параметров, которые сейчас недоступны», снять галочку с «Включить быстрый запуск» и нажать «Сохранить изменения».
5. Скачать установщик QEMU для Windows с официального сайта: https://www.qemu.org/download/#windows
6. Установить qemu, обязательно отметив галочку "Add to PATH" при установке
7. Добавить через Win + R, введя sysdm.cpl и нажав Enter, перейдя на вкладку «Дополнительно» и нажав «Переменные среды» в разделе «Переменные среды пользователя» Path - изменить - в конце добавить c:\Program Files\qemu
8. Перезагрузить Windows

### Запускаю на Windows машине из про Git Bash:

```text
winget install Kubernetes.minikube
minikube config set driver qemu2
minikube start
```

### Установка Prometheus Operator

У вас должен быть запущен кластер Minikube и установлен пакетный менеджер Helm. Если Helm не установлен, его можно установить через winget из PowerShell:

```powershell
winget install Helm.Helm
```

Не забудьте перезапустить терминал, чтобы путь к Helm применился.

### Добавление Helm репозитория Prometheus

Выполните следующие команды в Git Bash:

```text
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

> Внимание: начиная с версии `1.0.0` экспортер `nginx-prometheus-exporter` использует парсер флагов kingpin, поэтому адрес для сбора метрик задается флагом с двойным дефисом: `--nginx.scrape-uri=http://localhost:80/stub_status`. С одиночным дефисом (`-nginx.scrape-uri`) контейнер уйдет в CrashLoopBackOff.

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

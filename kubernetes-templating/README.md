# Разбор домашнего задания: Kubernetes Templating

## 0. Подготовка рабочего окружения для Windows

### Установка Helm CLI

Helm используется для управления пакетами Kubernetes.

Установка с помощью `winget` из PowerShell:
```powershell
winget install -e --id Helm.Helm
```

Проверка установки из GitBash:
```text
helm version
```

### Установка Helmfile

Helmfile позволяет декларативно управлять несколькими релизами Helm.

Поскольку `helmfile` недоступен в официальном репозитории `winget`, рекомендуется использовать пакетный менеджер `scoop` или скачать бинарный файл напрямую:

**Установка через scoop:**
```powershell
scoop install helmfile
```

**Либо ручная установка:**
1. Скачайте последнюю версию `helmfile_windows_amd64.exe` со страницы релизов [GitHub Helmfile](https://github.com/helmfile/helmfile/releases).
2. Переименуйте файл в `helmfile.exe` и поместите его в папку, добавленную в переменную окружения `PATH` (например, `C:\Windows\System32` или `C:\tools`).

Проверка установки:
```powershell
helmfile version
```

## 1. Развертывание приложения (Задание 1)

В директории `kubernetes-templating/homework-chart` подготовлен Helm-чарт для развертывания приложения из предыдущих заданий (nginx с initContainer).

Чарт поддерживает конфигурацию через `values.yaml`:
- Изменение имен контейнеров и образов (теги и репозитории разделены)
- Включение/отключение probes
- Добавлен community-чарт redis как зависимость

### Установка релиза

1. Обновите зависимости (Redis):
```powershell
cd kubernetes-templating/homework-chart
helm dependency update
```

2. Установите чарт в namespace `homework`:
```powershell
helm upgrade --install homework-release . -n homework --create-namespace
```

После установки вы увидите сообщение (из `NOTES.txt`), которое подскажет, по какому адресу можно обратиться к сервису (например, с помощью `kubectl port-forward`).

## 2. Установка Kafka через Helmfile (Задание 2)

В корне папки `kubernetes-templating` подготовлен файл `helmfile.yaml`, описывающий установку 2 релизов Kafka из Bitnami чарта:

1. **kafka-prod** (в namespace `prod`): 5 брокеров, версия Kafka 3.5.2, протокол клиентских и межброкерных взаимодействий — SASL_PLAINTEXT.
2. **kafka-dev** (в namespace `dev`): 1 брокер, последняя версия, отключенная авторизация (PLAINTEXT).

### Развертывание с помощью Helmfile

Выполните команду в папке `kubernetes-templating`:

```powershell
helmfile apply
```

Эта команда автоматически добавит необходимые репозитории (bitnami), создаст namespace-ы и установит/обновит релизы Kafka согласно конфигурации.

## 3. Проверка работоспособности

- Проверка статуса релизов Helm:
```powershell
helm list -A
```

- Проверка подов Kafka:
```powershell
kubectl get pods -n prod
kubectl get pods -n dev
```

- Проверка подов приложения из Задания 1:
```powershell
kubectl get pods -n homework
```

## 4. Полезные команды администратора

Удаление релизов и очистка:
```powershell
# Удаление приложения
helm uninstall homework-release -n homework
kubectl delete namespace homework

# Удаление Kafka
helmfile destroy
```

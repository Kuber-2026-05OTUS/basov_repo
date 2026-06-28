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

Сам `scoop` устанавливается одной строкой — установочный скрипт скачивается с официального адреса [get.scoop.sh](https://get.scoop.sh) (исходники: [github.com/ScoopInstaller/Install](https://github.com/ScoopInstaller/Install)). Выполните в обычном (не админском) окне PowerShell:
```powershell
# Разрешаем выполнение установочного скрипта для текущего пользователя
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Скачиваем и запускаем официальный установщик scoop
Invoke-RestMethod -Uri https://get.scoop.sh | Invoke-Expression
```

После установки scoop поставьте сам `helmfile`:
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

### Установка RancherDesktop через winget (PowerShell от администратора)

```powershell
winget install Microsoft.WSL
winget install SUSE.RancherDesktop
winget install Kubernetes.kubectl
winget install Helm.Helm
winget install derailed.k9s
```

Полезные ссылки:

- Rancher Desktop: https://rancherdesktop.io/
- k3s: https://docs.k3s.io/
- k9s: https://k9scli.io/topics/install/
- kubectl: https://kubernetes.io/docs/tasks/tools/
- Helm: https://helm.sh/docs/intro/install/
- Gateway API: https://gateway-api.sigs.k8s.io/

### Настройка Rancher Desktop

1. Открыть Rancher Desktop.
2. В разделе Kubernetes включить `Enable Kubernetes`.
3. Container Engine выбрать `containerd`.
4. В Kubernetes version выбрать релиз с k3s (из стабильных выбрать latest).
5. Нажать `Apply` и дождаться статуса `Kubernetes is running`.

Проверка:

```powershell
kubectl config current-context
kubectl get nodes
```

### Запуск k9s отдельно в PowerShell

```powershell
k9s
```

## 1. Развертывание приложения (Задание 1)

В директории `kubernetes-templating/homework-chart` подготовлен Helm-чарт для развертывания приложения из предыдущих заданий (nginx с initContainer).

Чарт поддерживает конфигурацию через `values.yaml`:
- Изменение имен контейнеров и образов (теги и репозитории разделены)
- Включение/отключение probes
- Добавлен community-чарт redis как зависимость

### Установка релиза

1. Обновите зависимости (Redis) из Gib Bash:
```text
cd kubernetes-templating/homework-chart
helm dependency update
```

2. Установите чарт в namespace `homework`  из Gib Bash:
```text
helm upgrade --install homework-release . -n homework --create-namespace
```

После установки вы увидите сообщение (из `NOTES.txt`), которое подскажет, по какому адресу можно обратиться к сервису (например, с помощью `kubectl port-forward`).

3. Возвращение в корневой каталог:
```text
cd ../..
```

## 2. Установка Kafka через Helmfile (Задание 2)

В папке `kubernetes-templating/kafka` подготовлен файл `helmfile.yaml` и два файла со значениями (`values-prod.yaml`, `values-dev.yaml`), описывающие установку 2 релизов Kafka из Bitnami чарта:

1. **kafka-prod** (в namespace `prod`): 5 брокеров, протокол клиентских и межброкерных взаимодействий — SASL_PLAINTEXT (`controller.replicaCount: 5`).
2. **kafka-dev** (в namespace `dev`): 1 брокер, отключенная авторизация (PLAINTEXT), `persistence.enabled: false`.

### Важно про образ и версию Kafka

Bitnami закрыл бесплатный доступ к своим образам, поэтому в `values-*.yaml` используется совместимый community-образ `soldevelo/kafka`. В их реестре нет версии `3.5.2`, поэтому взята ближайшая доступная — `3.7.1`. Так как Kafka к этому моменту уже перешла с ZooKeeper на KRaft, нужно зафиксировать версию чарта, совместимую с образом: для Kafka `3.7.1` это чарт `29.3.14` (поэтому он запинен в `helmfile.yaml` через `version: 29.3.14`).

Поскольку чарт от Bitnami, а образ сторонний, в yaml файл values добавлен флаг, разрешающий несовместимые образы:
```yaml
global:
  security:
    allowInsecureImages: true
```

### Плагин helm-diff

`helmfile apply` использует под капотом `helm diff`. Если плагин не установлен, команда упадёт с ошибкой `unknown command "diff" for "helm"`. Установите плагин один раз через GitBash:
```text
helm plugin install --verify=false https://github.com/databus23/helm-diff
helm plugin list
```
### Развертывание kafka с помощью Helmfile

Выполните через GitBash команду в папке `kubernetes-templating/kafka`:

```text
cd kubernetes-templating/kafka

# (опционально) посмотреть итоговые манифесты с подстановками
helmfile template

# установить/обновить релизы
helmfile apply
```

Эта команда автоматически добавит необходимый репозиторий (bitnami), создаст namespace-ы и установит/обновит релизы Kafka согласно конфигурации.

## 3. Проверка работоспособности

- Проверка статуса релизов Helm через Git Bash:
```text
helm list -A
```

- Проверка подов Kafka через GitBash:
```text
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

# Удаление Kafka (выполнять в папке kubernetes-templating/kafka)
helmfile destroy
```

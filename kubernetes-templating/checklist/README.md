# Выполнено ДЗ № 6

- [V] Основное ДЗ
- [V] Задание со *

## В процессе сделано:
- Шаблонизирован проект из прошлых ДЗ (Helm-чарт `homework-chart`).
- Установка Kafka через Helmfile.

## Как запустить проект:

### Задание 1: Создание чарта на основе прошлых ДЗ

```bash
minikube delete && minikube start

cd kubernetes-templating
```

Установка Helm:
```bash
curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3
chmod 700 get_helm.sh
./get_helm.sh
```

Работа с чартом (`homework-chart` уже подготовлен в репозитории):
```bash
cd homework-chart
helm dependency update   # подтянуть зависимость redis
helm lint .
helm template homework .
helm install homework . -n homework --create-namespace
helm status homework -n homework
kubectl get pods -n homework
```

Пример вывода:
```text
$ kubectl get pods -n homework
NAME                                     READY   STATUS    RESTARTS   AGE
homework-homework-chart-cf6677d5f-4hf8j  1/1     Running   0          11m
homework-homework-chart-cf6677d5f-d49b8  1/1     Running   0          11m
homework-homework-chart-cf6677d5f-d6klv  1/1     Running   0          11m
homework-redis-master-0                  1/1     Running   0          11m
```

### Задание 2: Kafka через Helmfile

```bash
minikube delete && minikube start

cd kubernetes-templating/kafka
```

Установка Helmfile (https://helmfile.readthedocs.io/en/latest/#installation):
```bash
# Скачиваем архив для Linux amd64
wget https://github.com/helmfile/helmfile/releases/download/v1.6.0/helmfile_1.6.0_linux_amd64.tar.gz

# Распаковываем архив
tar -xzvf helmfile_1.6.0_linux_amd64.tar.gz

# Перемещаем распакованный бинарник в /usr/local/bin/
sudo mv helmfile /usr/local/bin/

# Проверяем версию
helmfile version
```

Добавить репозиторий bitnami:
```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
```

Проверить вывод шаблона с подстановками:
```bash
helmfile template
```

Запуск:
```bash
helmfile apply
```

#### Возможная ошибка: не установлен плагин helm-diff

`helmfile apply` использует `helm diff`. Если плагин не установлен, будет ошибка:
```text
Error: unknown command "diff" for "helm"
```

Проверка и установка плагина:
```bash
helm plugin list
helm plugin install https://github.com/databus23/helm-diff --version v3.15.10
```

После установки плагина повторно применить конфиг:
```bash
helmfile apply
```

#### Почему образ не от Bitnami, версия другая и т.д.

- Bitnami больше не бесплатны. Есть аналог `soldevelo/kafka`, обещают полную совместимость.
- В их репозитории нет версии `3.5.2`, поэтому взята первая доступная после неё — `3.7.1`.
- У Kafka был переход с ZooKeeper на KRaft, нужно поймать чарт, совместимый с образом:
  ```bash
  helm search repo bitnami/kafka --versions
  ```
  Крайняя версия чарта на Kafka `3.7.1` — `29.3.14`, её нужно запинить в `helmfile.yaml`.
- Кроме того, поскольку чарт Bitnami, а образы сторонние, в `values-*.yaml` добавлено:
  ```yaml
  global:
    security:
      allowInsecureImages: true
  ```

## Как проверить работоспособность:
```bash
kubectl get pods -n dev
kubectl get pods -n prod
```

## PR checklist:
- [V] Выставлен label с темой домашнего задания

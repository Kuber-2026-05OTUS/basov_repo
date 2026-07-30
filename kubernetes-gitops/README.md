# Разбор домашнего задания: Kubernetes GitOps

## 1. Подготовка кластера в Yandex Cloud

Необходимо развернуть Managed Kubernetes cluster в Yandex Cloud.
Для кластера нужно создать 2 пула нод:
1. Для рабочей нагрузки (worker-pool) - 1 нода.
2. Для инфраструктурных сервисов (infra-pool) - 1 нода.

Для инфраструктурной ноды добавляется taint:
`node-role=infra:NoSchedule`

## 2. Установка ArgoCD

Установка производится с помощью Helm-чарта. В файле `argocd/values.yaml` сконфигурированы параметры так, чтобы компоненты ArgoCD устанавливались исключительно на infra-ноды (добавлены `tolerations` и `nodeSelector`).

Команда для установки:
```powershell
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
helm install argocd argo/argo-cd -n argocd --create-namespace -f argocd/values.yaml
```

## 3. Создание проекта Otus

Манифест `argocd/project-otus.yaml` описывает проект `otus`.
В качестве Source-репозитория указан репозиторий с ДЗ курса.
В качестве Destination указан локальный кластер `https://kubernetes.default.svc`.

Применение:
```powershell
kubectl apply -f argocd/project-otus.yaml
```

## 4. Развертывание приложения kubernetes-networks

Манифест `argocd/app-networks.yaml` описывает приложение ArgoCD, которое устанавливает ресурсы из директории `kubernetes-networks`.
- Sync policy: manual
- Namespace: homework
- Проект: otus

Применение:
```powershell
kubectl apply -f argocd/app-networks.yaml
```

## 5. Развертывание приложения kubernetes-templating

Манифест `argocd/app-templating.yaml` описывает приложение ArgoCD, которое устанавливает Helm-чарт из директории `kubernetes-templating/homework-chart`.
- SyncPolicy: Auto (prune: true, selfHeal: true)
- Namespace: HomeworkHelm
- Проект: otus
- Параметр `replicaCount` переопределен на `3`.

Применение:
```powershell
kubectl apply -f argocd/app-templating.yaml
```

## Проверка работоспособности

1. Получить пароль от ArgoCD:
```powershell
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | % { [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($_)) }
```

2. Пробросить порт для доступа к UI:
```powershell
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

3. Открыть `https://localhost:8080` и авторизоваться с логином `admin`.

4. Проверить статус приложений `kubernetes-networks` и `kubernetes-templating` в UI ArgoCD.

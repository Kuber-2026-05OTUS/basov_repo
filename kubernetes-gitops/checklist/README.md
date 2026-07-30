# Выполнено ДЗ №kubernetes-gitops

- [V] Основное ДЗ

## В процессе сделано:
- Подготовлен файл `kubernetes-gitops/argocd/values.yaml` для установки ArgoCD на infra-ноды
- Подготовлен манифест `kubernetes-gitops/argocd/project-otus.yaml` для создания проекта Otus
- Подготовлен манифест `kubernetes-gitops/argocd/app-networks.yaml` для развертывания приложения из ДЗ kubernetes-networks
- Подготовлен манифест `kubernetes-gitops/argocd/app-templating.yaml` для развертывания Helm-чарта из ДЗ kubernetes-templating
- Подготовлен файл `kubernetes-gitops/docs/cloud/README.md` с инструкцией для администратора Yandex Cloud

## Как запустить проект:
- Развернуть managed Kubernetes cluster в Yandex Cloud (2 пула нод: worker и infra)
- Установить ArgoCD через Helm с использованием `values.yaml`
- Применить манифесты: `project-otus.yaml`, `app-networks.yaml`, `app-templating.yaml`

## Как проверить работоспособность:
- Проверить наличие подов ArgoCD на infra-ноде
- Проверить статус синхронизации приложений в ArgoCD UI или через CLI
- Проверить, что приложение `kubernetes-networks` установлено в namespace `homework`
- Проверить, что приложение `kubernetes-templating` установлено в namespace `HomeworkHelm` с 3 репликами

## PR checklist:
- [V] Выставлен label с темой домашнего задания

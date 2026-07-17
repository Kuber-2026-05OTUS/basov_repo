# Выполнено ДЗ №6

 - [V] Основное ДЗ

## В процессе сделано:
 - Подготовлен файл `kubernetes-gitops/argocd/values.yaml`
 - Подготовлен файл `kubernetes-gitops/argocd/project-otus.yaml`
 - Подготовлен файл `kubernetes-gitops/argocd/app-networks.yaml`
 - Подготовлен файл `kubernetes-gitops/argocd/app-templating.yaml`
 - Подготовлен файл `kubernetes-gitops/README.md`

## Как запустить проект:
  - Установить ArgoCD через Helm: `helm install argocd argo/argo-cd --namespace argocd --create-namespace --values kubernetes-gitops/argocd/values.yaml`
  - Применить проект: `kubectl apply -f kubernetes-gitops/argocd/project-otus.yaml`
  - Применить Application для kubernetes-networks: `kubectl apply -f kubernetes-gitops/argocd/app-networks.yaml`
  - Применить Application для kubernetes-templating: `kubectl apply -f kubernetes-gitops/argocd/app-templating.yaml`

## Как проверить работоспособность:
  - Проверить ArgoCD: `kubectl get pods -n argocd`
  - Проверить проекты ArgoCD: `kubectl get appproject -n argocd`
  - Проверить Applications: `kubectl get application -n argocd`
  - Открыть UI ArgoCD: `kubectl port-forward svc/argocd-server -n argocd 8080:443` и перейти по ссылке

## PR checklist:
 - [V] Выставлен label с темой домашнего задания

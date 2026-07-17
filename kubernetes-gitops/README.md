# Разбор домашнего задания: Kubernetes GitOps

## 1. Создание Managed Kubernetes Cluster в Yandex Cloud

Создан managed Kubernetes кластер с 2 пулами нод:

- **Worker pool** — 1 нода для прикладных нагрузок
- **Infrastructure pool** — 1 нода для инфраструктурных сервисов (ArgoCD и др.)

Taint для инфраструктурной ноды:
```
node-role=infra:NoSchedule
```

Проверка нод:

```bash
kubectl get nodes -o wide
kubectl describe node <infra-node> | grep Taint
```

## 2. Установка ArgoCD через Helm

**Helm chart:** `argo/argo-cd`

**values.yaml** — `kubernetes-gitops/argocd/values.yaml`

Все компоненты ArgoCD (controller, server, repoServer, applicationSet, notifications) настроены с:
- `nodeSelector: { node-role: infra }` — планирование только на инфраструктурные ноды
- `tolerations` для taint `node-role=infra:NoSchedule`

### Подготовка Helm

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
```

### Установка ArgoCD

```bash
helm install argocd argo/argo-cd \
  --namespace argocd \
  --create-namespace \
  --values kubernetes-gitops/argocd/values.yaml
```

### Проверка установки

```bash
kubectl get pods -n argocd
kubectl get svc -n argocd
```

Ожидаемый результат: все поды в статусе `Running`, сервисы доступны.

## 3. Создание AppProject "Otus"

**Манифест:** `kubernetes-gitops/argocd/project-otus.yaml`

```bash
kubectl apply -f kubernetes-gitops/argocd/project-otus.yaml
```

Проверка:

```bash
kubectl get appproject -n argocd
```

## 4. ArgoCD Application — kubernetes-networks

**Манифест:** `kubernetes-gitops/argocd/app-networks.yaml`

- Source: директория `kubernetes-networks/`
- Destination namespace: `homework`
- Project: `Otus`
- Sync policy: **Manual**
- `CreateNamespace=true` обеспечивает создание namespace `homework`

```bash
kubectl apply -f kubernetes-gitops/argocd/app-networks.yaml
```

## 5. ArgoCD Application — kubernetes-templating

**Манифест:** `kubernetes-gitops/argocd/app-templating.yaml`

- Source: Helm chart `kubernetes-templating/homework-chart`
- Destination namespace: `HomeworkHelm`
- Project: `Otus`
- Sync policy: **Automated** (autoHeal: true, prune: true)
- Параметр `replicaCount` переопределён на `1`
- `CreateNamespace=true` обеспечивает создание namespace `HomeworkHelm`

```bash
kubectl apply -f kubernetes-gitops/argocd/app-templating.yaml
```

## 6. Запуск всего решения

Из каталога `kubernetes-gitops`:

```bash
# Установка ArgoCD
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
helm install argocd argo/argo-cd \
  --namespace argocd \
  --create-namespace \
  --values kubernetes-gitops/argocd/values.yaml

# Применение манифестов
kubectl apply -f kubernetes-gitops/argocd/project-otus.yaml
kubectl apply -f kubernetes-gitops/argocd/app-networks.yaml
kubectl apply -f kubernetes-gitops/argocd/app-templating.yaml
```

Проверка состояния:

```bash
kubectl get pods -n argocd
kubectl get appproject -n argocd
kubectl get application -n argocd
```

## 7. Проверка через UI ArgoCD

Запуск проброса порта:

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

Открыть в браузере: `https://localhost:8080`

Получить пароль admin:

```bash
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

В интерфейсе ArgoCD:

- проверить проект `Otus`;
- убедиться, что Applications `kubernetes-networks` и `kubernetes-templating` отображаются;
- для manual sync — нажать кнопку Sync в нужном Application.

## 8. Полезные команды администратора

```bash
# Проверка подов ArgoCD
kubectl get pods -n argocd -o wide

# Описание подов
kubectl describe pod -n argocd <pod-name>

# Логи
kubectl logs -n argocd <pod-name>

# Удаление Application
kubectl delete -f kubernetes-gitops/argocd/app-networks.yaml
kubectl delete -f kubernetes-gitops/argocd/app-templating.yaml

# Удаление проекта
kubectl delete -f kubernetes-gitops/argocd/project-otus.yaml

# Удаление ArgoCD через Helm
helm uninstall argocd -n argocd
```

# Разбор домашнего задания: Kubernetes Operators

## 0. Запускаю Kubernetes через Rancher Desktop (k3s) с управлением через kubectl и k9s

### Подготовка Windows ПК

### Чтобы Rancher Desktop и k3s корректно запустились, надо:

1. Перезагрузить компьютер и зайти в BIOS/UEFI (Fn+F2, Fn+DEL или F12 при старте).
2. Найти настройку виртуализации: Intel Virtualization Technology, VT-x, AMD-V, SVM Mode или Secure Virtual Machine.
3. Включить виртуализацию, сохранить изменения и перезагрузить ПК.
4. Открыть PowerShell от имени администратора и включить WSL2:

```powershell
wsl --install
```

5. После установки WSL перезагрузить Windows.
6. Проверить, что WSL установлен и работает:

```powershell
wsl --status
wsl -l -v
```

### Устанавливаю Rancher Desktop, kubectl и k9s через winget

Запускаю в PowerShell:

```powershell
winget install -e --id SUSE.RancherDesktop
winget install -e --id Kubernetes.kubectl
winget install -e --id Derailed.k9s
```

Проверка из PowerShell, что утилиты доступны:

```powershell
kubectl version --client
k9s version
```

### Первичный запуск и настройка Rancher Desktop

1. Запустить Rancher Desktop из меню Start.
2. На первом экране выбрать:
   - `Container Engine`: `containerd` (или `dockerd`, если нужен Docker CLI);
   - `Enable Kubernetes`: включено;
   - `Kubernetes version`: стабильную версию по умолчанию.
3. Дождаться статуса `Kubernetes is running`.
4. В Settings -> Kubernetes проверить:
   - Kubernetes включен;
   - backend: `k3s`;
   - порт API-сервера по умолчанию не конфликтует с локальными сервисами.
5. В Settings -> WSL Integration включить интеграцию с используемым Linux-дистрибутивом (если работаете через WSL).

Проверка кластера:

```powershell
kubectl config current-context
kubectl get nodes -o wide
```

## Возможные ошибки

### Конфигурация с Docker на WSL 

Переустановите WSL в версию 2 (Rancher Desktop поддерживает только WSL 2):

```powershell
# Откройте PowerShell и проверьте версии WSL
wsl --list --verbose

# Если версия WSL = 1, переключите на WSL 2
wsl --set-version rancher-desktop 2
wsl --set-version rancher-desktop-data 2

# Установите WSL 2 как версию по умолчанию для новых дистрибутивов
wsl --set-default-version 2
```

Обновите WSL:

```powershell
wsl --update
```

Перезапустите WSL и Rancher Desktop:

```powershell
# Полная остановка WSL
wsl --shutdown
```

Затем перезапустите Rancher Desktop через File -> Exit


Проверьте, что заглушка создана
```text
mkdir -p ~/.kube
cat > ~/.kube/config <<EOF
apiVersion: v1
clusters: []
contexts: []
current-context: ""
kind: Config
preferences: {}
users: []
EOF
rm -rf ~/.kube/
```

Если ошибка сохраняется — зарегистрируйте дистрибутивы вручную:

```powershell
# Удалите старые записи
wsl --unregister rancher-desktop
wsl --unregister rancher-desktop-data

# Перезапустите Rancher Desktop — он создаст дистрибутивы заново
```

Дополнительно: сбросьте Winsock (если есть проблемы с сетью):

```powershell
netsh winsock reset
```

## 1. Создание CustomResourceDefinition (crd.yaml)

Подготовка `crd.yaml`:

```yaml
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: mysqls.otus.homework
spec:
  scope: Namespaced
  group: otus.homework
  names:
    kind: MySQL
    plural: mysqls
    singular: mysql
  versions:
    - name: v1
      served: true
      storage: true
      schema:
        openAPIV3Schema:
          type: object
          properties:
            spec:
              type: object
              properties:
                image:
                  type: string
                database:
                  type: string
                password:
                  type: string
                storage_size:
                  type: string
              required:
                - image
                - database
                - password
                - storage_size
```

Применение:

```powershell
kubectl apply -f crd.yaml
kubectl get crd
```

## 2. Создание ServiceAccount, ClusterRole и ClusterRoleBinding

Права для оператора подготовлены в двух вариантах:

- `security.yaml` — основное задание: сервис-аккаунт с полными правами на доступ к API-серверу.
- `security-minimal.yaml` — задание со `*`: минимальный набор прав, необходимых оператору (управление ресурсом CRD, создание и удаление Service, PV, PVC, Deployment).

Применяется только один из этих файлов (см. раздел «Запуск всего решения»).

Подготовка `security.yaml` (полные права — основное задание):

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: mysql-operator
  namespace: default
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: mysql-operator
rules:
  - apiGroups: ["*"]
    resources: ["*"]
    verbs: ["*"]
  - apiGroups: ["otus.homework"]
    resources: ["mysqls"]
    verbs: ["*"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: mysql-operator
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: mysql-operator
subjects:
  - kind: ServiceAccount
    name: mysql-operator
    namespace: default
```

Подготовка `security-minimal.yaml` (минимальные права — задание со *):

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: mysql-operator
  namespace: default
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: mysql-operator
rules:
  # Полный контроль над кастомным ресурсом MySQL (включая удаление)
  - apiGroups: ["otus.homework"]
    resources: ["mysqls"]
    verbs: ["get", "list", "watch", "update", "patch", "delete"]

  # Создание/обновление/удаление Deployment и ReplicaSet
  - apiGroups: ["apps"]
    resources: ["deployments", "deployments/status", "replicasets"]
    verbs: ["create", "update", "patch", "delete"]

  # Создание/удаление Service
  - apiGroups: [""]
    resources: ["services"]
    verbs: ["create", "delete"]

  # Создание/удаление PersistentVolume
  - apiGroups: [""]
    resources: ["persistentvolumes"]
    verbs: ["create", "delete"]

  # Создание/удаление PersistentVolumeClaim
  - apiGroups: [""]
    resources: ["persistentvolumeclaims"]
    verbs: ["create", "delete"]

  # Создание событий (для логирования)
  - apiGroups: [""]
    resources: ["events"]
    verbs: ["create", "patch", "update"]

  # минимально необходимые права на чтение/наблюдение,
  # чтобы Kopf не писал WARNING про нехватку прав на watch
  - apiGroups: ["*"]
    resources: ["*"]
    verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: mysql-operator
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: mysql-operator
subjects:
  - kind: ServiceAccount
    name: mysql-operator
    namespace: default
```

Применение (один из вариантов):

```powershell
# основное задание (полные права)
kubectl apply -f security.yaml

# либо задание со * (минимальные права)
kubectl apply -f security-minimal.yaml
```

## 3. Создание Deployment для оператора (deployment.yaml)

Подготовка `deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mysql-operator
  namespace: default
spec:
  replicas: 1
  selector:
    matchLabels:
      app: mysql-operator
  template:
    metadata:
      labels:
        app: mysql-operator
    spec:
      serviceAccountName: mysql-operator
      containers:
        - name: operator
          image: roflmaoinmysoul/mysql-operator:1.0.0
          imagePullPolicy: Always
```

Применение:

```powershell
kubectl apply -f deployment.yaml
kubectl get pods -l app=mysql-operator
```

## 4. Создание кастомного ресурса MySQL (object-crd.yaml)

Подготовка `object-crd.yaml`:

```yaml
apiVersion: otus.homework/v1
kind: MySQL
metadata:
  name: mysql-demo
spec:
  image: mysql:8.0
  database: otusdb
  password: gta6_is_comming_soon
  storage_size: 1Gi
```

Применение:

```powershell
kubectl apply -f object-crd.yaml
```

## 5. Запуск всего решения

Из каталога `kubernetes-operators`.

Основное задание (оператор с полными правами):

```powershell
kubectl apply -f crd.yaml
kubectl apply -f security.yaml
kubectl apply -f object-crd.yaml
kubectl apply -f deployment.yaml
```

Задание со `*` (тот же оператор, но с минимальными правами):

```powershell
kubectl apply -f crd.yaml
kubectl apply -f security-minimal.yaml
kubectl apply -f object-crd.yaml
kubectl apply -f deployment.yaml
```

Дождитесь, пока под оператора перейдет в статус Running:

```powershell
kubectl get pods -l app=mysql-operator -w
```

## 6. Проверка работы оператора

Проверка создания ресурсов:

```powershell
kubectl get mysqls
kubectl get pv,pvc,svc,deployments,pods
```

Вы должны увидеть, что оператор автоматически создал для ресурса `mysql-demo`:
- PersistentVolume (`mysql-demo-pv`)
- PersistentVolumeClaim (`mysql-demo-pvc`)
- Service (`mysql-demo`)
- Deployment (`mysql-demo`)

Проверка удаления ресурсов:

```powershell
kubectl delete mysql mysql-demo
kubectl get pv,pvc,svc,deployments,pods
```

Все связанные ресурсы должны быть удалены автоматически.

## 7. Задание с ** (Свой оператор)

В директории `build/` находятся файлы для сборки собственного оператора на базе фреймворка `Kopf`:
- `mysql_operator.py` - исходный код оператора на Python
- `Dockerfile` - файл для сборки Docker-образа

Для сборки и использования собственного оператора:

```powershell
# Сборка образа (если используете Docker)
cd build
docker build -t my-mysql-operator:1.0.0 .

# Если используете containerd в Rancher Desktop, можно загрузить образ напрямую:
nerdctl build -t my-mysql-operator:1.0.0 .
```

Затем в файле `deployment.yaml` замените образ `roflmaoinmysoul/mysql-operator:1.0.0` на `my-mysql-operator:1.0.0` и примените изменения.

## 8. Полезные команды администратора

```powershell
kubectl describe crd mysqls.otus.homework
kubectl describe mysql mysql-demo
kubectl logs -l app=mysql-operator
kubectl delete -f object-crd.yaml
kubectl delete -f deployment.yaml
kubectl delete -f security.yaml          # либо security-minimal.yaml
kubectl delete -f crd.yaml
```

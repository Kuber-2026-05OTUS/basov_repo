# Разбор домашнего задания: Kubernetes Volumes

## 0. Подготовка Windows-машины (k3s + k9s)

### Что будет в итоге

- На Windows будет установлен WSL2 с Ubuntu.
- Внутри Ubuntu будет установлен и запущен `k3s` (single-node cluster).
- На Windows будет установлен `k9s` для удобного управления кластером.
- В кластер будут применены манифесты из каталога `kubernetes-volumes`.

### 0.1 Проверка требований на Windows

1. Убедиться, что включена виртуализация в BIOS/UEFI (Intel VT-x / AMD-V).
2. Открыть PowerShell от имени администратора.
3. Проверить версию WSL:

```powershell
wsl --status
```

Если WSL не установлен, выполнить:

```powershell
wsl --install
```

После установки перезагрузить Windows.

### 0.2 Установка Ubuntu в WSL2

В PowerShell (администратор):

```powershell
wsl --install -d Ubuntu
```

После первого запуска Ubuntu создать пользователя Linux и пароль.

Проверить, что дистрибутив работает именно в WSL2:

```powershell
wsl -l -v
```

### 0.3 Включение systemd в WSL (нужно для k3s)

В Ubuntu:

```bash
sudo tee /etc/wsl.conf > /dev/null <<'EOF'
[boot]
systemd=true
EOF
```

В PowerShell:

```powershell
wsl --shutdown
```

Снова открыть Ubuntu и проверить:

```bash
systemctl is-system-running
```

### 0.4 Установка k3s в Ubuntu (WSL2)

В Ubuntu:

```bash
curl -sfL https://get.k3s.io | sh -
```

Проверка сервиса:

```bash
sudo systemctl status k3s --no-pager
```

Проверка ноды:

```bash
sudo k3s kubectl get nodes -o wide
```

### 0.5 Настройка kubeconfig для обычного пользователя

В Ubuntu:

```bash
mkdir -p ~/.kube
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
sudo chown "$(id -u):$(id -g)" ~/.kube/config
chmod 600 ~/.kube/config
```

Проверка:

```bash
kubectl get nodes
```

Если `kubectl` не найден, использовать встроенный:

```bash
sudo k3s kubectl get nodes
```

### 0.6 Установка k9s на Windows

В PowerShell:

```powershell
winget install k9s
```

Проверка:

```powershell
k9s version
```

## 1. Подготовка namespace.yaml

Файл `namespace.yaml`:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: homework
```

Применение:

```bash
kubectl apply -f namespace.yaml
```

## 2. Подготовка storageClass.yaml (задание со *)

Файл `storageClass.yaml`:

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: homework-storage
provisioner: k8s.io/minikube-hostpath
reclaimPolicy: Retain
volumeBindingMode: Immediate
```

Применение:

```bash
kubectl apply -f storageClass.yaml
kubectl get storageclass
```

## 3. Подготовка pvc.yaml

Файл `pvc.yaml`:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: homework-pvc
  namespace: homework
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
  storageClassName: homework-storage
```

Применение:

```bash
kubectl apply -f pvc.yaml
kubectl get pvc -n homework
kubectl get pv
```

## 4. Подготовка cm.yaml

Файл `cm.yaml`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: homework-config
  namespace: homework
data:
  file: |
    homework-config-volume
  app.properties: |
    mode=training
    source=configmap
```

Применение:

```bash
kubectl apply -f cm.yaml
kubectl get configmap -n homework
```

## 5. Подготовка deployment.yaml

В `deployment.yaml`:

- общий volume `homework-volume` переведен с `emptyDir` на `PersistentVolumeClaim`;
- добавлен volume `homework-config-volume` из `ConfigMap`;
- основной контейнер монтирует ConfigMap в `/homework/conf`;
- nginx настроен так, чтобы путь `/conf/file` отдавал файл из ConfigMap.

Применение:

```bash
kubectl apply -f deployment.yaml
```

## 6. Запуск всех манифестов

Из каталога `kubernetes-volumes`:

```bash
kubectl apply -f namespace.yaml
kubectl apply -f storageClass.yaml
kubectl apply -f pvc.yaml
kubectl apply -f cm.yaml
kubectl apply -f deployment.yaml
```

Проверка ресурсов:

```bash
kubectl get sc
kubectl get pvc,pv -n homework
kubectl get deploy,rs,pods -n homework -o wide
kubectl rollout status deployment/homework-deployment -n homework
```

## 7. Проверка доступности ConfigMap по URL /conf/file

### Вариант A: через port-forward

```bash
kubectl port-forward -n homework deployment/homework-deployment 8000:8000
```

В другом терминале:

```bash
curl http://127.0.0.1:8000/conf/file
```

Ожидаемый ответ:

```text
homework-config-volume
```

### Вариант B: через exec в pod

```bash
kubectl get pods -n homework -l app=homework
kubectl exec -it -n homework <pod-name> -- cat /homework/conf/file
```

## 8. Проверка через k9s

1. В PowerShell или Ubuntu запустить:

```bash
k9s
```

2. В интерфейсе k9s:
   - выбрать namespace `homework`;
   - проверить `pods`, `deployments`, `pvc`, `configmaps`;
   - открыть pod `homework` и посмотреть mounted volume.

## 9. Полезные команды администратору

```bash
kubectl describe pvc homework-pvc -n homework
kubectl describe pod -n homework <pod-name>
kubectl logs -n homework <pod-name>
kubectl delete -f deployment.yaml
kubectl delete -f cm.yaml
kubectl delete -f pvc.yaml
kubectl delete -f storageClass.yaml
kubectl delete -f namespace.yaml
```

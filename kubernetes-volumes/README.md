# Разбор домашнего задания: Kubernetes Volumes

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

Проверка, что утилиты доступны:

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

## 1. Создание namespace.yaml

Подготовка `namespace.yaml`:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: homework
```

Применение:

```powershell
kubectl apply -f namespace.yaml
```

## 2. Создание storageClass.yaml (задание со *)

Подготовка `storageClass.yaml`:

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

```powershell
kubectl apply -f storageClass.yaml
kubectl get sc
```

## 3. Создание pvc.yaml

Подготовка `pvc.yaml`:

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

```powershell
kubectl apply -f pvc.yaml
kubectl get pvc -n homework
kubectl get pv
```

## 4. Создание cm.yaml

Подготовка `cm.yaml`:

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

```powershell
kubectl apply -f cm.yaml
kubectl get configmap -n homework
```

## 5. Обновление deployment.yaml

В `deployment.yaml` сделано:

- `emptyDir` заменен на `PersistentVolumeClaim` (`homework-pvc`);
- добавлен volume из `ConfigMap` и mount в `/homework/conf`;
- настроена выдача содержимого ConfigMap по URL `/conf/file`.

Применение:

```powershell
kubectl apply -f deployment.yaml
```

## 6. Запуск всего решения

Из каталога `kubernetes-volumes`:

```powershell
kubectl apply -f namespace.yaml
kubectl apply -f storageClass.yaml
kubectl apply -f pvc.yaml
kubectl apply -f cm.yaml
kubectl apply -f deployment.yaml
```

Проверка состояния:

```powershell
kubectl get sc
kubectl get pvc,pv -n homework
kubectl get deployments,rs,pods -n homework -o wide
kubectl rollout status deployment/homework-deployment -n homework
```

## 7. Проверка, что /conf/file отдается из ConfigMap

Запускаю проброс порта:

```powershell
kubectl port-forward -n homework deployment/homework-deployment 8000:8000
```

Во втором терминале:

```powershell
curl http://127.0.0.1:8000/conf/file
```

Ожидаемый ответ:

```text
homework-config-volume
```

Дополнительно можно проверить напрямую в pod:

```powershell
kubectl get pods -n homework -l app=homework
kubectl exec -it -n homework <pod-name> -- cat /homework/conf/file
```

## 8. Проверка через k9s

Запуск:

```powershell
k9s
```

В интерфейсе k9s:

- переключиться в namespace `homework`;
- проверить `pods`, `deployments`, `pvc`, `configmaps`;
- убедиться, что pod в статусе `Running` и рестартов нет.

## 9. Полезные команды администратора

```powershell
kubectl describe pvc homework-pvc -n homework
kubectl describe deployment homework-deployment -n homework
kubectl describe pod -n homework <pod-name>
kubectl logs -n homework <pod-name>
kubectl delete -f deployment.yaml
kubectl delete -f cm.yaml
kubectl delete -f pvc.yaml
kubectl delete -f storageClass.yaml
kubectl delete -f namespace.yaml
```

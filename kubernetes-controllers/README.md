# Разбор домашнего задания: Kubernetes Controllers

## 0. Запускаю minikube с управлением через kube-cli

### Подготовка Windows ПК

### Чтобы minikube мог запуститься, надо:

1. Перезагрузить компьютер и зайти в BIOS/UEFI (Fn+F2, Fn+DEL или F12 при старте нажать).
2. Найти настройку виртуализации: она может называться Intel Virtualization Technology, VT-x, AMD-V, SVM Mode или Secure Virtual Machine.
3. Включить её, сохранить изменения и перезагрузить ПК.
4. Чтобы отключить быстрый запуск в Windows, надо открыть Панель управления → Электропитание → Действия кнопок питания, нажать «Изменение параметров, которые сейчас недоступны», снять галочку с «Включить быстрый запуск» и нажать «Сохранить изменения».
5. Скачать установщик QEMU для Windows с официального сайта: https://www.qemu.org/download/#windows
6. Установить qemu, обязательно отметив галочку "Add to PATH" при установке
7. Добавить через Win + R, введя sysdm.cpl и нажав Enter, перейдя на вкладку «Дополнительно» и нажав «Переменные среды» в разделе «Переменные среды пользователя» Path - изменить - в конце добавить c:\Program Files\qemu
8. Перезагрузить Windows

### Запускаю на Windows машине из про Git Bash:

```text
winget install Kubernetes.minikube
minikube config set driver qemu2
minikube start
```

## 1. Создание namespace.yaml

Подготовка namespace.yaml:

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

## 2. Создание deployment.yaml

Подготовка deployment.yaml, файл включает:

- namespace homework;
- replicas = 3;
- спецификацию pod;
- readinessProbe с проверкой файла /homework/index.html;
- стратегию обновления RollingUpdate с maxUnavailable = 1.

Применение:

```powershell
kubectl apply -f deployment.yaml
```

## Запуск

```powershell
kubectl get deployments -n homework
kubectl get rs -n homework
kubectl get pods -n homework -o wide
kubectl describe deployment homework-deployment -n homework
kubectl rollout status deployment/homework-deployment -n homework
```

Проверка файла в одном из pod:

```powershell
kubectl exec -it $(kubectl get pod -n homework -l app=homework -o jsonpath="{.items[0].metadata.name}") -n homework -- ls /homework
```

## Задание со *

В deployment.yaml уже добавлен блок nodeSelector в виде комментария:

```yaml
# nodeSelector:
#   homework: "true"
```

Для выполнения задания со *:

1. Раскомментируем nodeSelector в deployment.yaml.
2. Повесим метку на ноду:

```powershell
kubectl label nodes <node-name> homework=true
```

## Разбор домашнего задания: namespace.yaml и pod.yaml, соответствующие всем требованиям.

## 0. Запускаю minikube с управлением через kube-cli
### Подготовка Windows ПК
### Чтобы VirtualBox/minikube мог запустить VM, надо:
1. Перезагрузить компьютер и зайти в BIOS/UEFI (Fn+F2, Fn+DEL или F12 при старте нажать).
2. Найти настройку виртуализации: она может называться Intel Virtualization Technology, VT-x, AMD-V, SVM Mode или Secure Virtual Machine.
3. Включить её, сохранить изменения и перезагрузить ПК.
4. Чтобы отключить быстрый запуск в Windows, надо открыть Панель управления → Электропитание → Действия кнопок питания, нажать «Изменение параметров, которые сейчас недоступны», снять галочку с «Включить быстрый запуск» и нажать «Сохранить изменения».

### Запускаю на Windows машине из про Git Bash:
text
### winget install Kubernetes.minikube
### minikube delete
### minikube start

## 1. Создание namespace.yaml
text
### apiVersion: v1
### kind: Namespace
### metadata:
### __name: homework
### Создаю файл namespace.yaml в папке kubernetes-intro и применяю:

powershell
### kubectl apply -f namespace.yaml
## 2. Создание pod.yaml
text
### apiVersion: v1
### kind: Pod
### metadata:
### __name: homework-pod
### __namespace: homework
### spec:
### __volumes:
### ____- name: shared-volume
### ______emptyDir: {}
### __initContainers:
### ____- name: init-downloader
### ______image: busybox
### ______command:
### ________- /bin/sh
### ________- -c
### ________- |
### __________wget -O /init/index.html https://example.com
### ______volumeMounts:
### ________- name: shared-volume
### __________mountPath: /init
### __containers:
### ____- name: main-server
### ______image: nginx
### ______ports:
### ________- containerPort: 8000
### ______volumeMounts:
### ________- name: shared-volume
### __________mountPath: /homework
### ______lifecycle:
### ________preStop:
### __________exec:
### ____________command:
### ______________- /bin/sh
### ______________- -c
### ______________- rm -f /homework/index.html
### Создаю файл pod.yaml в папке kubernetes-intro и применяю:

powershell
### kubectl apply -f pod.yaml
### Пояснения к pod.yaml
### Требование      Как реализовано
### Namespace homework      metadata.namespace: homework
### Веб-сервер на 8000 порту        containerPort: 8000 в основном контейнере
### Отдаёт /homework        volumeMounts.mountPath: /homework у основного контейнера
### init-контейнер скачивает index.html     busybox + wget -O /init/index.html
### init сохраняет в /init  volumeMounts.mountPath: /init у init-контейнера
### Общий том EmptyDir      volumes[0].emptyDir с именем shared-volume
### Монтирование: /homework и /init mountPath у обоих контейнеров
### Удаление index.html перед завершением   lifecycle.preStop.exec.command: rm -f /homework/index.html
### Проверка выполнения
powershell
### kubectl get pods -n homework
### kubectl describe pod homework-pod -n homework
### kubectl exec -it homework-pod -n homework -- ls /homework
### kubectl exec -it homework-pod -n homework -- ls /init

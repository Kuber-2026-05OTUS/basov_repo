# Выполнено ДЗ №4

 - [V] Основное ДЗ
 - [V] Задание со *

## В процессе сделано:
 - Подготовлен файл `kubernetes-volumes/namespace.yaml`
 - Подготовлен файл `kubernetes-volumes/pvc.yaml`
 - Подготовлен файл `kubernetes-volumes/cm.yaml`
 - Подготовлен файл `kubernetes-volumes/deployment.yaml`
 - Подготовлен файл `kubernetes-volumes/storageClass.yaml`
 - Подготовлен файл `kubernetes-volumes/README.md`

## Как запустить проект:
 - Выполнить в директории `kubernetes-volumes` команды `kubectl apply -f namespace.yaml`, `kubectl apply -f storageClass.yaml`, `kubectl apply -f pvc.yaml`, `kubectl apply -f cm.yaml`, `kubectl apply -f deployment.yaml`

## Как проверить работоспособность:
 - Проверить ресурсы: `kubectl get sc`, `kubectl get pvc,pv -n homework`, `kubectl get pods -n homework`
 - Проверить отдачу файла из ConfigMap по URL: `kubectl port-forward -n homework deployment/homework-deployment 8000:8000` и затем `curl http://127.0.0.1:8000/conf/file`

## PR checklist:
 - [V] Выставлен label с темой домашнего задания

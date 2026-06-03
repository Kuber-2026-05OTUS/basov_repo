# Основное ДЗ
## В процессе сделано:
### Создан namespace homework (kubernetes-intro/namespace.yaml)
### Создан pod my-pod в namespace homework (kubernetes-intro/pod.yaml)
### Изменена дефолтная конфигурация web server
## Как запустить проект:
### kubectl apply -f kubernetes-intro/namespace.yaml - создать ns
### kubectl apply -f kubernetes-intro/pod.yaml - создать pod
## Как проверить работоспособность:
### Пробросить порт: kubectl port-forward pod/homework-pod 8000:8000 -n homework и открыть localhost:8000
## PR checklist:
### Выставлен label с темой домашнего задания

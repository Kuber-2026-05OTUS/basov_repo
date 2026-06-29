# Выполнено ДЗ №7

 - [x] Основное ДЗ
 - [x] Задание со *
 - [x] Задание с **

## В процессе сделано:
- Подготовлен `crd.yaml` — CustomResourceDefinition `MySQL` (group `otus.homework`, version `v1`, plural `mysqls`) с обязательными строковыми полями `image`, `database`, `password`, `storage_size`.
- Подготовлен `security.yaml` (полные права на API-сервер — основное ДЗ) и `security-minimal.yaml` (минимальный набор прав — задание со *): `ServiceAccount`, `ClusterRole`, `ClusterRoleBinding`.
- Подготовлен `deployment.yaml` — Deployment оператора с образом `roflmaoinmysoul/mysql-operator:1.0.0`.
- Подготовлен `object-crd.yaml` — кастомный объект `kind: MySQL` (`mysql-demo`).
- Подготовлены файлы собственного оператора `build/mysql_operator.py` и `build/Dockerfile` на базе Kopf (задание с **).

## Как запустить проект:
 - Например, для основной задачи в директории kubernetes-operators запустить команды `kubectl apply -f crd.yaml`, `kubectl apply -f security.yaml`, `kubectl apply -f object-crd.yaml`, `kubectl apply -f deployment.yaml`
 - Например, для задачи со * в директории kubernetes-operators запустить команды `kubectl apply -f crd.yaml`, `kubectl apply -f security-minimal.yaml`, `kubectl apply -f object-crd.yaml`, `kubectl apply -f deployment.yaml`
 - Например, для задачи с ** в директории kubernetes-operators/build запустить команды `docker build -t my-mysql-operator:1.0.0 .`, `nerdctl build -t my-mysql-operator:1.0.0 .`, `kubectl describe crd mysqls.otus.homework`, `kubectl describe mysql mysql-demo`, `kubectl logs -l app=mysql-operator`

## Как проверить работоспособность:
 - Например, для основной задачи в директории kubernetes-operators командой `kubectl get crd mysqls.otus.homework`
 - Например, для задачи со * в директории kubernetes-operators командой `kubectl get pods -n default -l app=mysql-operator`
 - Например, для задачи с ** в директории kubernetes-operators командой `kubectl logs -l app=mysql-operator`

## PR checklist:
 - [x] Выставлен label с темой домашнего задания

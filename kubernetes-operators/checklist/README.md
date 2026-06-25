# Выполнено ДЗ: Kubernetes Operators

 - [V] Основное ДЗ
 - [V] Задание со *
 - [V] Задание со **

## В процессе сделано:
 - Подготовлен файл `kubernetes-operators/crd.yaml`
 - Подготовлен файл `kubernetes-operators/rbac.yaml` (с минимально необходимыми правами для задания со *)
 - Подготовлен файл `kubernetes-operators/deploy.yaml`
 - Подготовлен файл `kubernetes-operators/cr.yaml`
 - Подготовлены файлы для сборки собственного оператора `kubernetes-operators/build/mysql_operator.py` и `kubernetes-operators/build/Dockerfile` (для задания со **)
 - Подготовлен файл инструкций для Windows администратора `kubernetes-operators/README.md`

## Как запустить проект:
 - Выполнить в директории `kubernetes-operators` команды:
   - `kubectl apply -f crd.yaml`
   - `kubectl apply -f rbac.yaml`
   - `kubectl apply -f deploy.yaml`
 - Дождаться запуска оператора и выполнить `kubectl apply -f cr.yaml`

## Как проверить работоспособность:
 - Проверить создание ресурсов: `kubectl get mysqls`, `kubectl get pv,pvc,svc,deployments,pods`
 - Убедиться, что для созданного ресурса `mysql-instance` оператор развернул Deployment, Service, PV и PVC.
 - Проверить удаление: `kubectl delete mysql mysql-instance` и убедиться, что связанные ресурсы удалились.

## PR checklist:
 - [V] Выставлен label с темой домашнего задания

# Выполнено ДЗ "Kubernetes Templating"

 - [V] Основное ДЗ

## В процессе сделано:
 - Создан Helm-чарт `homework-chart` для развертывания приложения из предыдущих заданий с вынесением конфигурации (имена, образы, порты, probes) в `values.yaml`.
 - Настроен вывод сообщения в `NOTES.txt` с адресом подключения после установки чарта.
 - Добавлена зависимость от community-чарта Redis в `homework-chart`.
 - Подготовлен декларативный манифест `helmfile.yaml` для развертывания двух инсталляций Kafka из Bitnami чарта с разными параметрами конфигурации для dev и prod сред.
 - Подготовлена инструкция администратора в `kubernetes-templating/README.md` с описанием установки инструментов (Helm, Helmfile) и запуска проекта на ОС Windows.

## Как запустить проект:
 - Для запуска приложения: выполнить в директории `kubernetes-templating/homework-chart` команды `helm dependency update` и `helm upgrade --install homework-release . -n homework --create-namespace`
 - Для установки Kafka: выполнить в директории `kubernetes-templating` команду `helmfile apply`

## Как проверить работоспособность:
 - Проверить ресурсы приложения: `kubectl get pods,svc -n homework` и выполнить подключение по инструкции из `NOTES.txt`.
 - Проверить успешное развертывание Kafka: `helm list -A` и `kubectl get statefulsets,pods -n prod`, `kubectl get statefulsets,pods -n dev`.

## PR checklist:
 - [V] Выставлен label с темой домашнего задания

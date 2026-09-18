# Основное ДЗ

## В процессе сделано:
### Создан манифест пода с distroless-образом `kyos0109/nginx-distroless:1.18.0` (`k8s/pod-distroless-nginx.yaml`)
### Задокументирована команда создания эфемерного контейнера с доступом к pid-namespace основного контейнера: `kubectl debug -it distroless-nginx -n debug-demo --image=nicolaka/netshoot --target=nginx -- bash`
### Задокументирован доступ к файловой системе отлаживаемого контейнера из эфемерного (`ls -la /proc/1/root/etc/nginx`)
### Задокументирован запуск `tcpdump -nn -i any -e port 80` в отладочном контейнере и способ сгенерировать трафик для проверки
### Задокументирована отладка ноды через `kubectl debug node/<node> -it --image=busybox` и получение логов пода с ноды напрямую из `/host/var/log/pods/...`
### Собран единый runbook со всеми командами по порядку (`scripts/debug_session.sh`)

## Задание с * (бонус):
### Задокументирован запуск `strace -p 1` для корневого процесса nginx: нужен профиль `--profile=sysadmin` у `kubectl debug` (дает `CAP_SYS_PTRACE`), а также общий pid-namespace с целевым контейнером (обеспечивается флагом `--target`)

## Как запустить проект:
### Выполнить по порядку команды из `scripts/debug_session.sh` на реальном кластере (minikube или Managed Kubernetes в Yandex Cloud — конфигурация кластера не имеет значения по условию задания)

## Как проверить работоспособность:
### Под `distroless-nginx` в статусе `Running`: `kubectl get pod -n debug-demo distroless-nginx`
### Эфемерный контейнер добавлен и виден в `kubectl describe pod -n debug-demo distroless-nginx` (секция `Ephemeral Containers`)
### `ls -la /proc/1/root/etc/nginx` внутри эфемерного контейнера показывает конфигурацию nginx
### `tcpdump` в эфемерном контейнере показывает пакеты при обращении к поду
### Логи пода читаются напрямую с диска ноды через отладочный под ноды

## PR checklist:
### Выставлен label с темой домашнего задания

---

Честный отчет о том, что реально проверено в этой песочнице (структура
манифестов), а что требует живого кластера (весь вывод команд отладки) —
в `../IMPLEMENTATION_REPORT.md`.

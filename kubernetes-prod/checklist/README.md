# Основное ДЗ

## В процессе сделано:
### Подготовлен скрипт подготовки узлов: отключение swap, br_netfilter/overlay, ip_forward, установка containerd, kubeadm, kubelet, kubectl (`scripts/00-common-prep.sh`)
### Подготовлен скрипт `kubeadm init` на master с установкой Flannel и выводом join-команды (`scripts/01-master-init.sh`)
### Подготовлен скрипт `kubeadm join` для worker-нод (`scripts/02-worker-join.sh`)
### Подготовлен скрипт обновления master через `kubeadm upgrade plan/apply` (`scripts/03-upgrade-master.sh`)
### Подготовлен скрипт последовательного обновления worker-нод: cordon → drain → `kubeadm upgrade node` → uncordon (`scripts/04-upgrade-worker.sh`)
### Задокументирован полный порядок действий и создание ВМ в Yandex Cloud (`docs/cloud/README.md`)

## Задание с * (бонус):
### Подготовлен inventory-файл kubespray для отказоустойчивого кластера (3 master + 2 worker) — `kubespray/inventory/hosts.yaml`
### Задокументирован запуск kubespray с этим inventory (`kubespray/README.md`)

## Как запустить проект:
### Выполнить по порядку `docs/cloud/README.md` (создание ВМ) и скрипты из `scripts/` в порядке 00 → 01 → 02 → (при обновлении) 03 → 04

## Как проверить работоспособность:
### После создания кластера: `kubectl get nodes -o wide` — все узлы в статусе `Ready`, версия соответствует одной ниже актуальной на момент выполнения
### После обновления: `kubectl get nodes -o wide` повторно — версия всех узлов обновлена до последней актуальной
### Для бонуса: `kubectl get nodes -o wide` на kubespray-кластере — минимум 3 узла с ролью `control-plane` и 2 с ролью `worker`, все `Ready`

## PR checklist:
### Выставлен label с темой домашнего задания

---

Честный отчет о том, что реально проверено в этой песочнице (структура и
согласованность скриптов/inventory), а что требует реальных ВМ (весь
вывод команд создания и обновления кластера) — в `../IMPLEMENTATION_REPORT.md`.

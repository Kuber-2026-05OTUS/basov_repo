# Основное ДЗ

## В процессе сделано:
### Подготовлены манифесты для Managed Kubernetes в Yandex Cloud (конфигурация нод не имеет значения по условию задания)
### Задокументировано создание бакета Yandex Object Storage (autoProvisioning — бакет создается CSI-драйвером на каждый том)
### Задокументировано создание IAM сервисного аккаунта с ролью `storage.editor` и генерация статического ключа доступа
### Создан манифест Secret с ключами доступа к Object Storage (`k8s/secret.example.yaml`)
### Создан манифест StorageClass с провижининг-драйвером `ru.yandex.s3.csi` (`k8s/storageclass.yaml`)
### Задокументирована установка CSI-драйвера `yandex-cloud/k8s-csi-s3` из репозитория (Helm-чарт и manual-манифесты)
### Создан манифест PVC с автоматическим провижинингом на основе StorageClass (`k8s/pvc.yaml`)
### Создан манифест Deployment, монтирующий PVC в `/data/s3` и записывающий в него данные каждые 5 секунд (`k8s/deployment.yaml`)

## Как запустить проект:
### Выполнить команды из `kubernetes-csi/docs/cloud/README.md` (разделы 4-5): создать бакет/сервисный аккаунт, поднять кластер, установить CSI-драйвер, затем:
```
kubectl apply -f kubernetes-csi/k8s/namespace.yaml
kubectl create secret generic csi-s3-secret -n kube-system --from-literal=accessKeyID=<key> --from-literal=secretAccessKey=<secret> --from-literal=endpoint=https://storage.yandexcloud.net --from-literal=region=ru-central1
kubectl apply -f kubernetes-csi/k8s/storageclass.yaml
kubectl apply -f kubernetes-csi/k8s/pvc.yaml
kubectl apply -f kubernetes-csi/k8s/deployment.yaml
```

## Как проверить работоспособность:
### Проверить, что PVC связан: `kubectl get pvc -n csi-s3-demo csi-s3-pvc` (должен быть `Bound`)
### Проверить запись в примонтированный каталог: `kubectl exec -n csi-s3-demo deploy/csi-s3-writer -- tail -n 5 /data/s3/heartbeat.log`
### Проверить, что файл реально появился в Object Storage: `yc storage s3api list-objects-v2 --bucket <имя автоматически созданного бакета>` (имя бакета совпадает с `volumeHandle` соответствующего PV)

## PR checklist:
### Выставлен label с темой домашнего задания

---

Полная таблица соответствия каждому пункту `docs/README.md` (включая, что проверено локальными тестами, а что требует реального облачного аккаунта) — в `../IMPLEMENTATION_REPORT.md`.

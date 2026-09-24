# Инструкция для администратора Yandex Cloud

Данная инструкция описывает шаги по работе с Yandex Cloud для развертывания
решения `kubernetes-csi` (CSI-драйвер для Yandex Object Storage). Она
написана по тому же образцу, что и `kubernetes-vault/docs/cloud/README.md`
и `kubernetes-demo/docs/cloud/README.md`, но проще по требованиям к
ресурсам кластера: конфигурация нод "не имеет значения" по условию задания,
основная часть работы — Object Storage, IAM и сам CSI-драйвер.

Ни один из шагов ниже не был выполнен агентом, готовившим репозиторий, —
реального аккаунта Yandex Cloud и реального запуска не было. Что именно
проверено локально (структурные тесты манифестов), а что нет,
зафиксировано в `../../IMPLEMENTATION_REPORT.md`.

## 1. Регистрация и оплата

1. Перейдите на сайт [Yandex Cloud](https://cloud.yandex.ru/) и авторизуйтесь с помощью Яндекс ID.
2. Перейдите в консоль управления (Консоль).
3. Создайте платежный аккаунт, если он еще не создан: "Биллинг" -> "Создать платежный аккаунт".
4. Привяжите банковскую карту для активации аккаунта (спишется и вернется небольшая сумма для проверки).

## 2. Применение студенческого ваучера на скидку

1. В консоли управления перейдите в раздел "Биллинг".
2. Выберите ваш платежный аккаунт.
3. Перейдите на вкладку "Промокоды" (или "Гранты").
4. Нажмите "Активировать промокод" и введите код студенческого ваучера.
5. Убедитесь, что грант зачислен на баланс. Средства гранта расходуются в первую очередь.

## 3. Как не потратить грант впустую

Задание прямо говорит, что конфигурация нод кластера не имеет значения —
это самый дешевый вариант из всей серии домашних заданий. Экономьте так же,
как и в остальных заданиях:

1. **Тип мастера:** **Базовый (1 хост)**, не Высокодоступный.
2. **Рабочие узлы:** 1-2 узла, **Прерываемые ВМ** (Preemptible), минимальная
   конфигурация (2 vCPU / 4 ГБ RAM хватает — сама нагрузка это тестовый
   busybox-контейнер).
3. **Object Storage:** тарифицируется отдельно от кластера (за объем
   хранимых данных и операции), но в рамках демонстрации данные — это
   один текстовый файл `heartbeat.log` в несколько КБ, поэтому расходы на
   хранение пренебрежимо малы. Не забудьте удалить бакет(ы) на шаге 6.
4. **Время жизни:** удаляйте кластер сразу после проверки задания —
   развернуть его заново для пересдачи занимает несколько минут.

Подробнее о тарифах: [Цены на Managed Service for Kubernetes](https://yandex.cloud/ru/docs/managed-kubernetes/pricing),
[Цены на Object Storage](https://yandex.cloud/ru/docs/storage/pricing).

## 3.1. Настройка security groups (обязательно)

Прежде чем ставить CSI-драйвер, убедитесь, что security groups кластера и
групп узлов настроены согласно
[рекомендациям Yandex Cloud для Managed Kubernetes](https://yandex.cloud/ru/docs/managed-kubernetes/operations/connect/security-groups) —
некорректные правила ломают доступность драйвера и подов, а диагностировать
это постфактум дольше, чем настроить заранее.

## 4. Создание бакета и сервисного аккаунта

1. **Бакет (опционально):** Object Storage -> "Создать бакет". Для этого
   демо бакет не обязателен заранее — `k8s/storageclass.yaml` не указывает
   `bucket` в параметрах, поэтому CSI-драйвер создаст отдельный бакет
   автоматически на каждый PVC (autoProvisioning). Создавайте бакет вручную
   только если хотите, чтобы все тома жили в одном общем бакете — тогда
   пропишите его имя в `parameters.bucket` `k8s/storageclass.yaml`.
2. **Сервисный аккаунт:**
   ```bash
   yc iam service-account create --name kubernetes-csi-sa
   yc resource-manager folder add-access-binding <folder-id> \
     --role storage.editor \
     --subject serviceAccount:$(yc iam service-account get kubernetes-csi-sa --format json | jq -r .id)
   ```
   Роль `storage.editor` — минимально достаточная для чтения/записи и
   создания бакетов (не используйте `admin` или `editor` на весь каталог).
3. **Статический ключ доступа:**
   ```bash
   yc iam access-key create --service-account-name kubernetes-csi-sa
   ```
   Сохраните `key_id` и `secret` из вывода команды — они одноразово
   показываются только при создании. Это значения для
   `k8s/secret.example.yaml` (`accessKeyID` / `secretAccessKey`).
   **Не коммитьте их в git** — только заполненную локальную копию для
   `kubectl apply -f -`, никогда сам файл в репозитории.

## 5. Развертывание кластера и CSI-драйвера

1. В консоли Yandex Cloud создайте Managed Kubernetes кластер (конфигурация
   нод — любая, см. раздел 3): "Managed Service for Kubernetes" ->
   "Создать кластер" -> Базовый мастер -> группа узлов 1-2 Прерываемых ВМ.
2. Настройте `kubectl`:
   ```bash
   yc managed-kubernetes cluster get-credentials <имя_кластера> --external
   ```
3. Создайте секрет с ключами доступа (используйте реальные значения из
   раздела 4, не значения-плейсхолдеры из репозитория):
   ```bash
   kubectl create namespace kube-system --dry-run=client -o yaml | kubectl apply -f -  # уже существует по умолчанию
   kubectl create secret generic csi-s3-secret \
     --namespace kube-system \
     --from-literal=accessKeyID='<реальный key_id>' \
     --from-literal=secretAccessKey='<реальный secret>' \
     --from-literal=endpoint='https://storage.yandexcloud.net' \
     --from-literal=region='ru-central1'
   ```
4. Установите CSI-драйвер (репозиторий `yandex-cloud/k8s-csi-s3`), любым из
   двух способов:

   **a) Helm-чарт (рекомендуется):**
   ```bash
   helm repo add yandex-s3 https://yandex-cloud.github.io/k8s-csi-s3/charts
   helm repo update
   helm install csi-s3 yandex-s3/csi-s3 \
     --namespace kube-system \
     -f ../../helm/csi-s3-values.yaml
   ```

   **b) Манифесты вручную (из upstream-репозитория, не из этой папки):**
   ```bash
   git clone https://github.com/yandex-cloud/k8s-csi-s3.git /tmp/k8s-csi-s3
   kubectl apply -f /tmp/k8s-csi-s3/deploy/kubernetes/provisioner.yaml
   kubectl apply -f /tmp/k8s-csi-s3/deploy/kubernetes/driver.yaml
   kubectl apply -f /tmp/k8s-csi-s3/deploy/kubernetes/csi-s3.yaml
   ```
   Оба контроллер и node DaemonSet выполняются в `kube-system` от имени
   драйвера и требуют `privileged` для FUSE-монтирования — это ограничение
   самого драйвера, не то, что можно ослабить, не сломав монтирование.
5. Дождитесь готовности драйвера:
   ```bash
   kubectl get pods -n kube-system -l app=csi-s3
   kubectl get pods -n kube-system -l app=csi-provisioner-s3
   ```
6. Примените ресурсы из этого репозитория:
   ```bash
   kubectl apply -f ../../k8s/namespace.yaml
   kubectl apply -f ../../k8s/storageclass.yaml
   kubectl apply -f ../../k8s/pvc.yaml
   kubectl apply -f ../../k8s/deployment.yaml
   ```

## 6. Проверка решения

1. Убедитесь, что PVC перешел в `Bound`:
   ```bash
   kubectl get pvc -n csi-s3-demo csi-s3-pvc
   ```
2. Проверьте, что под пишет в примонтированный каталог:
   ```bash
   kubectl exec -n csi-s3-demo deploy/csi-s3-writer -- tail -n 5 /data/s3/heartbeat.log
   ```
3. Найдите имя автоматически созданного бакета (совпадает с volume ID PV):
   ```bash
   kubectl get pv -o jsonpath='{.items[?(@.spec.claimRef.name=="csi-s3-pvc")].spec.csi.volumeHandle}'
   ```
4. Убедитесь, что файл `heartbeat.log` реально лежит в Object Storage —
   через консоль (Object Storage -> бакет -> файлы) или CLI:
   ```bash
   yc storage s3api list-objects-v2 --bucket <имя_бакета_из_шага_3>
   ```
   Размер объекта должен расти между повторными вызовами команды, пока
   под продолжает писать.

## 7. Отключение облака (удаление ресурсов)

Чтобы избежать лишних списаний после завершения работы:

1. Удалите демо-нагрузку — PVC с `reclaimPolicy: Delete` автоматически
   удалит и созданный бакет:
   ```bash
   kubectl delete -f ../../k8s/deployment.yaml -f ../../k8s/pvc.yaml -f ../../k8s/storageclass.yaml -f ../../k8s/namespace.yaml
   ```
2. Убедитесь, что автоматически созданный бакет действительно удален
   (Object Storage -> список бакетов); если использовался
   заранее созданный общий бакет (`parameters.bucket` в
   `storageclass.yaml`), удалите его вручную.
3. Удалите драйвер:
   ```bash
   helm uninstall csi-s3 -n kube-system
   ```
4. Удалите группу узлов и сам кластер:
   - "Managed Service for Kubernetes" -> кластер -> "Группы узлов" -> удалить группу.
   - На странице списка кластеров -> три точки напротив кластера -> "Удалить".
5. Удалите сервисный аккаунт и его статический ключ, если они больше не нужны:
   ```bash
   yc iam access-key list --service-account-name kubernetes-csi-sa
   yc iam access-key delete --id <key-id>
   yc iam service-account delete --name kubernetes-csi-sa
   ```
6. При необходимости удалите каталог (Folder), если он использовался
   только для этого задания.

# Terraform: `kubernetes-demo` → Yandex Cloud

## Назначение

Этот каталог добавляет автоматизацию только для `kubernetes-demo`. Существующие каталоги репозитория не используются как Terraform-модули и не изменяются.

Схема работы:

1. **VPS Beget / Ubuntu Server 22.04** — рабочее место администратора. Здесь запускаются `terraform`, `yc`, `kubectl`, `helm`, `docker`.
2. **Terraform** — создаёт VPC, security group, service accounts/IAM, Yandex Managed Kubernetes и worker node group, а также Yandex Container Registry.
3. **`scripts/deploy.sh`** — после `terraform apply` собирает два Docker-образа из исходников `kubernetes-demo`, публикует их в Container Registry и разворачивает Kubernetes-часть.
4. Kubernetes запускает MongoDB, Airflow, DAG CBR → PySpark → MongoDB, Streamlit и, по умолчанию, kube-prometheus-stack.

Актуальная документация Yandex Cloud подтверждает использование Terraform-ресурсов `yandex_kubernetes_cluster` и `yandex_kubernetes_node_group`, service accounts с ролями `k8s.clusters.agent`, `vpc.publicAdmin` и `container-registry.images.puller`, а также интеграцию Managed Kubernetes с приватным Yandex Container Registry через service account узлов.

> **Важно:** это учебный/демонстрационный стенд. По умолчанию worker-ноды preemptible. После проверки обязательно выполняйте `./scripts/destroy.sh`.

---

## 1. Что требуется до начала

### 1.1. VPS Beget

Чистый **Ubuntu Server 22.04 LTS**, рекомендуемый минимум:

- 2 vCPU;
- 4 ГБ RAM;
- 30+ ГБ свободного диска;
- исходящий HTTPS-доступ в Интернет;
- SSH-доступ администратора (`sudo`);
- Docker с возможностью выполнять `docker build` и `docker push`.

Terraform и Docker работают на VPS; сами Kubernetes-ноды создаются в Yandex Cloud.

### 1.2. Yandex Cloud

Нужны:

- активный billing account;
- Cloud ID;
- Folder ID;
- возможность создавать VPC, Managed Kubernetes, service accounts/IAM bindings и Container Registry;
- достаточный лимит ресурсов для 3 × 4 vCPU / 8 ГБ worker-нód.

Yandex Cloud рекомендует отдельный service account для ресурсов кластера с `k8s.clusters.agent` и `vpc.publicAdmin`, а для узлов — `container-registry.images.puller`.

### 1.3. GitHub

Исходники берутся из:

`https://github.com/Kuber-2026-05OTUS/basov_repo`

Ветка проекта: `kubernetes-demo`.

---

## 2. Обновление Ubuntu

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y ca-certificates curl git jq unzip openssl python3 python3-pip python3-venv
```

Проверьте:

```bash
lsb_release -a
python3 --version
```

Python 3.10+ подходит для административных скриптов. Docker, Terraform и Helm устанавливаются отдельными шагами ниже.

---

## 3. Установка Docker

```bash
sudo apt update
sudo apt install -y docker.io
sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"
```

Переподключитесь по SSH, чтобы группа `docker` обновилась, затем:

```bash
docker --version
docker run --rm hello-world
```

Если Docker требуется только через `sudo`, не запускайте весь Terraform от root — лучше исправьте членство пользователя в группе `docker`.

---

## 4. Установка Terraform

Установите актуальный Terraform из официального источника HashiCorp либо из зеркала, доступного в вашей сети. Для этого каталога требуется Terraform **>= 1.6.0**.

После установки:

```bash
terraform version
```

Официальный Yandex Cloud quickstart описывает стандартный цикл `init → plan → validate → apply → destroy`.

---

## 5. Установка Yandex Cloud CLI (`yc`)

Установите `yc` по актуальной инструкции Yandex Cloud, затем выполните интерактивную настройку:

```bash
yc init
```

Выберите OAuth/IAM-профиль, Cloud и Folder.

Проверка:

```bash
yc config list
```

Должны быть видны как минимум cloud-id и folder-id.

Для Terraform можно использовать короткоживущий IAM token:

```bash
export TF_VAR_yc_token="$(yc iam create-token)"
```

Не записывайте этот token в Git, `terraform.tfvars`, shell-скрипты или презентацию.

---

## 6. Установка kubectl

Установите актуальный `kubectl` из официального источника Kubernetes/Yandex Cloud.

Проверка:

```bash
kubectl version --client
```

После создания кластера kubeconfig будет получен командой:

```bash
yc managed-kubernetes cluster get-credentials --id <CLUSTER_ID> --external
```

---

## 7. Установка Helm 3

Установите Helm 3 из официального источника Helm.

Проверка:

```bash
helm version
```

Helm нужен для Apache Airflow и kube-prometheus-stack.

---

## 8. Получение проекта

Если проект ещё не скачан:

```bash
cd ~
git clone --branch kubernetes-demo https://github.com/Kuber-2026-05OTUS/basov_repo.git
cd ~/basov_repo/kubernetes-demo/terraform
```

Проверить структуру:

```bash
pwd
find . -maxdepth 2 -type f | sort
```

Важный принцип: **все новые файлы находятся внутри `kubernetes-demo/terraform`**.

---

## 9. Подготовка Terraform variables

Создайте локальный файл:

```bash
cp terraform.tfvars.example terraform.tfvars
chmod 600 terraform.tfvars
```

Откройте:

```bash
nano terraform.tfvars
```

Заполните:

```hcl
cloud_id  = "b1g..."
folder_id = "b1g..."

zone                = "ru-central1-a"
kubernetes_version  = "1.30"
node_count          = 3
node_cores          = 4
node_memory_gb      = 8
node_disk_gb        = 64
preemptible_nodes   = true
registry_name       = "kubernetes-demo"
image_tag           = "1.0.0"
enable_monitoring   = true
```

Если выбранная версия Kubernetes уже недоступна для `STABLE`, поменяйте `kubernetes_version` на доступную в вашем регионе/каталоге версию. Yandex Cloud сейчас документирует создание Managed Kubernetes через Terraform и указывает, что конкретные версии и параметры кластера должны соответствовать доступным ресурсам региона.

---

## 10. Проверка Terraform-конфигурации

```bash
terraform fmt -recursive
terraform init
terraform validate
```

Ожидаемый результат последней команды:

```text
Success! The configuration is valid.
```

Проверить план без создания ресурсов:

```bash
terraform plan
```

Рекомендуемый вариант — сохранить план:

```bash
terraform plan -out=tfplan
```

---

## 11. Что создаст `terraform apply`

Terraform создаёт:

1. VPC network;
2. subnet `10.20.0.0/16`;
3. security group;
4. service account для control-plane resources;
5. service account для worker nodes;
6. IAM bindings;
7. Managed Kubernetes cluster;
8. фиксированную node group из 3 узлов;
9. Yandex Container Registry;
10. два Container Repository — `streamlit` и `spark-job`.

Поддержка этих ресурсов соответствует актуальному Terraform reference Yandex Cloud.

---

## 12. Создание инфраструктуры

```bash
terraform apply tfplan
```

Подтвердите `yes`.

После завершения:

```bash
terraform output
```

Особенно полезны:

```bash
terraform output -raw cluster_id
terraform output -raw registry_id
terraform output -raw streamlit_image
terraform output -raw spark_image
```

Проверить кластер:

```bash
yc managed-kubernetes cluster get --id "$(terraform output -raw cluster_id)"
```

Проверить node group:

```bash
yc managed-kubernetes node-group list
```

---

## 13. Получение kubeconfig

```bash
yc managed-kubernetes cluster get-credentials \
  --id "$(terraform output -raw cluster_id)" \
  --external \
  --force
```

Проверка:

```bash
kubectl config current-context
kubectl get nodes
```

Все 3 worker-ноды должны перейти в `Ready`.

Yandex Cloud отдельно предупреждает, что для доступа worker-нód к Container Registry им нужен публичный IP либо NAT gateway/NAT instance; в этой конфигурации используется `nat = true` на интерфейсе worker-ноды.

---

## 14. Запуск `deploy.sh`

Сначала задайте пароль Grafana **в окружении VPS**, а не в Git:

```bash
export GRAFANA_ADMIN_PASSWORD='СЛОЖНЫЙ_ПАРОЛЬ'
```

При необходимости можно также заранее задать:

```bash
export MONGO_ROOT_USER='admin'
export MONGO_ROOT_PASSWORD='СЛОЖНЫЙ_ПАРОЛЬ_MONGODB'
```

Запуск:

```bash
./scripts/deploy.sh
```

Скрипт выполняет последовательно:

1. проверяет `terraform`, `yc`, `kubectl`, `helm`, `docker`, `git`;
2. настраивает Docker credential helper для Yandex Container Registry;
3. собирает Streamlit image из существующего `kubernetes-demo/streamlit_app/Dockerfile`;
4. собирает Spark image из `terraform/docker/spark-job.Dockerfile`;
5. отправляет оба image в созданный Registry;
6. получает внешний kubeconfig;
7. создаёт namespaces;
8. создаёт MongoDB admin secret и application secret;
9. создаёт Airflow Fernet/secret key;
10. разворачивает MongoDB;
11. устанавливает Apache Airflow Helm chart `1.15.0` с dev overlay, чтобы Postgres для учебного стенда создавался самим chart;
12. задаёт DAG GitSync на текущую ветку `kubernetes-demo` исходного репозитория;
13. передаёт имя Spark image через `SPARK_JOB_IMAGE`;
14. применяет RBAC и NetworkPolicy;
15. разворачивает Streamlit и заменяет placeholder image на реальный image из Registry;
16. при `ENABLE_MONITORING=true` устанавливает kube-prometheus-stack и ServiceMonitors;
17. выводит команды проверки и port-forward.

Yandex Cloud рекомендует именно service-account интеграцию для private Container Registry: node service account получает короткоживущий IAM-доступ без `imagePullSecret`.

---

## 15. Проверка Kubernetes

```bash
kubectl get nodes
kubectl get namespaces
kubectl get pods -A
```

Проверка MongoDB:

```bash
kubectl get pods -n data-platform
kubectl get pvc -n data-platform
```

Проверка Airflow:

```bash
kubectl get pods -n airflow
kubectl get svc -n airflow
```

Проверка Streamlit:

```bash
kubectl get pods -n data-platform -l app.kubernetes.io/name=streamlit
kubectl get svc -n data-platform streamlit
```

Проверка мониторинга:

```bash
kubectl get pods -n monitoring
kubectl get servicemonitor -n airflow
```

---

## 16. Доступ к UI через SSH port-forward

### Airflow

В первом SSH-сеансе:

```bash
kubectl port-forward -n airflow svc/airflow-webserver 8080:8080
```

В браузере откройте `http://127.0.0.1:8080`.

### Streamlit

```bash
kubectl port-forward -n data-platform svc/streamlit 8501:8501
```

В браузере:

`http://127.0.0.1:8501`

### Grafana

```bash
kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3000:80
```

В браузере:

`http://127.0.0.1:3000`

Логин Grafana по умолчанию: `admin`; пароль — значение `GRAFANA_ADMIN_PASSWORD`.

---

## 17. Проверка Airflow DAG

В Airflow UI найдите:

```text
cbr_rates_pipeline
```

Запустите DAG вручную.

Проверка CLI:

```bash
kubectl -n airflow exec deploy/airflow-webserver -- airflow dags list | grep cbr_rates_pipeline
```

Поды задач:

```bash
kubectl get pods -n data-platform
```

Проверка MongoDB:

```bash
kubectl exec -n data-platform -it mongodb-0 -- \
  mongosh --username "$MONGO_ROOT_USER" --password "$MONGO_ROOT_PASSWORD" \
  --authenticationDatabase admin \
  --eval 'db.getSiblingDB("currency").rates.find().sort({date:-1}).limit(10).pretty()'
```

Если переменные `MONGO_ROOT_*` были заданы только внутри `deploy.sh`, команда выше на другой SSH-сессии не знает пароль. В таком случае извлеките secret только для диагностики:

```bash
kubectl get secret -n data-platform mongodb-admin-credentials \
  -o jsonpath='{.data.MONGO_INITDB_ROOT_PASSWORD}' | base64 -d; echo
```

Не публикуйте полученное значение.

---

## 18. Мониторинг

Установленный стек:

- Prometheus;
- Grafana;
- Alertmanager;
- kube-state-metrics;
- node-exporter.

Airflow ServiceMonitors применяются из:

```text
kubernetes-demo/k8s/airflow/servicemonitor.yaml
```

Dashboard JSON находится в:

```text
kubernetes-demo/monitoring/grafana-dashboard-kubernetes-demo.json
```

Импортируйте его в Grafana вручную после port-forward.

---

## 19. Что делать, если ресурсов мало

Проверить незапланированные pod:

```bash
kubectl get pods -A --field-selector=status.phase=Pending
```

Проверить причины:

```bash
kubectl describe pod -n <namespace> <pod-name>
```

Для учебного стенда можно уменьшить:

```hcl
node_count      = 3
node_cores      = 4
node_memory_gb  = 8
```

Но снижение ниже 3 узлов × 4 vCPU × 8 ГБ может привести к `Pending` у Airflow/Prometheus. Исходный проект сам предупреждает о заметном потреблении ресурсов мониторингом и Airflow.

Если мониторинг не нужен:

```hcl
enable_monitoring = false
```

и при запуске:

```bash
export ENABLE_MONITORING=false
./scripts/deploy.sh
```

---

## 20. Важное ограничение текущего исходного DAG

В исходном `kubernetes-demo/dags/cbr_rates_dag.py` Spark task получает путь к файлу, который создаётся в другом Airflow task pod. Эти два pod не имеют автоматически общего filesystem.

Кроме того, текущий DAG передаёт `env_from=["mongodb-credentials"]`, тогда как KubernetesPodOperator ожидает Kubernetes `V1EnvFromSource`. Актуальная документация Airflow описывает `env_from` как список `V1EnvFromSource`.

В рамках условия **не менять остальные каталоги** я не переписывал исходный DAG. Для демонстрационного запуска `terraform/docker/spark-entrypoint.py` содержит совместимый fallback: если переданный DAG путь не существует в Spark pod, image получает USD/EUR/CNY непосредственно из CBR и создаёт входной JSON.

Это позволяет не менять исходные файлы репозитория, но для production рекомендуется отдельным изменением проекта:

- заменить локальный staging на object storage/PVC RWX;
- передавать Secret через типизированный `V1EnvFromSource`;
- закрепить Spark connector и image digest;
- использовать managed MongoDB и managed PostgreSQL для Airflow.

---

## 21. Удаление стенда

После завершения работы:

```bash
./scripts/destroy.sh
```

Скрипт:

1. удаляет ServiceMonitors;
2. удаляет Helm release monitoring;
3. удаляет Helm release Airflow;
4. удаляет NetworkPolicy/RBAC/Streamlit/MongoDB;
5. удаляет namespaces;
6. выполняет `terraform destroy`.

После destroy дополнительно проверьте Yandex Cloud Console:

- Managed Kubernetes;
- Compute Cloud disks;
- public IP/load balancers;
- Container Registry и images;
- VPC subnet/network;
- service accounts.

---

## 22. Работа со state

По умолчанию Terraform state хранится локально на Beget VPS:

```text
terraform.tfstate
```

Не удаляйте state во время работающей инфраструктуры. Для production перенесите state в удалённый backend с блокировкой и резервным копированием.

Файлы:

```text
terraform.tfstate*
terraform.tfvars
*.tfplan
```

добавлены в `.gitignore`.

---

## 23. Минимальная последовательность команд

Если VPS уже подготовлен:

```bash
cd ~/basov_repo/kubernetes-demo/terraform

export TF_VAR_yc_token="$(yc iam create-token)"
cp terraform.tfvars.example terraform.tfvars
nano terraform.tfvars

terraform fmt -recursive
terraform init
terraform validate
terraform plan -out=tfplan
terraform apply tfplan

export GRAFANA_ADMIN_PASSWORD='change-this-now'
./scripts/deploy.sh

kubectl get nodes
kubectl get pods -A
```

После демонстрации:

```bash
./scripts/destroy.sh
```

---

## 24. Источники

- Yandex Cloud: Terraform quickstart — https://yandex.cloud/en/docs/terraform/quickstart
- Yandex Cloud: создание Managed Kubernetes — https://yandex.cloud/en/docs/managed-kubernetes/operations/kubernetes-cluster/kubernetes-cluster-create
- Yandex Cloud: Terraform resource `yandex_kubernetes_cluster` — https://yandex.cloud/en/docs/terraform/resources/kubernetes_cluster
- Yandex Cloud: Terraform resource `yandex_kubernetes_node_group` — https://yandex.cloud/en/docs/terraform/resources/kubernetes_node_group
- Yandex Cloud: интеграция Managed Kubernetes с Container Registry — https://yandex.cloud/en/docs/managed-kubernetes/tutorials/container-registry
- Airflow: KubernetesPodOperator — https://airflow.apache.org/docs/apache-airflow-providers-cncf-kubernetes/8.4.1/operators.html

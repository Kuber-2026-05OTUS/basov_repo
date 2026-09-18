# Инструкция для администратора Yandex Cloud

Данная инструкция описывает шаги по работе с Yandex Cloud для развертывания
решения `kubernetes-demo` (Airflow + курсы ЦБ + PySpark + MongoDB +
Streamlit + мониторинг). Она написана по тому же образцу, что и
`kubernetes-vault/docs/cloud/README.md`, но учитывает специфику этого
проекта: здесь одновременно работают Airflow (несколько компонентов),
MongoDB, Streamlit и стек Prometheus/Grafana, поэтому требования к
ресурсам кластера заметно выше, чем в задании про Vault.

Ни один из шагов ниже не был выполнен агентом, готовившим репозиторий, —
реального аккаунта Yandex Cloud и реального запуска не было. Что именно
проверено локально (тесты, линтеры), а что нет, зафиксировано в
`../../IMPLEMENTATION_REPORT.md`.

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

## 3. Важно: как не потратить грант впустую

Этот проект тяжелее, чем типовое ДЗ на 3 маленьких ноды: одновременно
должны поместиться Airflow (webserver, scheduler, triggerer, минимум один
worker, Postgres метаданных, статсд-экспортер), MongoDB, 2 реплики
Streamlit и стек `kube-prometheus-stack` (Prometheus, Grafana,
Alertmanager, node-exporter, kube-state-metrics). Суммарные запросы
ресурсов (`requests`) всех этих подов — ориентировочно от 3 vCPU и 6 ГБ
RAM даже без учета Prometheus/Grafana, которые сами по себе просят еще
~1-1.5 vCPU и 2-3 ГБ RAM. Если поднять кластер с избыточным запасом
"на всякий случай" и забыть его удалить, грант в 1000 ₽ уйдет за
несколько часов.

Чтобы уложиться в лимит и максимально сэкономить:

1. **Тип мастера:** выбирайте **Базовый (1 хост)**, а не Высокодоступный —
   отказоустойчивость мастера для сдачи ДЗ не требуется (её обеспечивает
   сам Managed Kubernetes на уровне control plane, а не то, что вы
   выбираете здесь).
2. **Рабочие узлы:** используйте **Прерываемые ВМ** (Preemptible) — они
   стоят на ~70% дешевле обычных. Диски — `network-ssd` 40-64 ГБ (SSD
   нужен, потому что MongoDB и Postgres метаданных Airflow пишут на диск
   активнее, чем сервисы из задания про Vault).
3. **Количество и размер узлов:** 3 узла по 4 vCPU / 8 ГБ RAM — минимум,
   при котором Airflow, MongoDB, Streamlit и мониторинг одновременно
   планируются без вытеснения друг друга. Меньший кластер (например,
   3×2 vCPU) может держать под давлением поды в `Pending` из-за нехватки
   ресурсов, особенно после установки `kube-prometheus-stack`.
4. **Если бюджет совсем сжат:** временно уменьшите `resources.requests` в
   `airflow/values-dev.yaml` и `monitoring/prometheus-values.yaml` (или
   вовсе пропустите установку мониторинга — она не блокирует проверку
   основного пайплайна CBR -> PySpark -> MongoDB -> Streamlit) вместо
   того, чтобы увеличивать кластер.
5. **Время жизни:** главное правило — **сразу удаляйте кластер и группу
   узлов** сразу после того, как проверили решение (см. раздел 6). За
   час работы кластера такого размера с прерываемыми узлами спишется
   несколько десятков рублей, а не тысячи.

Подробнее о тарифах: [Цены на Managed Service for Kubernetes](https://yandex.cloud/ru/docs/managed-kubernetes/pricing)

## 4. Запуск решения (Managed Kubernetes)

1. В консоли Yandex Cloud перейдите в нужный каталог (Folder).
2. В меню слева выберите "Managed Service for Kubernetes" -> "Создать кластер".
3. Укажите имя кластера `kubernetes-demo`, выберите (или создайте) сервисные
   учетные записи для ресурсов и для узлов с ролями `editor` и
   `container-registry.images.puller`.
4. В блоке "Конфигурация мастера" укажите тип **Базовый (1 хост)**,
   release channel `stable`, версию Kubernetes 1.29+.
5. Нажмите "Создать кластер" и дождитесь статуса `Running`.
6. На вкладке "Группы узлов" нажмите "Создать группу узлов": фиксированный
   размер 3, конфигурация 4 vCPU / 8 ГБ RAM, диск `network-ssd` 40-64 ГБ,
   **Прерываемые ВМ**.
7. Дождитесь готовности узлов и настройте `kubectl`:
   ```bash
   yc managed-kubernetes cluster get-credentials kubernetes-demo --external
   ```
8. Создайте namespaces проекта:
   ```bash
   kubectl apply -f ../../k8s/namespaces.yaml
   ```
9. Заведите секреты (**никогда не коммитьте реальные значения в git** —
   структура ключей описана в `../../k8s/secrets/secret.example.yaml`):
   ```bash
   kubectl create secret generic mongodb-credentials \
     --namespace data-platform \
     --from-literal=MONGODB_URI="mongodb://<user>:<password>@<host>:27017/?authSource=admin" \
     --from-literal=MONGODB_USERNAME="<user>" \
     --from-literal=MONGODB_PASSWORD="<password>"

   kubectl create secret generic airflow-fernet-secret \
     --namespace airflow \
     --from-literal=AIRFLOW_FERNET_KEY="$(python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')" \
     --from-literal=AIRFLOW_SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
   ```
   Для продакшена вместо прямого `kubectl create secret` предпочтительнее
   Yandex Lockbox + External Secrets Operator (тот же паттерн, что в
   `kubernetes-vault`, только источник — Lockbox, а не Vault).
10. Разверните MongoDB (для сдачи ДЗ достаточно in-cluster варианта;
    для реальной эксплуатации — Yandex Managed Service for MongoDB):
    ```bash
    kubectl apply -f ../../k8s/mongodb/
    ```
11. Установите Airflow из официального Helm-чарта:
    ```bash
    helm repo add apache-airflow https://airflow.apache.org
    helm repo update
    helm upgrade --install airflow apache-airflow/airflow \
      --namespace airflow --create-namespace \
      --version 1.15.0 \
      -f ../../airflow/values.yaml \
      -f ../../airflow/values-prod.yaml
    ```
    Дождитесь `kubectl get pods -n airflow` со всеми подами
    `Running`/`Ready`, прежде чем накатывать RBAC/NetworkPolicy — часть
    CRD должна быть создана чартом заранее.
12. Примените RBAC и NetworkPolicy (namespaced-роли, без `cluster-admin`;
    default-deny + явные разрешения):
    ```bash
    kubectl apply -f ../../k8s/rbac/
    kubectl apply -f ../../k8s/network-policies/
    kubectl apply -f ../../k8s/airflow/networkpolicy.yaml
    kubectl apply -f ../../k8s/streamlit/networkpolicy.yaml
    kubectl apply -f ../../k8s/mongodb/networkpolicy.yaml
    ```
    Managed Kubernetes в Yandex Cloud по умолчанию использует Calico,
    который поддерживает `NetworkPolicy` из коробки — ставить отдельный
    CNI-плагин не нужно.
13. Соберите и опубликуйте образ Streamlit в Yandex Container Registry,
    затем разверните приложение:
    ```bash
    yc container registry create --name kubernetes-demo
    yc container registry configure-docker
    docker build -f ../../streamlit_app/Dockerfile -t cr.yandex/<registry-id>/streamlit:1.0.0 ../..
    docker push cr.yandex/<registry-id>/streamlit:1.0.0
    # обновите image в k8s/streamlit/deployment.yaml на опубликованный тег
    kubectl apply -f ../../k8s/streamlit/
    ```
14. Разверните мониторинг:
    ```bash
    helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
    helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
      --namespace monitoring --create-namespace \
      -f ../../monitoring/prometheus-values.yaml
    kubectl apply -f ../../k8s/airflow/servicemonitor.yaml
    ```
    Импортируйте `../../monitoring/grafana-dashboard-kubernetes-demo.json`
    в Grafana (`kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3000:80`).
15. DAG `cbr_rates_dag.py` подхватывается автоматически: Airflow настроен
    на `dags.gitSync` из ветки `kubernetes-demo`, каталог
    `kubernetes-demo/dags` (см. `../../airflow/values.yaml`) — вручную
    ничего заливать в контейнер не нужно.

## 5. Проверка решения

1. Убедитесь, что узлы готовы:
   ```bash
   kubectl get nodes
   ```
   Статус всех 3 узлов должен быть `Ready`.
2. Проверьте, что поды Airflow, MongoDB и Streamlit в состоянии
   `Running`/`Ready`:
   ```bash
   kubectl get pods -n airflow -n data-platform -n streamlit
   ```
3. В Airflow UI (`kubectl port-forward -n airflow svc/airflow-webserver 8080:8080`)
   включите и один раз запустите DAG `cbr_rates_dag`, дождитесь статуса
   `success`.
4. Проверьте, что данные попали в MongoDB:
   ```bash
   kubectl exec -n data-platform -it mongodb-0 -- \
     mongosh --eval 'db.getSiblingDB("cbr_rates").rates.find().sort({date:-1}).limit(3)'
   ```
5. Откройте Streamlit (`kubectl port-forward -n streamlit svc/streamlit 8501:8501`)
   и убедитесь, что видны текущие курсы USD/EUR/CNY и прогноз (или сообщение
   "Недостаточно исторических данных", если пайплайн отработал меньше 5
   рабочих дней).
6. Убедитесь, что метрики Airflow видны в Prometheus/Grafana согласно
   `../../monitoring/README.md`.

## 6. Отключение облака (удаление ресурсов)

Чтобы избежать лишних списаний после завершения работы:

1. Удалите Helm-релизы:
   ```bash
   helm uninstall airflow -n airflow
   helm uninstall kube-prometheus-stack -n monitoring
   ```
2. Удалите оставшиеся манифесты проекта:
   ```bash
   kubectl delete -f ../../k8s/
   ```
3. Удалите группу узлов Kubernetes:
   - В разделе "Managed Service for Kubernetes" выберите кластер `kubernetes-demo`.
   - На вкладке "Группы узлов" выберите группу и нажмите "Удалить".
4. Удалите сам кластер:
   - На странице списка кластеров нажмите на три точки напротив
     `kubernetes-demo` и выберите "Удалить".
5. Проверьте и при необходимости вручную удалите диски и балансировщики
   нагрузки в разделах "Compute Cloud" -> "Диски" и "Network Load
   Balancer" — обычно они удаляются вместе с кластером/сервисами
   Kubernetes, но лучше убедиться, что не осталось "осиротевших" ресурсов.
6. При необходимости удалите каталог (Folder), если он использовался
   только для этого задания.

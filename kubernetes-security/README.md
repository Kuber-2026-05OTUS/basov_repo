# Разбор домашнего задания: Kubernetes Security

## 0. Подготовка Windows машины (minikube + k9s)

### Чтобы minikube мог запуститься, надо:

1. Перезагрузить компьютер и зайти в BIOS/UEFI (Fn+F2, Fn+DEL или F12 при старте нажать).
2. Найти настройку виртуализации: она может называться Intel Virtualization Technology, VT-x, AMD-V, SVM Mode или Secure Virtual Machine.
3. Включить её, сохранить изменения и перезагрузить ПК.
4. Чтобы отключить быстрый запуск в Windows, надо открыть Панель управления → Электропитание → Действия кнопок питания, нажать «Изменение параметров, которые сейчас недоступны», снять галочку с «Включить быстрый запуск» и нажать «Сохранить изменения».
5. Скачать установщик QEMU для Windows с официального сайта: https://www.qemu.org/download/#windows
6. Установить qemu, обязательно отметив галочку "Add to PATH" при установке
7. Добавить через Win + R, введя sysdm.cpl и нажав Enter, перейдя на вкладку «Дополнительно» и нажав «Переменные среды» в разделе «Переменные среды пользователя» Path - изменить - в конце добавить c:\Program Files\qemu
8. Перезагрузить Windows

### Установка инструментов

```powershell
winget install Kubernetes.kubectl
winget install Kubernetes.minikube
winget install derailed.k9s
```

Проверка:

```powershell
kubectl version --client
minikube version
k9s version
```

Ожидаемый результат: все 3 команды выводят версии без ошибок.

### Запуск minikube из под Git Bash:

```text
minikube delete
minikube config set driver qemu2
minikube start
kubectl config current-context
kubectl get nodes
```

Ожидаемый результат:

- контекст переключен на `minikube`;
- минимум 1 node в статусе `Ready`.

### Запуск k9s (опционально, для контроля)

```powershell
k9s
```

Ожидаемый результат: открывается интерфейс кластера, видны namespace и pods.

---

## 1. Переход в директорию ДЗ

```powershell
cd .\kubernetes-security
```

Ожидаемый результат: все дальнейшие команды выполняются в папке `kubernetes-security`.

---

## 2. Применение namespace и RBAC

### Применение манифестов

```powershell
kubectl apply -f namespace.yaml
kubectl apply -f monitoring-rbac.yaml
kubectl apply -f cd-rbac.yaml
```

Ожидаемый результат:

- namespace `homework` создан;
- ServiceAccount `monitoring` и `cd` созданы;
- созданы роли и bindings.

### Проверка созданных объектов

```powershell
kubectl get sa -n homework
kubectl get rolebinding -n homework
kubectl get clusterrole monitoring-metrics-reader
kubectl get clusterrolebinding monitoring-metrics-reader
```

Ожидаемый результат:

- в `kubectl get sa -n homework` есть `monitoring` и `cd`;
- в `kubectl get rolebinding -n homework` есть `cd-admin`;
- есть `ClusterRole` и `ClusterRoleBinding` для чтения `/metrics`.

### Проверка прав ServiceAccount `monitoring` на `/metrics`

```powershell
kubectl auth can-i --as=system:serviceaccount:homework:monitoring get /metrics
```

Ожидаемый результат: `yes`.

---

## 3. Применение deployment и service

```powershell
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
```

Ожидаемый результат:

- deployment `homework-deployment` создан;
- сервис `homework-service` создан;
- pod запускаются под `ServiceAccount monitoring`.

### Проверка статуса workload

```powershell
kubectl get deploy,rs,pods,svc -n homework
kubectl rollout status deployment/homework-deployment -n homework
```

Ожидаемый результат:

- `AVAILABLE` у deployment равно желаемому количеству реплик;
- rollout завершен сообщением `successfully rolled out`.

### Проверка serviceAccount в pod

```powershell
kubectl get pods -n homework -l app=homework -o jsonpath="{.items[0].spec.serviceAccountName}"
```

Ожидаемый результат: `monitoring`.

---

## 4. Создание kubeconfig для ServiceAccount `cd`

```powershell
$clusterName = kubectl config view --minify -o jsonpath='{.clusters[0].name}'
$server = kubectl config view --minify -o jsonpath='{.clusters[0].cluster.server}'
$caData = kubectl config view --raw --minify -o jsonpath='{.clusters[0].cluster.certificate-authority-data}'
$token = kubectl -n homework create token cd --duration=24h

kubectl config set-cluster $clusterName --server=$server --certificate-authority-data=$caData --embed-certs=true --kubeconfig=.\kubeconfig-cd
kubectl config set-credentials cd --token=$token --kubeconfig=.\kubeconfig-cd
kubectl config set-context cd@homework --cluster=$clusterName --user=cd --namespace=homework --kubeconfig=.\kubeconfig-cd
kubectl config use-context cd@homework --kubeconfig=.\kubeconfig-cd
```

Ожидаемый результат:

- в папке появляется файл `kubeconfig-cd`;
- контекст `cd@homework` успешно создается.

### Проверка прав в новом kubeconfig

```powershell
kubectl --kubeconfig .\kubeconfig-cd auth can-i create deployment -n homework
kubectl --kubeconfig .\kubeconfig-cd auth can-i delete pod -n homework
```

Ожидаемый результат: для namespace `homework` команды возвращают `yes` (роль `admin`).

---

## 5. Генерация токена `cd` на 1 день

```powershell
kubectl -n homework create token cd --duration=24h | Out-File -Encoding ascii .\token
Get-Content .\token
```

Ожидаемый результат:

- в папке создан файл `token`;
- содержимое файла похоже на JWT (три части, разделенные точками).

---

## 6. Проверка задания со `*` (`/metrics.html`)

В `deployment.yaml` уже настроен init-контейнер, который:

1. Берет SA token из `/var/run/secrets/kubernetes.io/serviceaccount/token`;
2. Запрашивает `https://kubernetes.default.svc/metrics`;
3. Сохраняет ответ в `/work/metrics.html`.

Далее nginx отдает файл по пути `/metrics.html`.

### Проверка файла внутри pod

```powershell
$pod = kubectl get pod -n homework -l app=homework -o jsonpath="{.items[0].metadata.name}"
kubectl exec -n homework $pod -- ls -l /homework
kubectl exec -n homework $pod -- sh -c "wc -c /homework/metrics.html"
```

Ожидаемый результат:

- файл `/homework/metrics.html` существует;
- его размер больше 0 байт.

### Проверка через сервис

```powershell
kubectl -n homework port-forward svc/homework-service 8080:80
```

В отдельном окне PowerShell:

```powershell
curl http://127.0.0.1:8080/metrics.html
```

Ожидаемый результат: возвращается содержимое метрик Kubernetes API.

---

## 7. Полезные команды диагностики

```powershell
kubectl get events -n homework --sort-by=.metadata.creationTimestamp
kubectl describe pod -n homework $pod
kubectl logs -n homework $pod -c init-metrics
kubectl auth can-i --list --as=system:serviceaccount:homework:cd -n homework
```

Ожидаемый результат: по логам `init-metrics` видно успешный `curl` без ошибок авторизации.

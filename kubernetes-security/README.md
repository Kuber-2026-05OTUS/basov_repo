# Разбор домашнего задания: Kubernetes Security

## Что реализовано

- ServiceAccount `monitoring` в namespace `homework`.
- Права для `monitoring` на чтение не-ресурсного URL `/metrics` (через `ClusterRole` + `ClusterRoleBinding`).
- Deployment запускается под `serviceAccountName: monitoring`.
- ServiceAccount `cd` в namespace `homework`.
- `RoleBinding` для `cd` на встроенную роль `admin` в рамках namespace `homework`.
- Шаги для генерации `kubeconfig` для `cd`.
- Шаги для генерации токена для `cd` на 1 день в файл `token`.
- Задание со `*`: при старте pod запрашивает `/metrics`, сохраняет ответ в `metrics.html`, файл доступен через сервис по пути `/metrics.html`.

## Файлы

- `namespace.yaml`
- `monitoring-rbac.yaml`
- `cd-rbac.yaml`
- `deployment.yaml`
- `service.yaml`
- `.gitignore` (игнорирует локальные секреты `token` и `kubeconfig-cd`)

## Применение манифестов

```powershell
kubectl apply -f namespace.yaml
kubectl apply -f monitoring-rbac.yaml
kubectl apply -f cd-rbac.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
```

## Проверка прав ServiceAccount `monitoring`

```powershell
kubectl auth can-i --as=system:serviceaccount:homework:monitoring get /metrics
```

Ожидаемый результат: `yes`.

## Создание kubeconfig для ServiceAccount `cd`

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

Проверка:

```powershell
kubectl --kubeconfig .\kubeconfig-cd auth can-i create deployment -n homework
```

## Генерация токена `cd` на 1 день

```powershell
kubectl -n homework create token cd --duration=24h | Out-File -Encoding ascii .\token
```

Проверка содержимого:

```powershell
Get-Content .\token
```

## Проверка задания со `*`

Проброс порта сервиса:

```powershell
kubectl -n homework port-forward svc/homework-service 8080:80
```

В другом терминале:

```powershell
curl http://127.0.0.1:8080/metrics.html
```

Если файл виден, значит init-контейнер успешно получил `/metrics` и сохранил ответ в общий том.

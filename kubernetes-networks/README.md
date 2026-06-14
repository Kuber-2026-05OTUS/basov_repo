# Разбор домашнего задания: Kubernetes Networks

## 0. Подготовка Windows машины (Rancher Desktop + k3s + k9s)

### Чтобы кластер на Windows работал стабильно, надо:

1. Перезагрузить компьютер и зайти в BIOS/UEFI (Fn+F2, Fn+DEL или F12 при старте).
2. Найти и включить виртуализацию (Intel VT-x / AMD-V / SVM Mode).
3. В Windows включить компоненты `Virtual Machine Platform` и `Windows Subsystem for Linux`.
4. Перезагрузить Windows.

### Установка через winget (PowerShell от администратора)

```powershell
winget install Microsoft.WSL
winget install SUSE.RancherDesktop
winget install Kubernetes.kubectl
winget install Helm.Helm
winget install derailed.k9s
```

Полезные ссылки:

- Rancher Desktop: https://rancherdesktop.io/
- k3s: https://docs.k3s.io/
- k9s: https://k9scli.io/topics/install/
- kubectl: https://kubernetes.io/docs/tasks/tools/
- Helm: https://helm.sh/docs/intro/install/
- Gateway API: https://gateway-api.sigs.k8s.io/

### Настройка Rancher Desktop

1. Открыть Rancher Desktop.
2. В разделе Kubernetes включить `Enable Kubernetes`.
3. Container Engine выбрать `containerd`.
4. В Kubernetes version выбрать релиз с k3s (из стабильных выбрать latest).
5. Нажать `Apply` и дождаться статуса `Kubernetes is running`.

Проверка:

```powershell
kubectl config current-context
kubectl get nodes
```

### Запуск k9s

```powershell
k9s
```

## Возможные ошибки

### Конфигурация с Docker на WSL 

Переустановите WSL в версию 2 (Rancher Desktop поддерживает только WSL 2):

```powershell
# Откройте PowerShell и проверьте версии WSL
wsl --list --verbose

# Если версия WSL = 1, переключите на WSL 2
wsl --set-version rancher-desktop 2
wsl --set-version rancher-desktop-data 2

# Установите WSL 2 как версию по умолчанию для новых дистрибутивов
wsl --set-default-version 2
```

Обновите WSL:

```powershell
wsl --update
```

Перезапустите WSL и Rancher Desktop:

```powershell
# Полная остановка WSL
wsl --shutdown
```
Затем перезапустите Rancher Desktop через File -> Exit


Проверьте, что заглушка создана:

```text
mkdir -p ~/.kube
cat > ~/.kube/config <<EOF
apiVersion: v1
clusters: []
contexts: []
current-context: ""
kind: Config
preferences: {}
users: []
EOF
rm -rf ~/.kube/
```

Если ошибка сохраняется — зарегистрируйте дистрибутивы вручную:

```powershell
# Удалите старые записи
wsl --unregister rancher-desktop
wsl --unregister rancher-desktop-data

# Перезапустите Rancher Desktop — он создаст дистрибутивы заново
```

Дополнительно: сбросьте Winsock (если есть проблемы с сетью):

```powershell
netsh winsock reset
```

## 1. Подготовка namespace.yaml

Применение:

```powershell
kubectl apply -f namespace.yaml
```

## 2. Подготовка deployment.yaml

В `deployment.yaml`:

- `readinessProbe` переведена на `httpGet`;
- путь проверки `/index.html`;
- порт проверки `8000`.

Применение:

```powershell
kubectl apply -f deployment.yaml
```

## 3. Подготовка service.yaml

`service.yaml` описывает сервис `ClusterIP`, направляющий трафик на pod-ы deployment.

Применение:

```powershell
kubectl apply -f service.yaml
```

## 4. Установка Gateway API и Traefik

Установка CRD Gateway API:

```powershell
kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.5.1/standard-install.yaml
```

Установка Traefik (Gateway API provider):

```powershell
helm repo add traefik https://traefik.github.io/charts
helm repo update
helm upgrade --install traefik traefik/traefik -n traefik --create-namespace --set providers.kubernetesGateway.enabled=true --set providers.kubernetesCRD.enabled=false --set providers.kubernetesIngress.enabled=false
```

Проверка:

```powershell
kubectl get gatewayclass
kubectl get pods -n traefik
```

## 5. Подготовка gateway.yaml

`gateway.yaml` содержит:

- один listener;
- протокол `HTTP`;
- явное разрешение маршрутов из всех namespace (`allowedRoutes.namespaces.from: All`).

Применение:

```powershell
kubectl apply -f gateway.yaml
```

## 6. Подготовка httpRoute.yaml

`httpRoute.yaml` содержит:

- маршрутизацию хоста `homework.otus` на сервис;
- задание со `*`: rewrite `/homepage` -> `/index.html`.

Применение:

```powershell
kubectl apply -f httpRoute.yaml
```

## Запуск всего решения

```powershell
kubectl apply -f namespace.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f gateway.yaml
kubectl apply -f httpRoute.yaml
```

## Проверка работоспособности

Проверка ресурсов:

```powershell
kubectl get pods,svc,gateway,httproute -n homework
kubectl get gateway -n homework
kubectl get httproute -n homework
```

Проверка доступа через host header:

```powershell
kubectl -n traefik port-forward svc/traefik 8080:80
curl -H "Host: homework.otus" http://127.0.0.1:8080/index.html
curl -H "Host: homework.otus" http://127.0.0.1:8080/homepage
```

Если хотите проверять без `Host` header, добавьте в `C:\Windows\System32\drivers\etc\hosts`:

```text
127.0.0.1 homework.otus
```

и используйте:

```powershell
curl http://homework.otus:8080/index.html
curl http://homework.otus:8080/homepage
```

## FAQ: частая ошибка администратора

Ошибка:

```text
The connection to the server 127.0.0.1:6443 was refused - did you specify the right host or port?
```

Что сделать:

1. Проверить, что Rancher Desktop показывает `Kubernetes is running`.
2. Проверить контекст:

```powershell
kubectl config current-context
kubectl config get-contexts
```

3. Если контекст неактуален, переключить на контекст Rancher Desktop и повторить:

```powershell
kubectl get nodes
```

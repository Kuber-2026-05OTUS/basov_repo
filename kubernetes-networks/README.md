# Разбор домашнего задания: Kubernetes Networks

## Выполнено ДЗ №3

- Основное ДЗ
- Задание со *

## 0. Подготовка Windows машины

### Полезные ссылки для администратора Windows

- WSL: https://learn.microsoft.com/windows/wsl/install
- Установка k3s: https://docs.k3s.io/quick-start
- Установка kubectl: https://kubernetes.io/docs/tasks/tools/
- Установка Helm: https://helm.sh/docs/intro/install/
- Установка k9s: https://k9scli.io/topics/install/

### Установка WSL2 и Ubuntu (PowerShell от администратора)

```powershell
wsl --install
```

После перезагрузки открыть Ubuntu и выполнить:

```bash
sudo apt update && sudo apt upgrade -y
```

### Установка k3s в Ubuntu/WSL

```bash
curl -sfL https://get.k3s.io | sh -
sudo kubectl get nodes
```

Настройка kubeconfig для текущего пользователя:

```bash
mkdir -p $HOME/.kube
sudo cp /etc/rancher/k3s/k3s.yaml $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config
kubectl get nodes
```

### Установка и запуск k9s в Windows

```powershell
winget install derailed.k9s
k9s
```

## 1. В процессе сделано

- Изменена readiness-проба в `deployment.yaml` с `exec` на `httpGet` (`/index.html`, порт `8000`)
- Создан `service.yaml` типа `ClusterIP` для pod-ов приложения
- Установлен Gateway API controller Traefik
- Создан `gateway.yaml` (HTTP listener + `allowedRoutes.namespaces.from: All`)
- Создан `httpRoute.yaml` для хоста `homework.otus`
- Добавлено rewrite-правило для задания со `*`: `/homepage` -> `/index.html`

## 2. Как запустить проект

Из директории `kubernetes-networks`:

```powershell
kubectl apply -f namespace.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
```

Установка CRD Gateway API:

```bash
kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.5.1/standard-install.yaml
```

Установка Traefik с поддержкой Gateway API:

```bash
helm repo add traefik https://traefik.github.io/charts
helm repo update
helm upgrade --install traefik traefik/traefik \
  -n traefik \
  --create-namespace \
  --reset-values \
  --set providers.kubernetesGateway.enabled=true \
  --set providers.kubernetesCRD.enabled=false \
  --set providers.kubernetesIngress.enabled=false \
  --set service.spec.type=LoadBalancer \
  --set ports.web.port=8000 \
  --set ports.web.exposedPort=80 \
  --set gateway.listeners.web.port=8000
```

Применение Gateway и HTTPRoute:

```powershell
kubectl apply -f gateway.yaml
kubectl apply -f httpRoute.yaml
```

## 3. Как проверить работоспособность

Проверка ресурсов:

```powershell
kubectl get pods,svc,gateway,httproute -n homework
kubectl get gatewayclass
kubectl get pods -n traefik
```

Основной вариант доступа (через IP шлюза):

1. Узнать IP сервиса Traefik:

```bash
kubectl get svc traefik -n traefik
```

2. Добавить в `C:\Windows\System32\drivers\etc\hosts`:

```text
<gateway-ip> homework.otus
```

3. Проверить:

```powershell
curl http://homework.otus/index.html
curl http://homework.otus/homepage
```

Альтернативный вариант (через `port-forward`):

```text
127.0.0.1 homework.otus
```

```bash
kubectl -n traefik port-forward svc/traefik 80:80
```

```powershell
curl http://homework.otus/index.html
curl http://homework.otus/homepage
```

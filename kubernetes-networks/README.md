# Разбор домашнего задания: Kubernetes Networks

## 0. Подготовка Windows машины и запуск k3s

### Подготовка Windows ПК

Чтобы развернуть `k3s` на Windows, удобно использовать WSL2 (Ubuntu):

1. Включить виртуализацию в BIOS/UEFI (Intel VT-x / AMD-V).
2. Убедиться, что включены компоненты Windows: **Virtual Machine Platform** и **Windows Subsystem for Linux**.
3. Установить WSL и Ubuntu:

```powershell
wsl --install
```

4. После перезагрузки открыть Ubuntu в WSL и обновить пакеты:

```bash
sudo apt update && sudo apt upgrade -y
```

Полезные ссылки:
- WSL: https://learn.microsoft.com/windows/wsl/install
- Установка k3s: https://docs.k3s.io/quick-start
- Установка kubectl: https://kubernetes.io/docs/tasks/tools/
- Установка Helm: https://helm.sh/docs/intro/install/
- Установка k9s: https://k9scli.io/topics/install/

### Установка k3s (внутри Ubuntu/WSL)

```bash
curl -sfL https://get.k3s.io | sh -
sudo kubectl get nodes
```

Проверка kubeconfig для текущего пользователя:

```bash
mkdir -p $HOME/.kube
sudo cp /etc/rancher/k3s/k3s.yaml $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config
kubectl get nodes
```

### Установка k9s

В Windows PowerShell:

```powershell
winget install derailed.k9s
```

Запуск:

```powershell
k9s
```

## 1. Подготовка namespace.yaml

```powershell
kubectl apply -f namespace.yaml
```

## 2. Подготовка deployment.yaml

В `deployment.yaml` используется `readinessProbe` типа `httpGet` на URL `/index.html`.

```powershell
kubectl apply -f deployment.yaml
```

## 3. Подготовка service.yaml (ClusterIP)

```powershell
kubectl apply -f service.yaml
```

## 4. Установка Gateway API контроллера Traefik

```bash
helm repo add traefik https://traefik.github.io/charts
helm repo update
helm upgrade --install traefik traefik/traefik \
  --namespace traefik --create-namespace \
  --set providers.kubernetesGateway.enabled=true
```

Проверка:

```bash
kubectl get gatewayclass
kubectl get pods -n traefik
```

## 5. Подготовка gateway.yaml

Gateway создается с HTTP listener и разрешением маршрутов из всех namespace.

```powershell
kubectl apply -f gateway.yaml
```

## 6. Подготовка httpRoute.yaml

`HTTPRoute` маршрутизирует хост `homework.otus` в сервис `homework-service`.
Дополнительно сделано задание со `*`: rewrite `"/homepage"` в `"/index.html"`.

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

Проверка ресурсов:

```powershell
kubectl get all -n homework
kubectl get gateway -n homework
kubectl get httproute -n homework
```

## Настройка доступа по хосту homework.otus

Вариант для проверки с Windows-хоста:

1. Добавить в файл `C:\Windows\System32\drivers\etc\hosts` строку:

```text
127.0.0.1 homework.otus
```

2. Пробросить порт Traefik в отдельном терминале:

```bash
kubectl -n traefik port-forward svc/traefik 80:80
```

3. Проверка:

```powershell
curl http://homework.otus/index.html
curl http://homework.otus/homepage
```

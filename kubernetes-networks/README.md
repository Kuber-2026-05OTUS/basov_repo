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

Сноска 1: если на команде `kubectl get nodes` появляется ошибка `127.0.0.1:6443 connection refused`, см. раздел `FAQ` ниже (кратко: запустить `k3s`, выставить `KUBECONFIG=/etc/rancher/k3s/k3s.yaml`, при необходимости скопировать kubeconfig в `$HOME/.kube/config`).
Сноска 2: если ошибка появляется после запуска `kubectl get nodes` из Windows-терминала, см. раздел `FAQ` ниже (кратко: выполнять команды в Ubuntu/WSL, проверить `kubectl config current-context`, при необходимости переключиться на контекст `default` из k3s).

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

## 4. Вопросы и ответы (FAQ)

### Вопрос

При выполнении `sudo kubectl get nodes` получаю ошибку:

```text
Get "https://127.0.0.1:6443/api?timeout=32s": dial tcp 127.0.0.1:6443: connect: connection refused
The connection to the server 127.0.0.1:6443 was refused - did you specify the right host or port?
```

### Ответ

Обычно это означает, что `kubectl` смотрит в неверный `kubeconfig` (или k3s сервер не запущен).

Сделайте шаги по порядку внутри Ubuntu/WSL:

1. Проверить, что служба k3s запущена:

```bash
sudo systemctl status k3s
```

Если служба не запущена:

```bash
sudo systemctl start k3s
sudo systemctl enable k3s
```

2. Проверить, что API k3s слушает порт 6443:

```bash
sudo ss -lntp | grep 6443
```

3. Принудительно использовать kubeconfig k3s:

```bash
echo '' >> ~/.bashrc
echo 'export KUBECONFIG=/etc/rancher/k3s/k3s.yaml' >> ~/.bashrc
source ~/.bashrc
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
kubectl get nodes
```

4. Если без `sudo` не работает, скопировать kubeconfig в домашнюю директорию:

```bash
mkdir -p $HOME/.kube
sudo cp /etc/rancher/k3s/k3s.yaml $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config
sed -i 's#/etc/rancher/k3s/k3s.yaml#~/.kube/config#g' ~/.bashrc
source ~/.bashrc
kubectl get nodes
```

5. Если проблема осталась, перезапустить k3s:

```bash
sudo systemctl restart k3s
kubectl get nodes
```

### Вопрос

После запуска `kubectl get nodes` вижу ошибку:

```text
E0614 08:36:14.872010   22541 memcache.go:265] "Unhandled Error" err="couldn't get current server API group list: Get \"https://127.0.0.1:6443/api?timeout=32s\": dial tcp 127.0.0.1:6443: connect: connection refused"
The connection to the server 127.0.0.1:6443 was refused - did you specify the right host or port?
```

### Ответ

Это тот же класс проблемы, но часто причина в запуске `kubectl` не из Ubuntu/WSL или в неверном текущем контексте.

Проверьте:

1. Где запущена команда:
   - для k3s в WSL запускайте `kubectl` в Ubuntu/WSL, а не в отдельном Windows-контуре без настроенного kubeconfig.
2. Текущий контекст:

```bash
kubectl config current-context
kubectl config get-contexts
```

3. Если контекст не от k3s, переключить на `default`:

```bash
kubectl config use-context default
kubectl get nodes
```

4. Если контекстов нет или они некорректны, переустановить kubeconfig:

```bash
mkdir -p $HOME/.kube
sudo cp /etc/rancher/k3s/k3s.yaml $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config
export KUBECONFIG=$HOME/.kube/config
kubectl get nodes
```

Альтернативный вариант (через `port-forward`):

```bash
sudo nano /etc/hosts
```

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

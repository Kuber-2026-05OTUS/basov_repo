# Разбор домашнего задания: Kubernetes Monitoring

## 0. Запускаю Kubernetes через Rancher Desktop (k3s) с управлением через kubectl и k9s

### Подготовка Windows ПК

### Чтобы Rancher Desktop и k3s корректно запустились, надо:

1. Перезагрузить компьютер и зайти в BIOS/UEFI (Fn+F2, Fn+DEL или F12 при старте).
2. Найти настройку виртуализации: Intel Virtualization Technology, VT-x, AMD-V, SVM Mode или Secure Virtual Machine.
3. Включить виртуализацию, сохранить изменения и перезагрузить ПК.
4. Открыть PowerShell от имени администратора и включить WSL2:

```powershell
wsl --install
```

5. После установки WSL перезагрузить Windows.
6. Проверить, что WSL установлен и работает:

```powershell
wsl --status
wsl -l -v
```

### Устанавливаю Rancher Desktop, kubectl и k9s через winget

Запускаю в PowerShell:

```powershell
winget install -e --id SUSE.RancherDesktop
winget install -e --id Kubernetes.kubectl
winget install -e --id Derailed.k9s
```

Проверка, что утилиты доступны:

```powershell
kubectl version --client
k9s version
```

### Первичный запуск и настройка Rancher Desktop

1. Запустить Rancher Desktop из меню Start.
2. На первом экране выбрать:
   - `Container Engine`: `containerd` (или `dockerd`, если нужен Docker CLI);
   - `Enable Kubernetes`: включено;
   - `Kubernetes version`: стабильную версию по умолчанию.
3. Дождаться статуса `Kubernetes is running`.
4. В Settings -> Kubernetes проверить:
   - Kubernetes включен;
   - backend: `k3s`;
   - порт API-сервера по умолчанию не конфликтует с локальными сервисами.
5. В Settings -> WSL Integration включить интеграцию с используемым Linux-дистрибутивом (если работаете через WSL).

Проверка кластера:

```powershell
kubectl config current-context
kubectl get nodes -o wide
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


Проверьте, что заглушка создана
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

## 1. Создание namespace.yaml

Подготовка `namespace.yaml`:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: homework
```

Применение:

```powershell
kubectl apply -f namespace.yaml
```

## 2. Установка Prometheus Operator через Helm

Установка kube-prometheus-stack:

```powershell
helm install prometheus oci://ghcr.io/prometheus-community/charts/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace
```

Проверка установки:

```powershell
kubectl get pods -n monitoring
```

## 3. Создание configmap.yaml

Подготовка `configmap.yaml`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: nginx-conf
  namespace: homework
data:
  default.conf: |
    server {
        listen 80;
        server_name localhost;

        location / {
            root /usr/share/nginx/html;
            index index.html index.htm;
        }

        location /nginx_status {
            stub_status on;
            access_log off;
            allow 127.0.0.1;
            deny all;
        }
    }
```

Применение:

```powershell
kubectl apply -f configmap.yaml
kubectl get configmap -n homework
```

## 4. Создание deployment.yaml

Подготовка `deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-server
  namespace: homework
spec:
  replicas: 2
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "9113"
    spec:
      containers:

        - name: nginx
          image: nginx:1.31-trixie-perl
          ports:
            - containerPort: 80
              name: http
          volumeMounts:
            - name: nginx-config
              mountPath: /etc/nginx/conf.d/default.conf
              subPath: default.conf
          resources:
            limits:
              memory: 256Mi
              cpu: 500m
            requests:
              memory: 128Mi
              cpu: 250m

        - name: nginx-exporter
          image: nginx/nginx-prometheus-exporter:1.5.1
          args:
            - -nginx.scrape-uri=http://localhost/nginx_status
          ports:
            - containerPort: 9113
              name: metrics
          resources:
            limits:
              memory: 128Mi
              cpu: 200m
            requests:
              memory: 64Mi
              cpu: 100m

      volumes:
        - name: nginx-config
          configMap:
            name: nginx-conf
```

Применение:

```powershell
kubectl apply -f deployment.yaml
```

## 5. Создание service.yaml

Подготовка `service.yaml`:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: nginx-service
  namespace: homework
  labels:
    app: nginx
spec:
  selector:
    app: nginx
  ports:
    - name: http
      port: 80
      targetPort: 80
    - name: metrics
      port: 9113
      targetPort: 9113
  type: ClusterIP
```

Применение:

```powershell
kubectl apply -f service.yaml
kubectl get svc -n homework
```

## 6. Создание serviceMonitor.yaml

Подготовка `serviceMonitor.yaml`:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: nginx-monitor
  namespace: homework
  labels:
    app: nginx
    release: prometheus
spec:
  selector:
    matchLabels:
      app: nginx
  namespaceSelector:
    matchNames:
      - homework
  endpoints:
    - port: metrics
      path: /metrics
      interval: 30s
      scheme: http
```

Применение:

```powershell
kubectl apply -f serviceMonitor.yaml
```

## 7. Запуск всего решения

Из каталога `kubernetes-monitoring`:

```powershell
helm install prometheus oci://ghcr.io/prometheus-community/charts/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace
kubectl apply -f namespace.yaml
kubectl apply -f configmap.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f serviceMonitor.yaml
```

Проверка состояния:

```powershell
kubectl get pods -n homework
kubectl get svc -n homework
kubectl get pods -n monitoring
```

## 8. Проверка через Prometheus

Запускаю проброс порта:

```powershell
kubectl port-forward -n monitoring svc/prometheus-operated 9091:9090
```

В интерфейсе Prometheus:

- Открыть `http://localhost:9091`;
- Перейти в раздел `Status -> Targets`;
- Убедиться, что target `homework/nginx-service:9113` в статусе `UP`;
- В разделе `query` выбрать поиск по `nginx_up`.

Ожидаемый результат:

```text
nginx_up 1
```

## 9. Проверка через k9s

Запуск:

```powershell
k9s
```

В интерфейсе k9s:

- переключиться в namespace `homework`;
- проверить `pods`, `deployments`, `services`, `configmaps`;
- убедиться, что pod в статусе `Running` и рестартов нет.

## 10. Полезные команды администратора

```powershell
kubectl describe deployment nginx-server -n homework
kubectl describe pod -n homework <pod-name>
kubectl logs -n homework <pod-name>
kubectl logs -n homework <pod-name> -c nginx-exporter
kubectl delete -f serviceMonitor.yaml
kubectl delete -f service.yaml
kubectl delete -f deployment.yaml
kubectl delete -f configmap.yaml
kubectl delete -f namespace.yaml
```

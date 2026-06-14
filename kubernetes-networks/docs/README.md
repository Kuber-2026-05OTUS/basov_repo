# C. kubernetes-networks
# Методическое пособие: финальная версия
## Сетевое взаимодействие Pod, Service и Gateway API

## Краткая цель

- Настроить сервис `ClusterIP` для Deployment из прошлого ДЗ
- Подключить Gateway API через Traefik
- Настроить маршрутизацию на хост `homework.otus`
- Реализовать rewrite для задания со `*`: `/homepage` -> `/index.html`

## Пошаговая инструкция выполнения

1. Изменить readinessProbe в `deployment.yaml` на `httpGet` с URL `/index.html`
2. Создать `service.yaml` типа `ClusterIP` для подов приложения
3. Установить CRD Gateway API:

```bash
kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.5.1/standard-install.yaml
```

4. Установить Traefik с поддержкой Gateway API:

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

5. Создать `gateway.yaml`:
   - listener: HTTP
   - `allowedRoutes.namespaces.from: All`

6. Создать `httpRoute.yaml`:
   - host: `homework.otus`
   - маршрутизация в `homework-service`
   - rewrite `/homepage` -> `/index.html`

## Проверка результата

1. Проверить ресурсы:

```powershell
kubectl get pods,svc,gateway,httproute -n homework
kubectl get gatewayclass
kubectl get pods -n traefik
```

2. Добавить в `hosts` запись:

```text
<gateway-ip> homework.otus
```

3. Проверить маршрутизацию:

```powershell
curl http://homework.otus/index.html
curl http://homework.otus/homepage
```

## Рекомендуемые источники

- Документация Service: https://kubernetes.io/docs/concepts/services-networking/service/
- Документация probes: https://kubernetes.io/ru/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/
- Gateway API: https://kubernetes.io/docs/concepts/services-networking/gateway/
- Traefik Helm chart: https://github.com/traefik/traefik-helm-chart
- Traefik Kubernetes Gateway provider: https://doc.traefik.io/traefik/reference/install-configuration/providers/kubernetes/kubernetes-gateway/
- HTTP redirect/rewrite в Gateway API: https://gateway-api.sigs.k8s.io/guides/http-redirect-rewrite/

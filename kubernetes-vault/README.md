# kubernetes-vault

## Разбор домашнего задания: Vault и External Secrets Operator

### 1. Установка Consul
```bash
kubectl create namespace consul
helm repo add hashicorp https://helm.releases.hashicorp.com
helm install consul hashicorp/consul -n consul -f consul-values.yaml
```

### 2. Установка Vault
```bash
kubectl create namespace vault
helm install vault hashicorp/vault -n vault -f vault-values.yaml
```

### 3. Инициализация и распечатывание Vault
```bash
kubectl exec -n vault -it vault-0 -- vault operator init
# Сохранить Unseal Keys и Initial Root Token
kubectl exec -n vault -it vault-0 -- vault operator unseal <Unseal Key 1>
kubectl exec -n vault -it vault-0 -- vault operator unseal <Unseal Key 2>
kubectl exec -n vault -it vault-0 -- vault operator unseal <Unseal Key 3>
kubectl exec -n vault -it vault-1 -- vault operator unseal <Unseal Key 1>
...
```

### 4. Создание секрета в Vault
```bash
kubectl exec -n vault -it vault-0 -- /bin/sh
vault login <Initial Root Token>
vault secrets enable -path=otus kv
vault kv put otus/cred username='otus' password='asajkjkahs'
```

### 5. Настройка Kubernetes Auth
```bash
kubectl apply -f vault-auth-sa.yaml

# Внутри пода vault-0:
vault auth enable kubernetes

vault write auth/kubernetes/config \
    kubernetes_host="https://$KUBERNETES_SERVICE_HOST:$KUBERNETES_SERVICE_PORT"

vault policy write otus-policy /vault/userconfig/otus-policy/otus-policy.hcl # или скопировать содержимое файла

vault write auth/kubernetes/role/otus \
    bound_service_account_names=vault-auth \
    bound_service_account_namespaces=vault \
    policies=otus-policy \
    ttl=24h
```

### 6. Установка External Secrets Operator
```bash
helm repo add external-secrets https://charts.external-secrets.io
helm install external-secrets external-secrets/external-secrets -n vault --set installCRDs=true
```

### 7. Создание SecretStore и ExternalSecret
```bash
kubectl apply -f secret-store.yaml
kubectl apply -f external-secret.yaml
```

### Проверка
```bash
kubectl get secret otus-cred -n vault -o yaml
```
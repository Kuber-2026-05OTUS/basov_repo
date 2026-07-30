# Основное ДЗ
## В процессе сделано:
### Развернут Managed Kubernetes в Yandex Cloud (3 ноды)
### Установлен Consul в namespace consul (3 реплики)
### Установлен HashiCorp Vault в namespace vault в HA-режиме с Consul
### Vault инициализирован и распечатан
### Создан Secret Engine KV `otus/` и секрет `otus/cred`
### Настроена авторизация `auth/kubernetes` в Vault
### Создана политика `otus-policy` и роль `otus`
### Установлен External Secrets Operator в namespace vault
### Создан SecretStore для подключения к Vault
### Создан ExternalSecret для синхронизации секрета `otus-cred`

## Как запустить проект:
### Выполнить команды из `kubernetes-vault/README.md`

## Как проверить работоспособность:
### Проверить наличие секрета: `kubectl get secret otus-cred -n vault -o jsonpath='{.data.username}' | base64 --decode` (должно быть `otus`)

## PR checklist:
### Выставлен label с темой домашнего задания
# Выполнено ДЗ № 7

- [x] Основное ДЗ
- [x] Задание со *
- [x] Задание со **

## В процессе сделано:

- Подготовлен `crd.yaml` — CustomResourceDefinition `MySQL` (group `otus.homework`, version `v1`, plural `mysqls`) с обязательными строковыми полями `image`, `database`, `password`, `storage_size`.
- Подготовлен `security.yaml` (полные права на API-сервер — основное ДЗ) и `security-minimal.yaml` (минимальный набор прав — задание со *): `ServiceAccount`, `ClusterRole`, `ClusterRoleBinding`.
- Подготовлен `deployment.yaml` — Deployment оператора с образом `roflmaoinmysoul/mysql-operator:1.0.0`.
- Подготовлен `object-crd.yaml` — кастомный объект `kind: MySQL` (`mysql-demo`).
- Подготовлены файлы собственного оператора `build/mysql_operator.py` и `build/Dockerfile` на базе Kopf (задание со **).

## Как запустить проект:

### 1-ая часть

```bash
minikube delete && minikube start
cd kubernetes-operators
```

Применение манифестов:

```bash
kubectl apply -f crd.yaml
kubectl apply -f security.yaml
kubectl apply -f object-crd.yaml
kubectl apply -f deployment.yaml
```

### 2-ая часть

Деплой:

```bash
minikube delete && minikube start
cd kubernetes-operators
kubectl apply -f crd.yaml
kubectl apply -f security-minimal.yaml
kubectl apply -f object-crd.yaml
kubectl apply -f deployment.yaml
```

## Как проверить работоспособность:

### 1-ая часть

CRD создан:

```bash
kubectl get crd mysqls.otus.homework
```

```text
ubuntu@ubuntu-MS-7C52:~/otus/bralbral_repo$ kubectl get crd mysqls.otus.homework
NAME                   CREATED AT
mysqls.otus.homework   2026-06-28T08:08:12Z
```

Под оператора жив:

```bash
kubectl get pods -n default -l app=mysql-operator
```

```text
ubuntu@ubuntu-MS-7C52:~/otus/bralbral_repo$ kubectl get pods -n default -l app=mysql-operator
NAME                              READY   STATUS    RESTARTS   AGE
mysql-operator-85f8745779-5bhf6   1/1     Running   0          9m1s
```

Логи оператора (должны быть сообщения о создании ресурсов):

```bash
kubectl logs -n default deployment/mysql-operator
```

```text
ubuntu@ubuntu-MS-7C52:~/otus/bralbral_repo$ kubectl logs -n default deployment/mysql-operator
/usr/local/lib/python3.10/site-packages/kopf/_core/reactor/running.py:179: FutureWarning: Absence of either namespaces or cluster-wide flag will become an error soon. For now, switching to the cluster-wide mode for backward compatibility.
  warnings.warn("Absence of either namespaces or cluster-wide flag will become an error soon."
[2026-06-28 08:26:32,620] kopf._core.engines.a [INFO    ] Initial authentication has been initiated.
[2026-06-28 08:26:32,621] kopf.activities.auth [INFO    ] Activity 'login_via_client' succeeded.
[2026-06-28 08:26:32,621] kopf._core.engines.a [INFO    ] Initial authentication has finished.
[2026-06-28 08:26:32,849] kopf.objects         [INFO    ] [default/mysql-demo] Creating pv, pvc for mysql data and svc...
[2026-06-28 08:26:32,862] kopf.objects         [INFO    ] [default/mysql-demo] Creating mysql deployment...
[2026-06-28 08:26:32,873] kopf.objects         [INFO    ] [default/mysql-demo] Waiting for mysql deployment to become ready...
[2026-06-28 08:26:42,882] kopf.objects         [INFO    ] [default/mysql-demo] Waiting for mysql deployment to become ready...
[2026-06-28 08:26:52,890] kopf.objects         [INFO    ] [default/mysql-demo] Waiting for mysql deployment to become ready...
[2026-06-28 08:27:02,905] kopf.objects         [INFO    ] [default/mysql-demo] Waiting for mysql deployment to become ready...
[2026-06-28 08:27:12,920] kopf.objects         [INFO    ] [default/mysql-demo] Waiting for mysql deployment to become ready...
[2026-06-28 08:27:22,934] kopf.objects         [INFO    ] [default/mysql-demo] Waiting for mysql deployment to become ready...
[2026-06-28 08:27:32,949] kopf.objects         [INFO    ] [default/mysql-demo] Waiting for mysql deployment to become ready...
[2026-06-28 08:27:42,963] kopf.objects         [INFO    ] [default/mysql-demo] Waiting for mysql deployment to become ready...
[2026-06-28 08:27:52,977] kopf.objects         [INFO    ] [default/mysql-demo] MySQL instance mysql-demo and its children resources created!
[2026-06-28 08:27:52,979] kopf.objects         [INFO    ] [default/mysql-demo] Handler 'mysql_on_create' succeeded.
[2026-06-28 08:27:52,979] kopf.objects         [INFO    ] [default/mysql-demo] Creation is processed: 1 succeeded; 0 failed.
[2026-06-28 08:27:52,984] kopf.objects         [WARNING ] [default/mysql-demo] Patching failed with inconsistencies: (('remove', ('status',), {'mysql_on_create': {'message': 'MySQL instance mysql-demo and its children resources created!'}}, None),)
```

Логи `mysql-demo`:

```bash
kubectl logs -n default deployment/mysql-demo
```

```text
ubuntu@ubuntu-MS-7C52:~/otus/bralbral_repo$ kubectl logs -n default deployment/mysql-demo
2026-06-28 08:27:32+00:00 [Note] [Entrypoint]: Entrypoint script for MySQL Server 8.0.46-1.el9 started.
2026-06-28 08:27:33+00:00 [Note] [Entrypoint]: Switching to dedicated user 'mysql'
2026-06-28 08:27:33+00:00 [Note] [Entrypoint]: Entrypoint script for MySQL Server 8.0.46-1.el9 started.
2026-06-28 08:27:33+00:00 [Note] [Entrypoint]: Initializing database files
2026-06-28T08:27:33.211086Z 0 [Warning] [MY-011068] [Server] The syntax '--skip-host-cache' is deprecated and will be removed in a future release. Please use SET GLOBAL host_cache_size=0 instead.
2026-06-28T08:27:33.211149Z 0 [System] [MY-013169] [Server] /usr/sbin/mysqld (mysqld 8.0.46) initializing of server in progress as process 81
2026-06-28T08:27:33.215925Z 1 [System] [MY-013576] [InnoDB] InnoDB initialization has started.
2026-06-28T08:27:33.769905Z 1 [System] [MY-013577] [InnoDB] InnoDB initialization has ended.
2026-06-28T08:27:34.866389Z 6 [Warning] [MY-010453] [Server] root@localhost is created with an empty password ! Please consider switching off the --initialize-insecure option.
2026-06-28 08:27:37+00:00 [Note] [Entrypoint]: Database files initialized
2026-06-28 08:27:37+00:00 [Note] [Entrypoint]: Starting temporary server
2026-06-28T08:27:37.682176Z 0 [Warning] [MY-011068] [Server] The syntax '--skip-host-cache' is deprecated and will be removed in a future release. Please use SET GLOBAL host_cache_size=0 instead.
2026-06-28T08:27:37.683497Z 0 [System] [MY-010116] [Server] /usr/sbin/mysqld (mysqld 8.0.46) starting as process 125
2026-06-28T08:27:37.699165Z 1 [System] [MY-013576] [InnoDB] InnoDB initialization has started.
2026-06-28T08:27:37.904255Z 1 [System] [MY-013577] [InnoDB] InnoDB initialization has ended.
2026-06-28T08:27:38.101426Z 0 [Warning] [MY-010068] [Server] CA certificate ca.pem is self signed.
2026-06-28T08:27:38.101451Z 0 [System] [MY-013602] [Server] Channel mysql_main configured to support TLS. Encrypted connections are now supported for this channel.
2026-06-28T08:27:38.103900Z 0 [Warning] [MY-011810] [Server] Insecure configuration for --pid-file: Location '/var/run/mysqld' in the path is accessible to all OS users. Consider choosing a different directory.
2026-06-28T08:27:38.115980Z 0 [System] [MY-011323] [Server] X Plugin ready for connections. Socket: /var/run/mysqld/mysqlx.sock
2026-06-28T08:27:38.116017Z 0 [System] [MY-010931] [Server] /usr/sbin/mysqld: ready for connections. Version: '8.0.46'  socket: '/var/run/mysqld/mysqld.sock'  port: 0  MySQL Community Server - GPL.
2026-06-28 08:27:38+00:00 [Note] [Entrypoint]: Temporary server started.
'/var/lib/mysql/mysql.sock' -> '/var/run/mysqld/mysqld.sock'
Warning: Unable to load '/usr/share/zoneinfo/iso3166.tab' as time zone. Skipping it.
Warning: Unable to load '/usr/share/zoneinfo/leap-seconds.list' as time zone. Skipping it.
Warning: Unable to load '/usr/share/zoneinfo/leapseconds' as time zone. Skipping it.
Warning: Unable to load '/usr/share/zoneinfo/tzdata.zi' as time zone. Skipping it.
Warning: Unable to load '/usr/share/zoneinfo/zone.tab' as time zone. Skipping it.
Warning: Unable to load '/usr/share/zoneinfo/zone1970.tab' as time zone. Skipping it.
2026-06-28 08:27:39+00:00 [Note] [Entrypoint]: Creating database otusdb

2026-06-28 08:27:39+00:00 [Note] [Entrypoint]: Stopping temporary server
2026-06-28T08:27:39.185308Z 11 [System] [MY-013172] [Server] Received SHUTDOWN from user root. Shutting down mysqld (Version: 8.0.46).
2026-06-28T08:27:40.926965Z 0 [System] [MY-010910] [Server] /usr/sbin/mysqld: Shutdown complete (mysqld 8.0.46)  MySQL Community Server - GPL.
2026-06-28 08:27:41+00:00 [Note] [Entrypoint]: Temporary server stopped

2026-06-28 08:27:41+00:00 [Note] [Entrypoint]: MySQL init process done. Ready for start up.

2026-06-28T08:27:41.410426Z 0 [Warning] [MY-011068] [Server] The syntax '--skip-host-cache' is deprecated and will be removed in a future release. Please use SET GLOBAL host_cache_size=0 instead.
2026-06-28T08:27:41.411616Z 0 [System] [MY-010116] [Server] /usr/sbin/mysqld (mysqld 8.0.46) starting as process 1
2026-06-28T08:27:41.415558Z 1 [System] [MY-013576] [InnoDB] InnoDB initialization has started.
2026-06-28T08:27:41.629493Z 1 [System] [MY-013577] [InnoDB] InnoDB initialization has ended.
2026-06-28T08:27:41.787155Z 0 [Warning] [MY-010068] [Server] CA certificate ca.pem is self signed.
2026-06-28T08:27:41.787177Z 0 [System] [MY-013602] [Server] Channel mysql_main configured to support TLS. Encrypted connections are now supported for this channel.
2026-06-28T08:27:41.789474Z 0 [Warning] [MY-011810] [Server] Insecure configuration for --pid-file: Location '/var/run/mysqld' in the path is accessible to all OS users. Consider choosing a different directory.
2026-06-28T08:27:41.801107Z 0 [System] [MY-011323] [Server] X Plugin ready for connections. Bind-address: '::' port: 33060, socket: /var/run/mysqld/mysqlx.sock
2026-06-28T08:27:41.801138Z 0 [System] [MY-010931] [Server] /usr/sbin/mysqld: ready for connections. Version: '8.0.46'  socket: '/var/run/mysqld/mysqld.sock'  port: 3306  MySQL Community Server - GPL.
```

Оператор создал Deployment для MySQL, Service, PVC и PV:

```bash
kubectl get deploy -n default | grep mysql
```

```text
ubuntu@ubuntu-MS-7C52:~/otus/bralbral_repo$ kubectl get deploy -n default | grep mysq
mysql-demo       1/1     1            1           8m57s
mysql-operator   1/1     1            1           10m
```

Service:

```bash
kubectl get svc -n default | grep mysql
```

```text
ubuntu@ubuntu-MS-7C52:~/otus/bralbral_repo$ kubectl get svc -n default | grep mysql
mysql-demo   ClusterIP   None         <none>        3306/TCP   9m11s
```

PVC:

```bash
kubectl get pvc -n default | grep mysql
```

```text
ubuntu@ubuntu-MS-7C52:~/otus/bralbral_repo$ kubectl get pvc -n default | grep mysql
mysql-demo-pvc   Bound    mysql-demo-pv   1Gi        RWO            standard       <unset>                 9m27s
```

PV:

```bash
kubectl get pv | grep mysql
```

```text
ubuntu@ubuntu-MS-7C52:~/otus/bralbral_repo$ kubectl get pv | grep mysql
mysql-demo-pv   1Gi        RWO            Retain           Bound    default/mysql-demo-pvc   standard       <unset>                          9m54s
```

Удаление:

```bash
kubectl delete mysql mysql-demo -n default
```

Проверка:

```bash
kubectl get deploy,svc,pvc -n default | grep mysql
kubectl get pv | grep mysql
```

```text
ubuntu@ubuntu-MS-7C52:~/otus/bralbral_repo$ kubectl get pv | grep mysql
No resources found
```

### 2-ая часть

Чек ошибок:

```bash
kubectl logs -n default deployment/mysql-operator --tail=50
kubectl logs -n default deployment/mysql-demo --tail=50
```

Чек созданных ресурсов:

```bash
kubectl get deploy,svc,pvc -n default | grep mysql
kubectl get pv | grep mysql
```

Чек удаления:

```bash
kubectl delete mysql mysql-demo -n default
kubectl get deploy,svc,pvc -n default | grep mysql
kubectl get pv | grep mysql
```

### 3-ая часть

## PR checklist:

- [x] Выставлен label с темой домашнего задания

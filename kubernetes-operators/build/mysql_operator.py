import kopf
import kubernetes
import yaml
from kubernetes.client.rest import ApiException

@kopf.on.create('otus.homework', 'v1', 'mysqls')
def mysql_on_create(body, spec, **kwargs):
    name = body['metadata']['name']
    namespace = body['metadata']['namespace']
    image = spec['image']
    password = spec['password']
    database = spec['database']
    storage_size = spec['storage_size']

    # PersistentVolume
    pv_name = f"{name}-pv"
    pv = {
        "apiVersion": "v1",
        "kind": "PersistentVolume",
        "metadata": {
            "name": pv_name,
            "labels": {
                "app": name
            }
        },
        "spec": {
            "capacity": {
                "storage": storage_size
            },
            "accessModes": ["ReadWriteOnce"],
            "hostPath": {
                "path": f"/data/{name}"
            }
        }
    }

    # PersistentVolumeClaim
    pvc_name = f"{name}-pvc"
    pvc = {
        "apiVersion": "v1",
        "kind": "PersistentVolumeClaim",
        "metadata": {
            "name": pvc_name,
            "namespace": namespace,
            "labels": {
                "app": name
            }
        },
        "spec": {
            "accessModes": ["ReadWriteOnce"],
            "resources": {
                "requests": {
                    "storage": storage_size
                }
            },
            "selector": {
                "matchLabels": {
                    "app": name
                }
            }
        }
    }

    # Service
    svc_name = f"{name}-svc"
    svc = {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {
            "name": svc_name,
            "namespace": namespace,
            "labels": {
                "app": name
            }
        },
        "spec": {
            "ports": [
                {
                    "port": 3306,
                    "targetPort": 3306
                }
            ],
            "selector": {
                "app": name
            },
            "type": "ClusterIP"
        }
    }

    # Deployment
    deploy_name = f"{name}-deployment"
    deploy = {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {
            "name": deploy_name,
            "namespace": namespace,
            "labels": {
                "app": name
            }
        },
        "spec": {
            "replicas": 1,
            "selector": {
                "matchLabels": {
                    "app": name
                }
            },
            "template": {
                "metadata": {
                    "labels": {
                        "app": name
                    }
                },
                "spec": {
                    "containers": [
                        {
                            "name": "mysql",
                            "image": image,
                            "env": [
                                {
                                    "name": "MYSQL_ROOT_PASSWORD",
                                    "value": password
                                },
                                {
                                    "name": "MYSQL_DATABASE",
                                    "value": database
                                }
                            ],
                            "ports": [
                                {
                                    "containerPort": 3306
                                }
                            ],
                            "volumeMounts": [
                                {
                                    "name": "mysql-data",
                                    "mountPath": "/var/lib/mysql"
                                }
                            ]
                        }
                    ],
                    "volumes": [
                        {
                            "name": "mysql-data",
                            "persistentVolumeClaim": {
                                "claimName": pvc_name
                            }
                        }
                    ]
                }
            }
        }
    }

    # Привязываем создаваемые ресурсы к нашему Custom Resource (для автоматического удаления)
    kopf.adopt(pvc)
    kopf.adopt(svc)
    kopf.adopt(deploy)

    api = kubernetes.client.CoreV1Api()
    apps_api = kubernetes.client.AppsV1Api()

    # Создаем PV (он cluster-scoped, поэтому kopf.adopt может работать некорректно для него, удалим вручную при удалении CR)
    try:
        api.create_persistent_volume(body=pv)
    except ApiException as e:
        if e.status != 409:
            raise

    # Создаем PVC
    try:
        api.create_namespaced_persistent_volume_claim(namespace=namespace, body=pvc)
    except ApiException as e:
        if e.status != 409:
            raise

    # Создаем Service
    try:
        api.create_namespaced_service(namespace=namespace, body=svc)
    except ApiException as e:
        if e.status != 409:
            raise

    # Создаем Deployment
    try:
        apps_api.create_namespaced_deployment(namespace=namespace, body=deploy)
    except ApiException as e:
        if e.status != 409:
            raise

    return {'message': f'MySQL {name} created successfully'}

@kopf.on.delete('otus.homework', 'v1', 'mysqls')
def mysql_on_delete(body, **kwargs):
    name = body['metadata']['name']
    
    api = kubernetes.client.CoreV1Api()
    
    # Удаляем PV вручную, так как он cluster-scoped
    pv_name = f"{name}-pv"
    try:
        api.delete_persistent_volume(name=pv_name)
    except ApiException as e:
        if e.status != 404:
            raise

    return {'message': f'MySQL {name} deleted successfully'}

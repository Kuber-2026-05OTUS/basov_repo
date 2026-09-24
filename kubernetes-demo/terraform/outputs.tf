output "cluster_id" {
  description = "Managed Kubernetes cluster ID."
  value       = yandex_kubernetes_cluster.demo.id
}

output "cluster_name" {
  value = yandex_kubernetes_cluster.demo.name
}

output "subnet_id" {
  value = yandex_vpc_subnet.demo.id
}

output "registry_id" {
  description = "Yandex Container Registry ID."
  value       = yandex_container_registry.demo.id
}

output "streamlit_image" {
  value = "cr.yandex/${yandex_container_registry.demo.id}/streamlit:${var.image_tag}"
}

output "spark_image" {
  value = "cr.yandex/${yandex_container_registry.demo.id}/spark-job:${var.image_tag}"
}

output "kubectl_credentials_command" {
  value = "yc managed-kubernetes cluster get-credentials --id ${yandex_kubernetes_cluster.demo.id} --external"
}

output "streamlit_port_forward" {
  value = "kubectl port-forward -n data-platform svc/streamlit 8501:8501"
}

output "airflow_port_forward" {
  value = "kubectl port-forward -n airflow svc/airflow-webserver 8080:8080"
}

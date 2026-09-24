resource "yandex_container_registry" "demo" {
  name      = var.registry_name
  folder_id = var.folder_id

  labels = {
    project = "kubernetes-demo"
  }
}

resource "yandex_container_repository" "streamlit" {
  name = "${yandex_container_registry.demo.id}/streamlit"
}

resource "yandex_container_repository" "spark_job" {
  name = "${yandex_container_registry.demo.id}/spark-job"
}

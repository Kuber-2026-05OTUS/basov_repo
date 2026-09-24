resource "yandex_iam_service_account" "cluster" {
  name        = "${var.cluster_name}-cluster-sa"
  description = "Service account used by Yandex Managed Kubernetes control plane resources."
}

resource "yandex_iam_service_account" "nodes" {
  name        = "${var.cluster_name}-node-sa"
  description = "Service account used by Kubernetes worker nodes to pull images from Container Registry."
}

resource "yandex_resourcemanager_folder_iam_member" "cluster_agent" {
  folder_id = var.folder_id
  role      = "k8s.clusters.agent"
  member    = "serviceAccount:${yandex_iam_service_account.cluster.id}"
}

resource "yandex_resourcemanager_folder_iam_member" "cluster_vpc_public_admin" {
  folder_id = var.folder_id
  role      = "vpc.publicAdmin"
  member    = "serviceAccount:${yandex_iam_service_account.cluster.id}"
}

resource "yandex_resourcemanager_folder_iam_member" "node_registry_puller" {
  folder_id = var.folder_id
  role      = "container-registry.images.puller"
  member    = "serviceAccount:${yandex_iam_service_account.nodes.id}"
}

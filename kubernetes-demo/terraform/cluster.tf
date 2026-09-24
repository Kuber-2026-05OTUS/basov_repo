resource "yandex_kubernetes_cluster" "demo" {
  name        = var.cluster_name
  description = "kubernetes-demo: Airflow + PySpark + MongoDB + Streamlit + monitoring"
  network_id  = yandex_vpc_network.demo.id

  master {
    version = var.kubernetes_version

    zonal {
      zone      = yandex_vpc_subnet.demo.zone
      subnet_id = yandex_vpc_subnet.demo.id
    }

    public_ip          = true
    security_group_ids = [yandex_vpc_security_group.k8s.id]
  }

  service_account_id      = yandex_iam_service_account.cluster.id
  node_service_account_id = yandex_iam_service_account.nodes.id

  cluster_ipv4_range = var.cluster_ipv4_range
  service_ipv4_range = var.service_ipv4_range
  release_channel    = "STABLE"

  depends_on = [
    yandex_resourcemanager_folder_iam_member.cluster_agent,
    yandex_resourcemanager_folder_iam_member.cluster_vpc_public_admin,
    yandex_resourcemanager_folder_iam_member.node_registry_puller,
  ]

  timeouts {
    create = "45m"
    update = "45m"
    delete = "45m"
  }
}

resource "yandex_kubernetes_node_group" "demo" {
  cluster_id  = yandex_kubernetes_cluster.demo.id
  name        = "${var.cluster_name}-nodes"
  description = "Worker nodes for the kubernetes-demo lab"
  version     = var.kubernetes_version

  instance_template {
    platform_id = "standard-v3"

    resources {
      cores  = var.node_cores
      memory = var.node_memory_gb
    }

    boot_disk {
      type = "network-ssd"
      size = var.node_disk_gb
    }

    scheduling_policy {
      preemptible = var.preemptible_nodes
    }

    container_runtime {
      type = "containerd"
    }

    network_interface {
      nat               = true
      subnet_ids        = [yandex_vpc_subnet.demo.id]
      security_group_ids = [yandex_vpc_security_group.k8s.id]
    }
  }

  scale_policy {
    fixed_scale {
      size = var.node_count
    }
  }

  allocation_policy {
    location {
      zone = var.zone
    }
  }

  deploy_policy {
    max_expansion   = 1
    max_unavailable = 1
  }

  maintenance_policy {
    auto_upgrade = true
    auto_repair  = true
  }

  timeouts {
    create = "45m"
    update = "45m"
    delete = "45m"
  }
}

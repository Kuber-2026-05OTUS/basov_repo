resource "yandex_vpc_network" "demo" {
  name = "${var.cluster_name}-network"
}

resource "yandex_vpc_subnet" "demo" {
  name           = "${var.cluster_name}-subnet"
  zone           = var.zone
  network_id     = yandex_vpc_network.demo.id
  v4_cidr_blocks = [var.network_cidr]
}

resource "yandex_vpc_security_group" "k8s" {
  name       = "${var.cluster_name}-sg"
  network_id = yandex_vpc_network.demo.id

  ingress {
    description    = "Kubernetes API from the Internet"
    protocol       = "TCP"
    port           = 443
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "All cluster-internal traffic"
    protocol    = "ANY"
    from_port   = 0
    to_port     = 65535
    predefined_target = "self_security_group"
  }

  egress {
    description    = "Internet and cluster egress"
    protocol       = "ANY"
    from_port      = 0
    to_port        = 65535
    v4_cidr_blocks = ["0.0.0.0/0"]
  }
}

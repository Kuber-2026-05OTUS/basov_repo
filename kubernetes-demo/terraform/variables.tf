variable "cloud_id" {
  description = "Yandex Cloud cloud ID."
  type        = string
}

variable "folder_id" {
  description = "Yandex Cloud folder ID where the demo will be created."
  type        = string
}

variable "yc_token" {
  description = "Yandex Cloud IAM token. Prefer YC_TOKEN environment variable via TF_VAR_yc_token."
  type        = string
  sensitive   = true
  default     = null
}

variable "zone" {
  description = "Availability zone for the single-zone lab cluster."
  type        = string
  default     = "ru-central1-a"
}

variable "cluster_name" {
  description = "Managed Kubernetes cluster name."
  type        = string
  default     = "kubernetes-demo"
}

variable "kubernetes_version" {
  description = "Kubernetes minor version available in the selected Yandex Cloud release channel."
  type        = string
  default     = "1.30"
}

variable "network_cidr" {
  description = "Subnet CIDR for worker nodes."
  type        = string
  default     = "10.20.0.0/16"
}

variable "cluster_ipv4_range" {
  description = "Pod CIDR. Must not overlap with the worker subnet."
  type        = string
  default     = "10.21.0.0/16"
}

variable "service_ipv4_range" {
  description = "Kubernetes Service CIDR. Must not overlap with VPC ranges."
  type        = string
  default     = "10.22.0.0/16"
}

variable "node_count" {
  description = "Fixed number of worker nodes."
  type        = number
  default     = 3
}

variable "node_cores" {
  description = "vCPU per worker node."
  type        = number
  default     = 4
}

variable "node_memory_gb" {
  description = "RAM in GB per worker node."
  type        = number
  default     = 8
}

variable "node_disk_gb" {
  description = "Worker boot disk size in GB. Yandex Cloud Managed Kubernetes currently requires at least 64 GB."
  type        = number
  default     = 64
}

variable "preemptible_nodes" {
  description = "Use preemptible worker VMs to reduce lab cost."
  type        = bool
  default     = true
}

variable "registry_name" {
  description = "Yandex Container Registry name."
  type        = string
  default     = "kubernetes-demo"
}

variable "image_tag" {
  description = "Immutable application image tag used by the deployment script."
  type        = string
  default     = "1.0.0"
}

variable "grafana_admin_password" {
  description = "Grafana admin password used only by deploy.sh. Not stored in Terraform files."
  type        = string
  sensitive   = true
  default     = null
}

variable "enable_monitoring" {
  description = "Install kube-prometheus-stack. Disable to reduce lab resource consumption."
  type        = bool
  default     = true
}

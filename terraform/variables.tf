variable "project_id" {
  description = "GCP project ID"
  type        = string
  default     = "image-editing-488312"
}

variable "zone" {
  description = "GCP zone"
  type        = string
  default     = "us-central1-a"
}

variable "cluster_name" {
  description = "GKE cluster name"
  type        = string
  default     = "comfyui-cluster"
}



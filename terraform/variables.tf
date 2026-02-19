variable "project_name" {
  description = "Project name prefix for resources"
  type        = string
  default     = "devops-core"
}

variable "cloud_id" {
  description = "Yandex Cloud ID"
  type        = string
}

variable "folder_id" {
  description = "Yandex Cloud folder ID"
  type        = string
}

variable "zone" {
  description = "Availability zone"
  type        = string
  default     = "ru-central1-a"
}

variable "subnet_cidr" {
  description = "Subnet CIDR"
  type        = string
  default     = "10.10.0.0/24"
}

variable "allowed_ssh_cidr" {
  description = "CIDR block allowed to SSH to VM"
  type        = string
}

variable "ssh_username" {
  description = "Username configured for SSH login"
  type        = string
  default     = "ubuntu"
}

variable "ssh_public_key_path" {
  description = "Path to public SSH key file"
  type        = string
}

variable "image_family" {
  description = "Image family for VM boot disk"
  type        = string
  default     = "ubuntu-2404-lts"
}

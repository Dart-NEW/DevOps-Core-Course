terraform {
  required_version = ">= 1.9.0"

  required_providers {
    yandex = {
      source  = "yandex-cloud/yandex"
      version = "~> 0.130"
    }
  }
}

provider "yandex" {
  zone      = var.zone
  folder_id = var.folder_id
  cloud_id  = var.cloud_id
}

data "yandex_compute_image" "ubuntu" {
  family = var.image_family
}

resource "yandex_vpc_network" "lab04" {
  name = "${var.project_name}-network"
}

resource "yandex_vpc_subnet" "lab04" {
  name           = "${var.project_name}-subnet"
  zone           = var.zone
  network_id     = yandex_vpc_network.lab04.id
  v4_cidr_blocks = [var.subnet_cidr]
}

resource "yandex_vpc_security_group" "lab04" {
  name       = "${var.project_name}-sg"
  network_id = yandex_vpc_network.lab04.id

  ingress {
    description    = "SSH from trusted CIDR"
    protocol       = "TCP"
    port           = 22
    v4_cidr_blocks = [var.allowed_ssh_cidr]
  }

  ingress {
    description    = "HTTP"
    protocol       = "TCP"
    port           = 80
    v4_cidr_blocks = [var.allowed_ssh_cidr]
  }

  ingress {
    description    = "Custom app port"
    protocol       = "TCP"
    port           = 5000
    v4_cidr_blocks = [var.allowed_ssh_cidr]
  }

  egress {
    description    = "Allow all outbound traffic"
    protocol       = "ANY"
    from_port      = 0
    to_port        = 65535
    v4_cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "yandex_compute_instance" "lab04_vm" {
  name        = "${var.project_name}-vm"
  hostname    = "${var.project_name}-vm"
  platform_id = "standard-v2"
  zone        = var.zone

  resources {
    cores         = 2
    memory        = 1
    core_fraction = 20
  }

  boot_disk {
    initialize_params {
      image_id = data.yandex_compute_image.ubuntu.id
      size     = 10
      type     = "network-hdd"
    }
  }

  network_interface {
    subnet_id          = yandex_vpc_subnet.lab04.id
    nat                = true
    security_group_ids = [yandex_vpc_security_group.lab04.id]
  }

  metadata = {
    ssh-keys = "${var.ssh_username}:${file(var.ssh_public_key_path)}"
  }

  labels = {
    project = var.project_name
    lab     = "lab04"
    tool    = "terraform"
  }
}

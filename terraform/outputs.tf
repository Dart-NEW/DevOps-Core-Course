output "vm_public_ip" {
  description = "Public IPv4 address of the VM"
  value       = yandex_compute_instance.lab04_vm.network_interface[0].nat_ip_address
}

output "vm_internal_ip" {
  description = "Internal IPv4 address of the VM"
  value       = yandex_compute_instance.lab04_vm.network_interface[0].ip_address
}

output "ssh_command" {
  description = "Convenient SSH command"
  value       = "ssh ${var.ssh_username}@${yandex_compute_instance.lab04_vm.network_interface[0].nat_ip_address}"
}

# Terraform (Lab 4)

## What is created
- Yandex VPC network and subnet
- Security group with ports 22, 80, 5000
- VM (standard-v2, 2 cores, 20% CPU, 1 GB RAM, 10 GB HDD)
- Public IP via NAT on VM network interface

## Prerequisites
- Terraform >= 1.9
- Yandex Cloud account and configured auth (`yc init`)
- SSH key pair on local machine

## Quick start
```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
# fill terraform.tfvars with your values

terraform init
terraform fmt
terraform validate
terraform plan
terraform apply
```

## Access
After `terraform apply`:
```bash
terraform output vm_public_ip
terraform output ssh_command
```

Then connect by SSH:
```bash
ssh ubuntu@<public_ip>
```

## Destroy
```bash
terraform destroy
```

## Important
- Never commit `terraform.tfvars` and any `*.tfstate*`
- Keep credentials only in local environment/config

# Terraform GitHub Import (Lab 4 Bonus)

## Purpose
Import an already existing GitHub repository into Terraform state and manage key settings.

## Steps
```bash
cd terraform/github-import
cp terraform.tfvars.example terraform.tfvars
# fill owner/token values

terraform init
terraform import github_repository.course_repo DevOps-Core-Course
terraform plan
terraform apply
```

## Notes
- Use a GitHub PAT with `repo` scope
- Never commit `terraform.tfvars` or state files
- If import succeeds, `terraform plan` should show either no changes or only intended metadata differences

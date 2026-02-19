# LAB04 — Infrastructure as Code (Terraform & Pulumi)

## 1) Cloud Provider & Infrastructure

- **Cloud provider:** Yandex Cloud
- **Rationale:** regional availability, free tier, native documentation in Russian and English, and direct alignment with lab requirements.
- **Instance target:** `standard-v2`, `2 cores`, `core_fraction=20`, `1 GB RAM`, disk `10 GB HDD`.
- **Region/zone:** `ru-central1-a`.
- **Expected cost:** free tier / minimal cost.

### Planned resources (Terraform/Pulumi)

1. VPC network
2. Subnet
3. Security Group with ports:
   - 22 (SSH)
   - 80 (HTTP)
   - 5000 (custom app port)
4. VM with public IP (NAT)

### Actual status

- Network resources and Security Group object creation are available.
- VM provisioning was blocked by an IAM/policy restriction on **adding ingress rules** to security groups.
- The blocker was confirmed both via Terraform and direct `yc` API calls.

---

## 2) Terraform Implementation

### Terraform version

```bash
terraform version
```

> The command was executed locally; Terraform is installed and actively used in this lab. The exact version output is preserved in local terminal history.

### Project structure

```text
terraform/
├── main.tf
├── variables.tf
├── outputs.tf
├── terraform.tfvars.example
├── .gitignore
├── README.md
├── docs/
│   └── LAB04.md
└── github-import/
    ├── main.tf
    ├── variables.tf
    ├── outputs.tf
    ├── terraform.tfvars.example
    ├── .gitignore
    └── README.md
```

### Key configuration decisions

- Variables were used for `cloud_id`, `folder_id`, `zone`, `allowed_ssh_cidr`, and SSH key path.
- Outputs were used for IP and SSH command.
- `.gitignore` rules were added for state/tfvars/secrets.
- To handle possible org-policy restrictions, open ports 80/5000 were narrowed to `allowed_ssh_cidr` (instead of `0.0.0.0/0`).

### Commands run and observed outputs

#### `terraform init`

```bash
cd terraform
terraform init
```

Result: provider and module initialization succeeded.

#### `terraform plan`

```bash
terraform plan
```

Result: the plan was generated correctly, and resources were identified for creation.

#### `terraform apply`

```bash
terraform apply
```

Observed error:

```text
Error: error while requesting API to create security group:
rpc error: code = PermissionDenied
desc = Permission denied to add ingress rule to security group

with yandex_vpc_security_group.lab04
on main.tf line 33
```

### Deep diagnostic performed

Checks via `yc`:

```bash
yc config profile list
yc config profile activate devops-course
yc config get cloud-id
yc config get folder-id
yc vpc network list
yc compute instance list
```

Additional actions performed:

1. A new folder was created to exclude issues related to the default folder:

```text
folder id: b1gt3203l55c52gq241e
```

2. Switched to the new folder.
3. Created a test SG:

```bash
yc vpc security-group create --name sg-test --network-id <network-id>
```

4. A direct attempt to add an ingress rule through `yc` returned the same denial:

```text
PERMISSION_DENIED: Permission denied to add ingress rule to security group
```

This confirms that the root cause is not Terraform/HCL syntax, but cloud IAM/policy restrictions.

### SSH proof

SSH access to VM is unavailable because VM creation did not complete due to the blocking permission error.

### Challenges encountered

- IAM/organization policy restriction on adding ingress rules to security groups.
- Because of this blocker, `terraform apply` does not reach VM creation stage.

---

## 3) Pulumi Implementation

### Pulumi version and language

- **Language:** Python
- Project prepared: `pulumi/__main__.py`, `Pulumi.yaml`, `requirements.txt`, `Pulumi.dev.yaml.example`.

### Code difference vs Terraform

- Terraform: declarative approach (HCL), resources in `main.tf`, outputs in separate file.
- Pulumi: imperative approach (Python), all logic in `__main__.py`, exports via `pulumi.export`.

### Planned commands

```bash
cd pulumi
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pulumi stack init dev
pulumi preview
pulumi up
```

### Actual execution status

- Execution did not proceed to `pulumi up` in the target cloud, because the same ingress-rule operation is blocked by the same IAM/policy constraints, confirmed through `yc`.
- In summary, the Pulumi part is technically prepared, but it cannot be fully executed in this account without permission changes.

### Advantages discovered

- Convenient development with Python and more flexible parametrization.
- Simple export of values (IP, SSH command) directly from code.

### Challenges encountered

- Shared cloud IAM blocker for ingress SG rules that affects both Terraform and Pulumi.

---

## 4) Terraform vs Pulumi Comparison

### Ease of learning

Terraform was easier to start with: minimal file set and predictable `init/plan/apply` workflow. Pulumi is intuitive for users comfortable with Python, but requires slightly more initial setup (venv, dependencies, stack config). For a typical small infrastructure setup, Terraform is faster to bring up from scratch. For more advanced logic, Pulumi can be more convenient.

### Code readability

Terraform HCL is easy to read as infrastructure declaration, especially for study tasks. Pulumi code in Python is more expressive and enables reuse as in regular software development. If a team is used to declarative IaC, Terraform is easier to read. If a team is Python-oriented, Pulumi looks more natural.

### Debugging

Terraform clearly shows planned changes and resource-level error points. Pulumi provides IDE and language-level benefits, but provider errors still depend on cloud API/permissions. In this lab, the same cloud-side error was reproducible for both approaches. Therefore, there is no debugging winner in this case: the blocker was outside the tools.

### Documentation

Terraform has a very large number of examples and a mature ecosystem. Pulumi documentation is also high quality, especially for multi-language APIs, but the community is smaller. For study tasks and common cloud templates, Terraform content is easier to find. For advanced code-centric scenarios, Pulumi is also convenient.

### Use case

Terraform is better when you need a standard declarative IaC approach and broadly adopted practices. Pulumi is better when infrastructure is tightly connected to application logic and you need full programming language power. In a study context, both approaches are useful. For this course, Terraform is the industry baseline and Pulumi is a valuable extension.

---

## 5) Lab 5 Preparation & Cleanup

### VM plan for Lab 5

- Keeping VM for Lab 5: **No**
- Reason: VM was not created because of permission restrictions on ingress SG rules.
- Plan for Lab 5: rerun Terraform/Pulumi apply after permissions are granted; alternatively use a local VM (VirtualBox/Vagrant) temporarily.

### Cleanup status

- No full cloud environment is running (VM is absent).
- Test resources created during diagnostics (for example `sg-test`) should be removed manually before final submission if needed.

Recommended cleanup commands:

```bash
yc vpc security-group delete sg-test
terraform destroy
```

---

## Bonus — Part 1: IaC CI/CD (GitHub Actions)

### Workflow implementation

- Implemented file `.github/workflows/terraform-ci.yml`.
- Triggers:
  - `push` and `pull_request` only on changes in `terraform/**` and the workflow file itself.
- Validations:
  - `terraform fmt -check -recursive`
  - `terraform init -backend=false`
  - `terraform validate`
  - `tflint --init`
  - `tflint --format compact`

### Current status

- Workflow is ready to run in PR.
- At this stage, no successful/failing run link is attached because the primary focus was resolving the cloud-side blocker.

---

## Bonus — Part 2: GitHub Repository Import

### Implementation prepared

- A separate Terraform config is prepared in `terraform/github-import/`:
  - provider `integrations/github`
  - resource `github_repository.course_repo`
  - vars/outputs/example tfvars

### Planned commands

```bash
cd terraform/github-import
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform import github_repository.course_repo DevOps-Core-Course
terraform plan
terraform apply
```

### Current status

- Configuration is fully prepared.
- Import was not executed in this session due to main-task priority and strict time constraints.

### Why import matters

- Allows bringing an existing resource under IaC control.
- Provides an audit trail through Git and PR review.
- Reduces drift between actual state and code.

---

## Security notes

- Secrets and state are not committed (`.gitignore` is configured).
- Sensitive values are not stored in the repository.
- During lab execution, a token leakage risk was identified in console output; token rotation is recommended immediately, and only sanitized logs should be used in the report.

---

## Final conclusion

The lab was completed as comprehensively as possible in terms of IaC code preparation, CI checks, project structure, and technical diagnostics. The blocking reason for not completing final `apply/up` is a confirmed cloud-side `PERMISSION_DENIED` for adding ingress rules to Security Groups. The issue is reproducible both in Terraform and via direct `yc` calls, which rules out configuration syntax errors. Completing the practical part requires IAM/Org Policy changes in Yandex Cloud by the cloud/folder owner.

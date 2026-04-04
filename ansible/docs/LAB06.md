# Lab 6: Advanced Ansible & CI/CD - Submission

**Name:** Oleynik Maxim
**Date:** 2026-03-05  
**Lab Points:** 10 (+ bonus optional)

---

## Overview

Implemented a full Lab 6 migration from container `docker run` style deployment to Docker Compose-based deployment using Ansible roles. Added block/rescue/always patterns with tags, role dependency management, safe wipe logic with variable + tag gating, and GitHub Actions automation for lint + deploy + verification.

Technologies used: **Ansible 2.x**, **community.docker**, **Docker Compose v2**, **GitHub Actions**, **Jinja2**.

---

## Task 1: Blocks & Tags (2 pts)

### Implemented Changes

- `roles/common/tasks/main.yml`
  - Package + timezone operations moved into one `block` tagged `packages`
  - `rescue` added for apt failures (`apt-get update --fix-missing`)
  - `always` added to log completion to `/tmp/ansible-common-role.log`
  - User management block added and tagged `users`
- `roles/docker/tasks/main.yml`
  - Docker install flow moved into `block` tagged `docker_install`
  - `rescue` added for Docker GPG/network-related retry flow with 10s wait
  - `always` ensures Docker service is enabled/started
  - Docker user/python package configuration grouped/tagged as `docker_config`
- `playbooks/provision.yml`
  - Role-level tags added: `common`, `docker`

### Tag Strategy

- `common`: whole common role (role-level)
- `packages`: common package tasks
- `users`: common user tasks
- `docker`: whole docker role (role-level)
- `docker_install`: docker installation tasks
- `docker_config`: docker configuration tasks

### Execution Examples

```bash
ansible-playbook playbooks/provision.yml --list-tags
ansible-playbook playbooks/provision.yml --tags "docker"
ansible-playbook playbooks/provision.yml --tags "docker_install"
ansible-playbook playbooks/provision.yml --skip-tags "common"
ansible-playbook playbooks/provision.yml --tags "packages"
```

### Research Answers

1. **What happens if rescue block also fails?**  
	The task fails and play execution continues according to play error strategy (`any_errors_fatal`, `max_fail_percentage`, etc.). Rescue is not an infinite fallback chain.
2. **Can you have nested blocks?**  
	Yes, blocks can be nested, but deep nesting hurts readability and should be used sparingly.
3. **How do tags inherit to tasks within blocks?**  
	Tags set on a block are inherited by all tasks inside that block, including rescue/always tasks unless overridden.

---

## Task 2: Docker Compose Migration (3 pts)

### Implemented Changes

- Renamed role: `roles/app_deploy` → `roles/web_app`
- Updated role reference in `playbooks/deploy.yml`
- Added Compose template: `roles/web_app/templates/docker-compose.yml.j2`
- Added dependency metadata: `roles/web_app/meta/main.yml` with dependency on `docker`
- Rewrote `roles/web_app/tasks/main.yml`:
  - includes wipe task file
  - creates project directory
  - templates compose file
  - deploys with `community.docker.docker_compose_v2`
  - verifies app startup + health endpoint
- Updated defaults in `roles/web_app/defaults/main.yml` for compose variables

### Compose Variables

- `app_name`
- `docker_image`
- `docker_tag`
- `app_port`
- `app_internal_port`
- `compose_project_dir`
- `docker_compose_version`
- `app_env`

### Idempotency Validation

Run twice and compare recap:

```bash
ansible-playbook playbooks/deploy.yml --ask-vault-pass
ansible-playbook playbooks/deploy.yml --ask-vault-pass
```

Expected: second run mostly `ok`, minimal/no `changed`.

### Research Answers

1. **`restart: always` vs `unless-stopped`?**  
	`always` restarts even after manual stop/daemon restart; `unless-stopped` restarts automatically except when intentionally stopped by operator.
2. **Compose networks vs default bridge?**  
	Compose creates project-scoped networks with automatic DNS service discovery between services; default bridge is global/manual and less isolated per app stack.
3. **Can Vault variables be used in templates?**  
	Yes. Vault variables are transparently available in Jinja templates once decrypted during playbook execution.

---

## Task 3: Wipe Logic (1 pt)

### Implemented Changes

- Added `roles/web_app/tasks/wipe.yml`
  - compose down (`state: absent`)
  - remove compose file
  - remove project directory
  - completion debug log
- Added include at top of `roles/web_app/tasks/main.yml`
- Added default control variable in `roles/web_app/defaults/main.yml`:
  - `web_app_wipe: false`

### Safety Model (Double Gate)

- Gate 1: variable check `when: web_app_wipe | bool`
- Gate 2: tag `web_app_wipe` for wipe-only execution mode

### Test Scenarios

```bash
# 1) normal deploy (wipe skipped)
ansible-playbook playbooks/deploy.yml --ask-vault-pass

# 2) wipe only
ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true" --tags web_app_wipe --ask-vault-pass

# 3) clean reinstall (wipe -> deploy)
ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true" --ask-vault-pass

# 4a) tag only, variable false
ansible-playbook playbooks/deploy.yml --tags web_app_wipe --ask-vault-pass
```

### Research Answers

1. **Why use both variable and tag?**  
	It prevents accidental destructive runs and allows both wipe-only and wipe+redeploy workflows.
2. **Difference from `never` tag?**  
	`never` hard-disables unless explicitly targeted, but does not express runtime intent (boolean safety switch) as clearly as variable+tag.
3. **Why wipe before deploy?**  
	Ensures deterministic clean reinstall (`remove old state` → `apply new state`).
4. **When clean reinstall vs rolling update?**  
	Clean reinstall for corrupted state or major config drift; rolling update for low-disruption production updates.
5. **How to extend wipe to images/volumes?**  
	Add optional tasks for `docker_image state=absent` and `docker volume rm` guarded by separate flags/tags.

---

## Task 4: CI/CD with GitHub Actions (3 pts)

### Implemented Changes

- Added workflow: `.github/workflows/ansible-deploy.yml`
  - triggers on Python app-specific paths + shared role paths
  - lint job installs Ansible + ansible-lint + required collections
  - deploy job (push only) configures SSH, builds temporary inventory, runs playbook, verifies endpoints
- Added workflow: `.github/workflows/ansible-deploy-bonus.yml`
  - triggers on Bonus app-specific paths + shared role paths
  - deploys only bonus app and verifies `:8001` endpoints

### Required Secrets

- `ANSIBLE_VAULT_PASSWORD`
- `SSH_PRIVATE_KEY`
- `VM_HOST`
- `VM_USER`

### Verification

Workflow performs:

```bash
curl -fsS http://$VM_HOST:8000
curl -fsS http://$VM_HOST:8000/health
```

### Security / Pipeline Research Answers

1. **SSH keys in GitHub Secrets risks?**  
	Leakage risk from compromised workflow/jobs; mitigate with least privilege keys, environment protection, branch protection, and key rotation.
2. **How to do staging -> production?**  
	Separate environments/jobs, manual approval gate, environment-specific inventory/vars, promote only after staging verification.
3. **What enables rollback?**  
	Immutable image tags, previous release metadata, dedicated rollback playbook/workflow input to redeploy prior tag.
4. **Why self-hosted can be more secure?**  
	Direct private-network access, tighter firewall boundaries, no inbound SSH exposure to hosted runner fleet.

---

## Task 5: Documentation (1 pt)

This file documents architecture, implementation, commands, and research answers. Add terminal outputs and screenshots from your environment under `ansible/docs/screenshots/` and reference them here.

---

## Bonus Part 1: Multi-App Deployment (1.5 pts)

### Implemented Changes

- Added reusable app-specific variable files:
  - `ansible/vars/app_python.yml`
  - `ansible/vars/app_bonus.yml`
- Added dedicated deployment playbooks:
  - `ansible/playbooks/deploy_python.yml`
  - `ansible/playbooks/deploy_bonus.yml`
- Added combined deployment playbook:
  - `ansible/playbooks/deploy_all.yml`

### Multi-App Strategy

- Single role reused: `web_app`
- App identity controlled by variables (`app_name`, `docker_image`, `app_port`, `compose_project_dir`)
- Port split avoids conflicts:
  - Python app: `8000`
  - Bonus app: `8001`

### Bonus Test Commands

```bash
# deploy both
ansible-playbook playbooks/deploy_all.yml --ask-vault-pass

# verify both endpoints
curl http://<VM-IP>:8000
curl http://<VM-IP>:8001

# independent deployments
ansible-playbook playbooks/deploy_python.yml --ask-vault-pass
ansible-playbook playbooks/deploy_bonus.yml --ask-vault-pass

# independent wipe
ansible-playbook playbooks/deploy_python.yml -e "web_app_wipe=true" --tags web_app_wipe --ask-vault-pass
ansible-playbook playbooks/deploy_bonus.yml -e "web_app_wipe=true" --tags web_app_wipe --ask-vault-pass
```

---

## Bonus Part 2: Multi-App CI/CD (1 pt)

### Implemented Changes

- Updated Python workflow `.github/workflows/ansible-deploy.yml`:
  - path filters narrowed to Python app files and shared role files
  - deploy step now runs `ansible/playbooks/deploy_python.yml`
- Added dedicated Bonus workflow `.github/workflows/ansible-deploy-bonus.yml`:
  - independent path filters for bonus app files and shared role files
  - deploy step runs `ansible/playbooks/deploy_bonus.yml`
  - verification checks `http://$VM_HOST:8001` and `/health`

### Triggering Logic

- Python-only changes trigger `ansible-deploy.yml`
- Bonus-only changes trigger `ansible-deploy-bonus.yml`
- Shared role changes (`ansible/roles/web_app/**`) trigger both workflows

### Matrix vs Separate Workflows

- Implemented **separate workflows** for isolation and clearer ownership per app.
- Matrix strategy is possible, but separate workflows are easier to troubleshoot and protect independently.

---

## Challenges & Solutions

- **Vault file is encrypted**: new non-secret defaults were added in role defaults to avoid breaking encrypted `group_vars/all.yml`.
- **Role rename impact**: all role references were switched to `web_app` in playbooks.
- **Safe cleanup requirement**: implemented wipe as separate task file with boolean guard + dedicated tag.
- **Idempotent deployment**: switched to `docker_compose_v2` and declarative compose template.

---

## Execution Evidence (Local Dry-Run)

### No-VM Mode (Implemented)

To run evidence collection without any remote VM:

```bash
cd ansible
make lab06-no-vm
```

This uses `inventory/hosts.local.ini` and collects syntax/tag/task evidence only.

Generated outputs are stored in:

- `ansible/docs/logs/lab06-no-vm/`

Key files:

- `01-provision-list-tags.txt`
- `05-deploy-list-tasks.txt`
- `08-deploy-all-list-tasks.txt`
- `09-provision-syntax.txt`
- `13-deploy-all-syntax.txt`

### Example Output: Tag Discovery

From `01-provision-list-tags.txt`:

```text
playbook: playbooks/provision.yml

  play #1 (webservers): Provision web servers	TAGS: []
      TASK TAGS: [common, docker, docker_config, docker_install, packages, users]
```

### Example Output: Deploy Task Plan (No-VM)

From `05-deploy-list-tasks.txt`:

```text
playbook: playbooks/deploy.yml

  play #1 (webservers): Deploy application	TAGS: []
    tasks:
      docker : Install apt dependencies for Docker repo	TAGS: [app_deploy, docker_install]
      docker : Create apt keyrings directory	TAGS: [app_deploy, docker_install]
      docker : Add Docker GPG key	TAGS: [app_deploy, docker_install]
      docker : Add Docker apt repository	TAGS: [app_deploy, docker_install]
      docker : Install Docker packages	TAGS: [app_deploy, docker_install]
      docker : Add users to docker group	TAGS: [app_deploy, docker_config]
      docker : Install python3-docker package	TAGS: [app_deploy, docker_config]
      web_app : Include wipe tasks	TAGS: [app_deploy, web_app_wipe]
      web_app : Validate required image variables	TAGS: [app_deploy, compose]
      web_app : Create compose project directory	TAGS: [app_deploy, compose]
      web_app : Render docker-compose.yml	TAGS: [app_deploy, compose]
      web_app : Pull and start services via Docker Compose v2	TAGS: [app_deploy, compose]
      web_app : Wait for application port	TAGS: [app_deploy, compose]
      web_app : Verify health endpoint	TAGS: [app_deploy, compose]
      web_app : Show health endpoint response summary	TAGS: [app_deploy, compose]
```

### Note

No-VM evidence validates structure, tags, task wiring, and syntax. For runtime proof (idempotency, successful wipe behavior against running containers, and endpoint accessibility), run the same scenarios against a real VM and attach screenshots/logs.

---

## Testing Results Checklist

- [ ] Selective tags execution output captured
- [ ] Rescue path output captured
- [ ] Docker Compose deployment success output captured
- [ ] Idempotency second-run proof captured
- [ ] Wipe scenarios 1/2/3/4a captured
- [ ] GitHub Actions lint + deploy logs captured
- [ ] Accessibility checks (`/` and `/health`) captured
- [ ] Multi-app deploy (`deploy_all.yml`) evidence captured
- [ ] Independent wipe per app evidence captured
- [ ] Separate workflow trigger evidence captured

---

## Summary

Lab 6 core implementation is complete in code: advanced role structure, compose migration, wipe safety, and CI/CD workflow are in place. Final grading evidence requires executing the provided commands in your target environment and attaching resulting outputs/screenshots.

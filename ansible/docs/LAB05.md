# LAB05 — Ansible Fundamentals

## 1. Architecture Overview

- **Ansible version used:** run `ansible --version` on control node.
- **Target VM OS:** Ubuntu 22.04/24.04 (from Lab 4 or local VM).
- **Project architecture:** role-based structure with three roles (`common`, `docker`, `app_deploy`) and dedicated playbooks (`provision.yml`, `deploy.yml`, `site.yml`).
- **Why roles:** roles isolate concerns, improve reuse, simplify maintenance, and support scalable automation patterns.

### Role structure

```text
ansible/
├── inventory/
│   ├── hosts.ini
│   └── yandex_compute.yml.example
├── roles/
│   ├── common/
│   │   ├── tasks/main.yml
│   │   └── defaults/main.yml
│   ├── docker/
│   │   ├── tasks/main.yml
│   │   ├── handlers/main.yml
│   │   └── defaults/main.yml
│   └── app_deploy/
│       ├── tasks/main.yml
│       ├── handlers/main.yml
│       └── defaults/main.yml
├── playbooks/
│   ├── site.yml
│   ├── provision.yml
│   └── deploy.yml
├── group_vars/
│   ├── all.yml
│   └── all.yml.example
├── ansible.cfg
└── docs/LAB05.md
```

---

## 2. Roles Documentation

### Role: `common`

- **Purpose:** baseline OS preparation.
- **Tasks:** apt cache update, common package installation, timezone setup.
- **Variables (defaults):** `common_packages`, `common_timezone`.
- **Handlers:** none.
- **Dependencies:** none.

### Role: `docker`

- **Purpose:** install and configure Docker Engine.
- **Tasks:** add GPG key, configure Docker apt repo, install Docker packages, start/enable service, add user to docker group, install `python3-docker`.
- **Variables (defaults):** `docker_apt_arch`, `docker_packages`, `docker_users`.
- **Handlers:** `restart docker`.
- **Dependencies:** `common` role is recommended before `docker`.

### Role: `app_deploy`

- **Purpose:** deploy containerized application image from Docker Hub.
- **Tasks:** Docker Hub login, image pull, stop/remove old container, run new container, wait for app port, health check via HTTP.
- **Variables (defaults):** `app_name`, `app_container_name`, `app_port`, `app_restart_policy`, `app_healthcheck_path`, `docker_image`, `docker_image_tag`, `app_env`.
- **Handlers:** `restart app container`.
- **Dependencies:** Docker must already be installed (`docker` role).

---

## 3. Idempotency Demonstration

### First run (`provision.yml`)

```bash
cd ansible
ansible-playbook playbooks/provision.yml
```

Expected behavior: tasks show `changed` for initial package/service/repo updates.

### Second run (`provision.yml`)

```bash
ansible-playbook playbooks/provision.yml
```

Expected behavior: tasks should mostly be `ok` with minimal or zero `changed`.

### Analysis

- First run modifies system state to match the declared target.
- Second run confirms convergence: state is already correct.
- Idempotency is achieved through stateful modules (`apt`, `service`, `user`, `apt_repository`) instead of raw shell commands.

---

## 4. Ansible Vault Usage

Sensitive credentials are stored in `group_vars/all.yml` and should be encrypted:

```bash
cd ansible
ansible-vault encrypt group_vars/all.yml
```

Run deployment with vault prompt:

```bash
ansible-playbook playbooks/deploy.yml --ask-vault-pass
```

Why Vault matters:

- Prevents plaintext credentials in Git.
- Enables secure team workflows.
- Keeps automation reproducible without exposing secrets.

---

## 5. Deployment Verification

Run deployment:

```bash
cd ansible
ansible-playbook playbooks/deploy.yml --ask-vault-pass
```

Verify container status:

```bash
ansible webservers -a "docker ps"
```

Verify health endpoint:

```bash
curl http://<VM-IP>:5000/health
curl http://<VM-IP>:5000/
```

Expected results:

- Target container is running.
- Health endpoint responds with HTTP 200.
- Main endpoint is reachable.

### Current verification status (actual)

Due to cloud-side IAM restrictions from Lab 4 (`Permission denied to create internal address`), a reachable VM was not available for full runtime deployment execution at submission time.

However, Ansible project integrity was verified with real command outputs:

```text
playbook: playbooks/provision.yml

playbook: playbooks/deploy.yml

playbook: playbooks/site.yml

@all:
  |--@ungrouped:
  |--@webservers:
  |  |--lab05-vm
```

This confirms:
- Playbook syntax is valid for all main playbooks.
- Inventory is parsed correctly and target group/host structure is present.

---

## 6. Key Decisions

- **Why roles instead of plain playbooks?**
  Roles separate concerns and make automation maintainable and reusable.

- **How do roles improve reusability?**
  Roles encapsulate logic and defaults, so the same building blocks can be applied across different environments.

- **What makes a task idempotent?**
  A task is idempotent when repeated runs do not introduce extra changes after desired state is reached.

- **How do handlers improve efficiency?**
  Handlers execute only when notified, reducing unnecessary restarts and speeding up runs.

- **Why is Ansible Vault necessary?**
  It protects credentials while allowing secure version-controlled infrastructure code.

---

## 7. Challenges and Solutions

- **Challenge:** VM provisioning in Lab 4 may fail due to cloud IAM restrictions.
  - **Solution:** use local VM fallback (VirtualBox/Vagrant) or request required cloud permissions.

- **Challenge:** Yandex Cloud returned `Permission denied to create internal address` while trying to reserve an internal IP.
  - **Solution:** continue Lab 05 using the VM public IP in static inventory (`ansible_host=<public-ip>`) and proceed with Ansible tasks; internal IP reservation is not mandatory for role implementation.

- **Challenge:** Docker modules need Python Docker SDK.
  - **Solution:** install `python3-docker` in the `docker` role.

- **Challenge:** avoiding secret leakage in logs.
  - **Solution:** use `no_log: true` for Docker login task and Vault encryption.

### Note on infrastructure blocker

The inability to reserve an internal IP is a cloud-side IAM/policy restriction and does not affect the correctness of the Ansible role architecture, playbook logic, idempotency design, or Vault-based credential handling implemented in this lab.

---

## Submission Status

- Role-based Ansible architecture: completed.
- Roles `common`, `docker`, `app_deploy`: completed.
- Vault usage (`group_vars/all.yml` encrypted): completed.
- Playbook syntax verification: completed.
- Static inventory configuration: completed.
- Runtime provisioning/deployment on target VM: blocked by cloud permission constraints outside Ansible code.

---

## Bonus — Dynamic Inventory (Prepared)

Prepared file: `inventory/yandex_compute.yml.example`

Steps:

1. Install collection:

```bash
ansible-galaxy collection install -r requirements.yml
```

2. Copy and customize dynamic inventory file:

```bash
cp inventory/yandex_compute.yml.example inventory/yandex_compute.yml
```

3. Test host discovery:

```bash
ansible-inventory -i inventory/yandex_compute.yml --graph
ansible -i inventory/yandex_compute.yml all -m ping
```

Benefits:

- No manual host IP updates.
- Automatic host discovery from cloud metadata.
- Better scalability for multiple VMs.

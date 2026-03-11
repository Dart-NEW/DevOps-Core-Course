# Ansible Lab 06

[![Ansible Deployment](https://github.com/Dart-NEW/DevOps-Core-Course/actions/workflows/ansible-deploy.yml/badge.svg)](https://github.com/Dart-NEW/DevOps-Core-Course/actions/workflows/ansible-deploy.yml)
[![Ansible Bonus Deployment](https://github.com/Dart-NEW/DevOps-Core-Course/actions/workflows/ansible-deploy-bonus.yml/badge.svg)](https://github.com/Dart-NEW/DevOps-Core-Course/actions/workflows/ansible-deploy-bonus.yml)

## Quick start

```bash
cd ansible
ansible-galaxy collection install -r requirements.yml

# run Lab 6 checks/evidence without a VM
make lab06-no-vm
```

### 1) Configure inventory

Edit `inventory/hosts.ini` with your VM IP/user.

### 2) Configure secrets (Vault)

```bash
cp group_vars/all.yml.example group_vars/all.yml
# edit values
ansible-vault encrypt group_vars/all.yml
```

### 3) Check connectivity

```bash
ansible all -m ping
ansible webservers -a "uname -a"
```

### 4) Provision system

```bash
ansible-playbook playbooks/provision.yml
ansible-playbook playbooks/provision.yml

# selective runs
ansible-playbook playbooks/provision.yml --list-tags
ansible-playbook playbooks/provision.yml --tags "docker"
ansible-playbook playbooks/provision.yml --tags "docker_install"
ansible-playbook playbooks/provision.yml --skip-tags "common"
```

### 5) Deploy app

```bash
ansible-playbook playbooks/deploy.yml --ask-vault-pass

# wipe only
ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true" --tags web_app_wipe --ask-vault-pass

# clean reinstall (wipe -> deploy)
ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true" --ask-vault-pass
```

### 6) Verify

```bash
ansible webservers -a "docker ps"
docker compose -f /opt/devops-app/docker-compose.yml ps
curl http://<VM-IP>:8000/health
```

### 7) Bonus multi-app deployment

```bash
# deploy each app independently
ansible-playbook playbooks/deploy_python.yml --ask-vault-pass
ansible-playbook playbooks/deploy_bonus.yml --ask-vault-pass

# deploy both apps
ansible-playbook playbooks/deploy_all.yml --ask-vault-pass

# wipe only python app
ansible-playbook playbooks/deploy_python.yml -e "web_app_wipe=true" --tags web_app_wipe --ask-vault-pass

# wipe only bonus app
ansible-playbook playbooks/deploy_bonus.yml -e "web_app_wipe=true" --tags web_app_wipe --ask-vault-pass
```

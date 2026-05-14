# Ansible Lab 05

## Quick start

```bash
cd ansible
ansible-galaxy collection install -r requirements.yml
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
```

### 5) Deploy app

```bash
ansible-playbook playbooks/deploy.yml --ask-vault-pass
```

### 6) Verify

```bash
ansible webservers -a "docker ps"
curl http://<VM-IP>:5000/health
```

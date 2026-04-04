.PHONY: lab06-no-vm

LAB06_LOG_DIR := docs/logs/lab06-no-vm
LOCAL_INV := inventory/hosts.local.ini

lab06-no-vm:
	@mkdir -p $(LAB06_LOG_DIR)
	@echo "[lab06-no-vm] collecting syntax/tag/task evidence without VM"
	@ansible-playbook playbooks/provision.yml -i $(LOCAL_INV) --list-tags > $(LAB06_LOG_DIR)/01-provision-list-tags.txt 2>&1
	@ansible-playbook playbooks/deploy.yml -i $(LOCAL_INV) --list-tags > $(LAB06_LOG_DIR)/02-deploy-list-tags.txt 2>&1
	@ansible-playbook playbooks/deploy_all.yml -i $(LOCAL_INV) --list-tags > $(LAB06_LOG_DIR)/03-deploy-all-list-tags.txt 2>&1
	@ansible-playbook playbooks/provision.yml -i $(LOCAL_INV) --list-tasks > $(LAB06_LOG_DIR)/04-provision-list-tasks.txt 2>&1
	@ansible-playbook playbooks/deploy.yml -i $(LOCAL_INV) --list-tasks > $(LAB06_LOG_DIR)/05-deploy-list-tasks.txt 2>&1
	@ansible-playbook playbooks/deploy_python.yml -i $(LOCAL_INV) --list-tasks > $(LAB06_LOG_DIR)/06-deploy-python-list-tasks.txt 2>&1
	@ansible-playbook playbooks/deploy_bonus.yml -i $(LOCAL_INV) --list-tasks > $(LAB06_LOG_DIR)/07-deploy-bonus-list-tasks.txt 2>&1
	@ansible-playbook playbooks/deploy_all.yml -i $(LOCAL_INV) --list-tasks > $(LAB06_LOG_DIR)/08-deploy-all-list-tasks.txt 2>&1
	@ansible-playbook playbooks/provision.yml --syntax-check > $(LAB06_LOG_DIR)/09-provision-syntax.txt 2>&1
	@ansible-playbook playbooks/deploy.yml --syntax-check > $(LAB06_LOG_DIR)/10-deploy-syntax.txt 2>&1
	@ansible-playbook playbooks/deploy_python.yml --syntax-check > $(LAB06_LOG_DIR)/11-deploy-python-syntax.txt 2>&1
	@ansible-playbook playbooks/deploy_bonus.yml --syntax-check > $(LAB06_LOG_DIR)/12-deploy-bonus-syntax.txt 2>&1
	@ansible-playbook playbooks/deploy_all.yml --syntax-check > $(LAB06_LOG_DIR)/13-deploy-all-syntax.txt 2>&1
	@echo "[lab06-no-vm] done -> $(LAB06_LOG_DIR)"
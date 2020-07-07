#!/usr/bin/env bash
set -eux

# Envs
export ANSIBLE_PYTHON_INTERPRETER=${ANSIBLE_TEST_PYTHON_INTERPRETER:-$(which python)}
export ANSIBLE_INVENTORY_ENABLED="community.vmware.vmware_vm_inventory,host_list,ini"
export ANSIBLE_CACHE_PLUGIN_CONNECTION="${PWD}/inventory_cache"
export ANSIBLE_CACHE_PLUGIN="community.general.jsonfile"

set -euo pipefail

# Required to differentiate between Python 2 and 3 environ
export ANSIBLE_PYTHON_INTERPRETER=${ANSIBLE_TEST_PYTHON_INTERPRETER:-$(which python)}

export ANSIBLE_INVENTORY_ENABLED="community.vmware.vmware_vm_inventory,host_list,ini"

# Cache setting
export ANSIBLE_CACHE_PLUGIN_CONNECTION="inventory_cache"
export ANSIBLE_CACHE_PLUGIN="community.general.jsonfile"

# prepare_vmware_test envs!
export VMWARE_HOST="${VCENTER_HOSTNAME}"
export VMWARE_USER="${VCENTER_USERNAME}"
export VMWARE_PASSWORD="${VCENTER_PASSWORD}"
export VMWARE_VALIDATE_CERTS="no" # Note: Should be set by ansible-test

INVENTORY_DIR="${PWD}/_test/hosts"
mkdir -p "${INVENTORY_DIR}" 2>/dev/null
touch "${INVENTORY_DIR}/empty.yml"

cleanup() {
    ec=$?
    echo "Cleanup"
    if [ -d "${ANSIBLE_CACHE_PLUGIN_CONNECTION}" ]; then
        echo "Removing ${ANSIBLE_CACHE_PLUGIN_CONNECTION}"
        rm -rf "${ANSIBLE_CACHE_PLUGIN_CONNECTION}"
    fi
    
    if [ -d "${INVENTORY_DIR}" ]; then
        echo "Removing ${INVENTORY_DIR}"
        rm -rf "${INVENTORY_DIR}"
    fi

    echo "Done"
    exit $ec
}
trap cleanup INT TERM EXIT

set_inventory(){
    export ANSIBLE_INVENTORY="${1}"
    echo "INVENTORY '${1}' is active" 
}


# Install dependencies
ansible-playbook -i 'localhost,' playbook/install_dependencies.yml "$@"

# Prepare tests
ansible-playbook -i 'localhost,' playbook/prepare_vmware.yml "$@"


set_inventory "inventory/defaults_with_cache.vmware.yml"
# Get inventory
ansible-inventory --list 1>/dev/null

# Check if cache is working for inventory plugin
ansible-playbook playbook/test_inventory_cache.yml "$@"

# Get inventory using YAML
ansible-inventory --list --yaml 1>/dev/null

# Get inventory using TOML
ansible-inventory --list --toml 1>/dev/null


set_inventory "inventory/defaults.vmware.yml"
# # Test playbook with given inventory
ansible-playbook playbook/test_vmware_vm_inventory.yml "$@"


# Test options
set_inventory "${INVENTORY_DIR}"
ansible-playbook playbook/test_options.yml "$@"
#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2015, Joseph Callen <jcallen () csc.com>
# Copyright: (c) 2018, Ansible Project
# Copyright: (c) 2018, Fedor Vompe <f.vompe () comptek.ru>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: vmware_vm_info
short_description: Return basic info pertaining to a VMware machine guest
description:
- Return basic information pertaining to a vSphere or ESXi virtual machine guest.
author:
- Joseph Callen (@jcpowermac)
- Abhijeet Kasurde (@Akasurde)
- Fedor Vompe (@sumkincpp)
options:
    vm_type:
      description:
      - If set to V(vm), then information are gathered for virtual machines only.
      - If set to V(template), then information are gathered for virtual machine templates only.
      - If set to V(all), then information are gathered for all virtual machines and virtual machine templates.
      required: false
      default: 'all'
      choices: [ all, vm, template ]
      type: str
    show_attribute:
      description:
      - Attributes related to VM guest shown in information only when this is set V(true).
      default: false
      type: bool
    folder:
      description:
      - Specify a folder location of VMs to gather information from.
      - Can't be used if O(cluster) is set.
      - 'Examples:'
      - '   folder: /ha-datacenter/vm'
      - '   folder: ha-datacenter/vm'
      - '   folder: /datacenter1/vm'
      - '   folder: datacenter1/vm'
      - '   folder: /datacenter1/vm/folder1'
      - '   folder: datacenter1/vm/folder1'
      - '   folder: /folder1/datacenter1/vm'
      - '   folder: folder1/datacenter1/vm'
      - '   folder: /folder1/datacenter1/vm/folder2'
      type: str
    vm_names:
      description:
      - List of the names of the virtual machines to get related configurations information from.
      - Can´t be used if O(regex) is set.
      type: list
      elements: str
    vm_name:
      description:
      - Name of the virtual machine to get related configurations information from.
      - Or if O(regex) is True, it will be used as an Filter for the Names of the virtual machines.
      - Can´t be used if O(cluster) or O(vm_names) is set.
      type: str
    show_cluster:
      description:
        - Tags virtual machine's cluster is shown if set to V(true).
      version_added: '3.5.0'
      default: true
      type: bool
    show_datacenter:
      description:
        - Tags virtual machine's datacenter is shown if set to V(true).
      version_added: '3.5.0'
      default: true
      type: bool
    show_datastore:
      description:
        - Tags virtual machine's datastore is shown if set to V(true).
      version_added: '3.5.0'
      default: true
      type: bool
    show_esxi_hostname:
      description:
        - Tags virtual machine's ESXi host is shown if set to V(true).
      version_added: '3.5.0'
      default: true
      type: bool
    show_folder:
      description:
        - Show folders
      version_added: '3.7.0'
      default: true
      type: bool
    show_mac_address:
      description:
        - Tags virtual machine's mac address is shown if set to V(true).
      version_added: '3.5.0'
      default: true
      type: bool
    show_net:
      description:
        - Tags virtual machine's network is shown if set to V(true).
      version_added: '3.5.0'
      default: true
      type: bool
    show_resource_pool:
      description:
        - Tags virtual machine's resource pool is shown if set to V(true).
      version_added: '3.5.0'
      default: true
      type: bool
    show_tag:
      description:
        - Tags related to virtual machine are shown if set to V(true).
      default: false
      type: bool
    show_notes:
      description:
        -Tags virtual machine's notes is shown if set to V(true).
      default: false
      type: bool
    show_allocated:
      description:
        - Allocated storage in byte and memory in MB are shown if it set to True.
      default: false
      type: bool
    regex:
      description:
        - If O(vm_name) is used as an Regex Filter.
        - For Metacharacters use in the O(vm_name) show Python RegEx
      type: bool
      default: false
    cluster:
      description:
      - Name of the cluster to gather information from VMs of this cluster.
      type: str
      aliases: [ cluster_name ]
extends_documentation_fragment:
- community.vmware.vmware.documentation
'''

EXAMPLES = r'''
- name: Gather all registered virtual machines
  community.vmware.vmware_vm_info:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
  delegate_to: localhost
  register: vm_info

- debug:
    var: vm_info.virtual_machines

- name: Gather all registered virtual machines of this cluster
  community.vmware.vmware_vm_info:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    cluster: DC0_C0
  delegate_to: localhost
  register: vminfo

- debug:
    var: vminfo.virtual_machines

- name: Gather one specific VM
  community.vmware.vmware_vm_info:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    vm_name: 'vm_name_as_per_vcenter'
  delegate_to: localhost
  register: vm_info

- debug:
    var: vm_info.virtual_machines

- name: Gather only registered virtual machine templates
  community.vmware.vmware_vm_info:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    vm_type: template
  delegate_to: localhost
  register: template_info

- debug:
    var: template_info.virtual_machines

- name: Gather only registered virtual machines
  community.vmware.vmware_vm_info:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    vm_type: vm
  delegate_to: localhost
  register: vm_info

- debug:
    var: vm_info.virtual_machines

- name: Get UUID from given VM Name
  block:
    - name: Get virtual machine info
      community.vmware.vmware_vm_info:
        hostname: '{{ vcenter_hostname }}'
        username: '{{ vcenter_username }}'
        password: '{{ vcenter_password }}'
        folder: "/datacenter/vm/folder"
      delegate_to: localhost
      register: vm_info

    - debug:
        msg: "{{ item.uuid }}"
      with_items:
        - "{{ vm_info.virtual_machines | community.general.json_query(query) }}"
      vars:
        query: "[?guest_name=='DC0_H0_VM0']"

- name: Get Tags from given VM Name
  block:
    - name: Get virtual machine info
      community.vmware.vmware_vm_info:
        hostname: '{{ vcenter_hostname }}'
        username: '{{ vcenter_username }}'
        password: '{{ vcenter_password }}'
        folder: "/datacenter/vm/folder"
      delegate_to: localhost
      register: vm_info

    - debug:
        msg: "{{ item.tags }}"
      with_items:
        - "{{ vm_info.virtual_machines | community.general.json_query(query) }}"
      vars:
        query: "[?guest_name=='DC0_H0_VM0']"

- name: Gather all VMs from a specific folder
  community.vmware.vmware_vm_info:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    folder: "/Asia-Datacenter1/vm/prod"
  delegate_to: localhost
  register: vm_info

- name: Get datastore_url from given VM name
  block:
    - name: Get virtual machine info
      community.vmware.vmware_vm_info:
        hostname: '{{ vcenter_hostname }}'
        username: '{{ vcenter_username }}'
        password: '{{ vcenter_password }}'
      delegate_to: localhost
      register: vm_info

    - debug:
        msg: "{{ item.datastore_url }}"
      with_items:
        - "{{ vm_info.virtual_machines | community.general.json_query(query) }}"
      vars:
        query: "[?guest_name=='DC0_H0_VM0']"
'''

RETURN = r'''
virtual_machines:
  description: list of dictionary of virtual machines and their information
  returned: success
  type: list
  sample: [
    {
        "guest_name": "ubuntu_t",
        "datacenter": "Datacenter-1",
        "cluster": null,
        "esxi_hostname": "10.76.33.226",
        "folder": "/Datacenter-1/vm",
        "guest_fullname": "Ubuntu Linux (64-bit)",
        "running_guest_fullname": "Ubuntu Linux (64-bit)",
        "running_guest_id": "ubuntu64Guest",
        "ip_address": "",
        "mac_address": [
            "00:50:56:87:a5:9a"
        ],
        "power_state": "poweredOff",
        "uuid": "4207072c-edd8-3bd5-64dc-903fd3a0db04",
        "vm_network": {
            "00:50:56:87:a5:9a": {
              "ipv4": [
                "10.76.33.228/24"
              ],
              "ipv6": []
            }
        },
        "attributes": {
            "job": "backup-prepare"
        },
        "datastore_url": [
            {
                "name": "t880-o2g",
                "url": "/vmfs/volumes/e074264a-e5c82a58"
            }
        ],
        "tags": [
            {
                "category_id": "urn:vmomi:InventoryServiceCategory:b316cc45-f1a9-4277-811d-56c7e7975203:GLOBAL",
                "category_name": "cat_0001",
                "description": "",
                "id": "urn:vmomi:InventoryServiceTag:43737ec0-b832-4abf-abb1-fd2448ce3b26:GLOBAL",
                "name": "tag_0001"
            }
        ],
        "moid": "vm-24",
        "allocated": {
            "storage": 500000000,
            "cpu": 2,
            "memory": 16
        },
    }
  ]
'''

try:
    from pyVmomi import vim, vmodl
    import re
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.community.vmware.plugins.module_utils.vmware import PyVmomi, \
    get_all_objs, vmware_argument_spec, _get_vm_prop, get_parent_datacenter, find_vm_by_name, find_cluster_by_name
from ansible_collections.community.vmware.plugins.module_utils.vmware_rest_client import VmwareRestClient
import re


class VmwareVmInfo(PyVmomi):
    def __init__(self, module):
        super(VmwareVmInfo, self).__init__(module)
        if self.module.params.get('show_tag'):
            self.vmware_client = VmwareRestClient(self.module)

    def get_tag_info(self, vm_dynamic_obj):
        return self.vmware_client.get_tags_for_vm(vm_mid=vm_dynamic_obj._moId)

    def get_vm_attributes(self, vm):
        custom_field_values = vm.customValue
        custom_field_mgr = self.custom_field_mgr
        vm_attributes = {}
        for custom_field in custom_field_mgr:
            for custom_value in custom_field_values:
                if custom_field.key == custom_value.key:
                    vm_attributes[custom_field.name] = custom_value.value
        return vm_attributes

    # https://github.com/vmware/pyvmomi-community-samples/blob/master/samples/getallvms.py
    def get_virtual_machines(self):
        """
        Get one/all virtual machines and related configurations information.
        """
        folder = self.params.get('folder')
        folder_obj = None
        if folder:
            folder_obj = self.content.searchIndex.FindByInventoryPath(folder)
            if not folder_obj:
                self.module.fail_json(msg="Failed to find folder specified by %(folder)s" % self.params)

        vm_name = self.params.get('vm_name')
        if vm_name and not self.params.get('regex'):
            virtual_machine = find_vm_by_name(self.content, vm_name=vm_name, folder=folder_obj)
            if not virtual_machine:
                self.module.fail_json(msg="Failed to find virtual machine %s" % vm_name)
            else:
                virtual_machines = [virtual_machine]
        else:
            cluster = self.params.get('cluster')
            vm_names = self.params.get('vm_names')
            if cluster:
                cluster_obj = find_cluster_by_name(self.content, cluster_name=cluster)
                if cluster_obj is None:
                    self.module.fail_json(msg="Failed to find cluster '%s'" % cluster)

                virtual_machines = []
                for host in cluster_obj.host:
                    virtual_machines.extend(host.vm)
            else:
                virtual_machines = get_all_objs(self.content, [vim.VirtualMachine], folder=folder_obj)
        _virtual_machines = []

        for vm in virtual_machines:
            try:
                if self.params.get('vm_names') and vm.name not in vm_names:
                    continue
                if self.params.get('regex') and not re.search(vm_name, vm.name):
                    continue

                _ip_address = ""
                summary = vm.summary
                if summary.guest is not None:
                    _ip_address = summary.guest.ipAddress
                    if _ip_address is None:
                        _ip_address = ""
                _mac_address = []
                if self.module.params.get('show_mac_address'):
                    all_devices = _get_vm_prop(vm, ('config', 'hardware', 'device'))
                    if all_devices:
                        for dev in all_devices:
                            if isinstance(dev, vim.vm.device.VirtualEthernetCard):
                                _mac_address.append(dev.macAddress)

                net_dict = {}
                if self.module.params.get('show_net'):
                    vmnet = _get_vm_prop(vm, ('guest', 'net'))
                    if vmnet:
                        for device in vmnet:
                            net_dict[device.macAddress] = dict()
                            net_dict[device.macAddress]['ipv4'] = []
                            net_dict[device.macAddress]['ipv6'] = []
                            if device.ipConfig is not None:
                                for ip_addr in device.ipConfig.ipAddress:
                                    if "::" in ip_addr.ipAddress:
                                        net_dict[device.macAddress]['ipv6'].append(ip_addr.ipAddress + "/" + str(ip_addr.prefixLength))
                                    else:
                                        net_dict[device.macAddress]['ipv4'].append(ip_addr.ipAddress + "/" + str(ip_addr.prefixLength))

                esxi_hostname = None
                esxi_parent = None
                note = None

                if self.module.params.get('show_esxi_hostname') or self.module.params.get('show_cluster'):
                    if summary.runtime.host:
                        esxi_hostname = summary.runtime.host.summary.config.name
                        esxi_parent = summary.runtime.host.parent

                cluster_name = None
                if self.module.params.get('show_cluster'):
                    if esxi_parent and isinstance(esxi_parent, vim.ClusterComputeResource):
                        cluster_name = summary.runtime.host.parent.name

                resource_pool = None
                if self.module.params.get('show_resource_pool'):
                    if vm.resourcePool and vm.resourcePool != vm.resourcePool.owner.resourcePool:
                        resource_pool = vm.resourcePool.name

                vm_attributes = dict()
                if self.module.params.get('show_attribute'):
                    vm_attributes = self.get_vm_attributes(vm)

                vm_tags = list()
                if self.module.params.get('show_tag'):
                    vm_tags = self.get_tag_info(vm)

                if self.module.params.get('show_notes'):
                    note = vm.summary.config.annotation

                allocated = {}
                if self.module.params.get('show_allocated'):
                    storage_allocated = 0
                    for device in vm.config.hardware.device:
                        if isinstance(device, vim.vm.device.VirtualDisk):
                            storage_allocated += device.capacityInBytes
                    allocated = {
                        "storage": storage_allocated,
                        "cpu": vm.config.hardware.numCPU,
                        "memory": vm.config.hardware.memoryMB}

                vm_folder = None
                if self.module.params.get('show_folder'):
                    vm_folder = PyVmomi.get_vm_path(content=self.content, vm_name=vm)

                datacenter = None
                if self.module.params.get('show_datacenter'):
                    datacenter = get_parent_datacenter(vm)
                datastore_url = list()
                if self.module.params.get('show_datastore'):
                    datastore_attributes = ('name', 'url')
                    vm_datastore_urls = _get_vm_prop(vm, ('config', 'datastoreUrl'))
                    if vm_datastore_urls:
                        for entry in vm_datastore_urls:
                            datastore_url.append({key: getattr(entry, key) for key in dir(entry) if key in datastore_attributes})
                virtual_machine = {
                    "guest_name": summary.config.name,
                    "guest_fullname": summary.config.guestFullName,
                    "running_guest_fullname": summary.guest.guestFullName,
                    "running_guest_id": summary.guest.guestId,
                    "power_state": summary.runtime.powerState,
                    "ip_address": _ip_address,  # Kept for backward compatibility
                    "mac_address": _mac_address,  # Kept for backward compatibility
                    "uuid": summary.config.uuid,
                    "instance_uuid": summary.config.instanceUuid,
                    "vm_network": net_dict,
                    "esxi_hostname": esxi_hostname,
                    "datacenter": None if datacenter is None else datacenter.name,
                    "cluster": cluster_name,
                    "resource_pool": resource_pool,
                    "attributes": vm_attributes,
                    "tags": vm_tags,
                    "note": note,
                    "folder": vm_folder,
                    "moid": vm._moId,
                    "datastore_url": datastore_url,
                    "allocated": allocated
                }

                vm_type = self.module.params.get('vm_type')
                is_template = _get_vm_prop(vm, ('config', 'template'))
                if vm_type == 'vm' and not is_template:
                    _virtual_machines.append(virtual_machine)
                elif vm_type == 'template' and is_template:
                    _virtual_machines.append(virtual_machine)
                elif vm_type == 'all':
                    _virtual_machines.append(virtual_machine)
            except vmodl.fault.ManagedObjectNotFound:
                continue

        if _virtual_machines is None:
            self.module.fail_json(msg="No virtual machines found.")
        return _virtual_machines


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        vm_type=dict(type='str', choices=['vm', 'all', 'template'], default='all'),
        show_attribute=dict(type='bool', default='no'),
        show_cluster=dict(type='bool', default=True),
        show_datacenter=dict(type='bool', default=True),
        show_datastore=dict(type='bool', default=True),
        show_folder=dict(type='bool', default=True),
        show_esxi_hostname=dict(type='bool', default=True),
        show_mac_address=dict(type='bool', default=True),
        show_net=dict(type='bool', default=True),
        show_resource_pool=dict(type='bool', default=True),
        show_tag=dict(type='bool', default=False),
        show_notes=dict(type='bool', default=False),
        show_allocated=dict(type='bool', default=False),
        folder=dict(type='str'),
        cluster=dict(type='str', aliases=['cluster_name']),
        vm_name=dict(type='str'),
        vm_names=dict(type='list', elements='str'),
        regex=dict(type='bool', default=False)
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[
            ['cluster', 'folder'], ['vm_name', 'vm_names', 'cluster'], ['vm_names', 'regex']
        ]
    )

    vmware_vm_info = VmwareVmInfo(module)
    _virtual_machines = vmware_vm_info.get_virtual_machines()

    module.exit_json(changed=False, virtual_machines=_virtual_machines)


if __name__ == '__main__':
    main()

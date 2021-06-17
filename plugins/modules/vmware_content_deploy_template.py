#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2019, Ansible Project
# Copyright: (c) 2019, Pavan Bidkar <pbidkar@vmware.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: vmware_content_deploy_template
short_description: Deploy Virtual Machine from template stored in content library.
description:
- Module to deploy virtual machine from template in content library.
- Content Library feature is introduced in vSphere 6.0 version.
- vmtx templates feature is introduced in vSphere 67U1 and APIs for clone template from content library in 67U2.
- This module does not work with vSphere version older than 67U2.
- All variables and VMware object names are case sensitive.
author:
- Pavan Bidkar (@pgbidkar)
notes:
- Tested on vSphere 6.7 U3
requirements:
- python >= 2.6
- PyVmomi
- vSphere Automation SDK
options:
    template:
      description:
      - The name of template from which VM to be deployed.
      type: str
      required: True
      aliases: ['template_src']
    content_library:
      description:
      - The name of the content library from where the template resides.
      type: str
      required: False
      aliases: ['content_library_src']
    name:
      description:
      - The name of the VM to be deployed.
      type: str
      required: True
      aliases: ['vm_name']
    datacenter:
      description:
      - Name of the datacenter, where VM to be deployed.
      type: str
      required: True
    datastore:
      description:
      - Name of the datastore to store deployed VM and disk.
      - Required if I(datastore_cluster) is not provided.
      type: str
      required: False
    datastore_cluster:
       description:
       - Name of the datastore cluster to store deployed VM and disk.
       - Please make sure Storage DRS is active for recommended datastore from the given datastore cluster.
       - If Storage DRS is not enabled, datastore with largest free storage space is selected.
       - Required if I(datastore) is not provided.
       type: str
       required: False
       version_added: '1.7.0'
    folder:
      description:
      - Name of the folder in datacenter in which to place deployed VM.
      type: str
      required: True
    host:
      description:
      - Name of the ESX Host in datacenter in which to place deployed VM.
      - The host has to be a member of the cluster that contains the resource pool.
      - Required with I(resource_pool) to find resource pool details. This will be used as additional
        information when there are resource pools with same name.
      type: str
      required: False
    resource_pool:
      description:
      - Name of the resource pool in datacenter in which to place deployed VM.
      - Required if I(cluster) is not specified.
      - For default or non-unique resource pool names, specify I(host) and I(cluster).
      - C(Resources) is the default name of resource pool.
      type: str
      required: False
    cluster:
      description:
      - Name of the cluster in datacenter in which to place deployed VM.
      - Required if I(resource_pool) is not specified.
      type: str
      required: False
    state:
      description:
      - The state of Virtual Machine deployed from template in content library.
      - If set to C(present) and VM does not exists, then VM is created.
      - If set to C(present) and VM exists, no action is taken.
      - If set to C(poweredon) and VM does not exists, then VM is created with powered on state.
      - If set to C(poweredon) and VM exists, no action is taken.
      type: str
      required: False
      default: 'present'
      choices: [ 'present', 'poweredon' ]
extends_documentation_fragment:
- community.vmware.vmware_rest_client.documentation

'''

EXAMPLES = r'''
- name: Deploy Virtual Machine from template in content library
  community.vmware.vmware_content_deploy_template:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    template: rhel_test_template
    datastore: Shared_NFS_Volume
    folder: vm
    datacenter: Sample_DC_1
    name: Sample_VM
    resource_pool: test_rp
    state: present
  delegate_to: localhost

- name: Deploy Virtual Machine from template in content library with PowerON State
  community.vmware.vmware_content_deploy_template:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    template: rhel_test_template
    content_library: test_content_library
    datastore: Shared_NFS_Volume
    folder: vm
    datacenter: Sample_DC_1
    name: Sample_VM
    resource_pool: test_rp
    state: poweredon
  delegate_to: localhost
'''

RETURN = r'''
vm_deploy_info:
  description: Virtual machine deployment message and vm_id
  returned: on success
  type: dict
  sample: {
        "msg": "Deployed Virtual Machine 'Sample_VM'.",
        "vm_id": "vm-1009"
    }
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.community.vmware.plugins.module_utils.vmware_rest_client import VmwareRestClient
from ansible_collections.community.vmware.plugins.module_utils.vmware import PyVmomi
from ansible.module_utils._text import to_native

HAS_VAUTOMATION_PYTHON_SDK = False
try:
    from com.vmware.vcenter.vm_template_client import LibraryItems
    from com.vmware.vapi.std.errors_client import Error
    HAS_VAUTOMATION_PYTHON_SDK = True
except ImportError:
    pass


class VmwareContentDeployTemplate(VmwareRestClient):
    def __init__(self, module):
        """Constructor."""
        super(VmwareContentDeployTemplate, self).__init__(module)
        self.pyv = PyVmomi(module=module)
        vm = self.pyv.get_vm()
        if vm:
            self.module.exit_json(
                changed=False,
                vm_deploy_info=dict(
                    msg="Virtual Machine '%s' already exists." % self.module.params['name'],
                    vm_id=vm._moId,
                )
            )
        self.template_service = self.api_client.vcenter.vm_template.LibraryItems
        self.template_name = self.params.get('template')
        self.content_library_name = self.params.get('content_library')
        self.vm_name = self.params.get('name')
        self.datacenter = self.params.get('datacenter')
        self.datastore = self.params.get('datastore')
        self.datastore_cluster = self.params.get('datastore_cluster')
        self.datastore_id = None
        self.folder = self.params.get('folder')
        self.resourcepool = self.params.get('resource_pool')
        self.cluster = self.params.get('cluster')
        self.host = self.params.get('host')

    def deploy_vm_from_template(self, power_on=False):
        # Find the datacenter by the given datacenter name
        self.datacenter_id = self.get_datacenter_by_name(datacenter_name=self.datacenter)
        if not self.datacenter_id:
            self.module.fail_json(msg="Failed to find the datacenter %s" % self.datacenter)

        if self.datastore:
            # Find the datastore by the given datastore name
            self.datastore_id = self.get_datastore_by_name(self.datacenter, self.datastore)
        if self.datastore_cluster:
            # Find the datastore by the given datastore cluster name
            datastore_cluster = self.pyv.find_datastore_cluster_by_name(self.datastore_cluster, datacenter=self.datacenter_id)
            if not datastore_cluster:
                self.module.fail_json(msg="Failed to find the datastore cluster %s" % self.datastore_cluster)
            self.datastore_id = self.pyv.get_recommended_datastore(datastore_cluster)

        if not self.datastore_id:
            if self.datastore:
                self.module.fail_json(msg="Failed to find the datastore %s" % self.datastore)
            if self.datastore_cluster:
                self.module.fail_json(msg="Failed to find the datastore using datastore cluster %s" % self.datastore_cluster)

        # Find the LibraryItem (Template) by the given LibraryItem name
        if self.content_library_name:
            self.library_item_id = self.get_library_item_from_content_library_name(
                self.template_name, self.content_library_name)
            if not self.library_item_id:
                self.module.fail_json(msg="Failed to find the library Item %s in content library %s" % (self.template_name, self.content_library_name))
        else:
            self.library_item_id = self.get_library_item_by_name(self.template_name)
            if not self.library_item_id:
                self.module.fail_json(msg="Failed to find the library Item %s" % self.template_name)
        # Find the folder by the given folder name
        self.folder_id = self.get_folder_by_name(self.datacenter, self.folder)
        if not self.folder_id:
            self.module.fail_json(msg="Failed to find the folder %s" % self.folder)
        # Find the Host by given HostName
        self.host_id = None
        if self.host:
            self.host_id = self.get_host_by_name(self.datacenter, self.host)
            if not self.host_id:
                self.module.fail_json(msg="Failed to find the Host %s" % self.host)

        # Find the resourcepool by the given resourcepool name
        self.cluster_id = None
        self.resourcepool_id = None

        if self.resourcepool:
            self.resourcepool_id = self.get_resource_pool_by_name(self.datacenter, self.resourcepool, self.cluster, self.host)
            if not self.resourcepool_id:
                self.module.fail_json(msg="Failed to find the resource_pool %s" % self.resourcepool)

        # Find the Cluster by the given Cluster name
        if self.cluster:
            self.cluster_id = self.get_cluster_by_name(self.datacenter, self.cluster)
            if not self.cluster_id:
                self.module.fail_json(msg="Failed to find the Cluster %s" % self.cluster)
            cluster_obj = self.api_client.vcenter.Cluster.get(self.cluster_id)
            self.resourcepool_id = cluster_obj.resource_pool

        # Create VM placement specs
        self.placement_spec = LibraryItems.DeployPlacementSpec(folder=self.folder_id)
        if self.host_id:
            self.placement_spec.host = self.host_id
        if self.resourcepool_id:
            self.placement_spec.resource_pool = self.resourcepool_id
        if self.cluster_id:
            self.placement_spec.cluster = self.cluster_id
        self.vm_home_storage_spec = LibraryItems.DeploySpecVmHomeStorage(datastore=to_native(self.datastore_id))
        self.disk_storage_spec = LibraryItems.DeploySpecDiskStorage(datastore=to_native(self.datastore_id))
        self.deploy_spec = LibraryItems.DeploySpec(name=self.vm_name,
                                                   placement=self.placement_spec,
                                                   vm_home_storage=self.vm_home_storage_spec,
                                                   disk_storage=self.disk_storage_spec,
                                                   powered_on=power_on
                                                   )
        vm_id = ''
        try:
            vm_id = self.template_service.deploy(self.library_item_id, self.deploy_spec)
        except Error as error:
            self.module.fail_json(msg="%s" % self.get_error_message(error))
        except Exception as err:
            self.module.fail_json(msg="%s" % to_native(err))

        if vm_id:
            self.module.exit_json(
                changed=True,
                vm_deploy_info=dict(
                    msg="Deployed Virtual Machine '%s'." % self.vm_name,
                    vm_id=vm_id,
                )
            )
        self.module.exit_json(changed=False,
                              vm_deploy_info=dict(msg="Virtual Machine deployment failed", vm_id=vm_id))


def main():
    argument_spec = VmwareRestClient.vmware_client_argument_spec()
    argument_spec.update(
        state=dict(type='str', default='present',
                   choices=['present', 'poweredon']),
        template=dict(type='str', aliases=['template_src'], required=True),
        content_library=dict(type='str', aliases=[
                             'content_library_src'], required=False),
        name=dict(type='str', required=True, aliases=['vm_name']),
        datacenter=dict(type='str', required=True),
        datastore=dict(type='str', required=False),
        datastore_cluster=dict(type='str', required=False),
        folder=dict(type='str', required=True),
        host=dict(type='str', required=False),
        resource_pool=dict(type='str', required=False),
        cluster=dict(type='str', required=False),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_one_of=[
            ['datastore', 'datastore_cluster'],
        ],
    )
    result = {'failed': False, 'changed': False}

    vmware_contentlib_create = VmwareContentDeployTemplate(module)
    if module.params['state'] in ['present']:
        if module.check_mode:
            result.update(
                vm_name=module.params['name'],
                changed=True,
                desired_operation='Create VM with PowerOff State',
            )
            module.exit_json(**result)
        vmware_contentlib_create.deploy_vm_from_template()
    if module.params['state'] == 'poweredon':
        if module.check_mode:
            result.update(
                vm_name=module.params['name'],
                changed=True,
                desired_operation='Create VM with PowerON State',
            )
            module.exit_json(**result)
        vmware_contentlib_create.deploy_vm_from_template(power_on=True)


if __name__ == '__main__':
    main()

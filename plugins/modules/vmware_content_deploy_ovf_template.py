#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020, Lev Goncharov <lev@goncharov.xyz>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: vmware_content_deploy_ovf_template
short_description: Deploy Virtual Machine from ovf template stored in content library.
description:
- Module to deploy virtual machine from ovf template in content library.
author:
- Lev Goncharv (@ultral)
requirements:
- vSphere Automation SDK
options:
    log_level:
      description:
      - The level of logging desired in this module.
      type: str
      required: false
      default: 'normal'
      choices: [ 'debug', 'info', 'normal' ]
    template:
      description:
      - The name of OVF template from which VM to be deployed.
      type: str
      required: true
      aliases: ['ovf', 'ovf_template', 'template_src']
    library:
      description:
      - The name of the content library from where the template resides.
      type: str
      required: false
      aliases: ['content_library', 'content_library_src']
    name:
      description:
      - The name of the VM to be deployed.
      type: str
      required: true
      aliases: ['vm_name']
    datacenter:
      description:
      - Name of the datacenter, where VM to be deployed.
      type: str
      required: true
    datastore:
      description:
      - Name of the datastore to store deployed VM and disk.
      type: str
      required: false
    datastore_cluster:
      description:
      - Name of the datastore cluster housing a datastore to store deployed VM and disk.
      - If datastore is not specified, the recommended datastore from this cluster will be used.
      type: str
      required: false
    folder:
      description:
      - Name of the folder in datacenter in which to place deployed VM.
      type: str
      default: 'vm'
    host:
      description:
      - Name of the ESX Host in datacenter in which to place deployed VM. The host has to be a member of the cluster that contains the resource pool.
      type: str
      required: false
    resource_pool:
      description:
      - Name of the resourcepool in datacenter in which to place deployed VM.
      type: str
      required: false
    cluster:
      description:
      - Name of the cluster in datacenter in which to place deployed VM.
      type: str
      required: false
    storage_provisioning:
      description:
      - Default storage provisioning type to use for all sections of type vmw:StorageSection in the OVF descriptor.
      type: str
      default: 'thin'
      choices: [ thin, thick, eagerZeroedThick, eagerzeroedthick ]
extends_documentation_fragment: community.vmware.vmware_rest_client.documentation
'''

EXAMPLES = r'''
- name: Deploy Virtual Machine from OVF template in content library
  community.vmware.vmware_content_deploy_ovf_template:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    ovf_template: rhel_test_template
    datastore: Shared_NFS_Volume
    folder: vm
    datacenter: Sample_DC_1
    name: Sample_VM
    resource_pool: test_rp
  delegate_to: localhost

- name: Deploy Virtual Machine from OVF template in content library with eagerZeroedThick storage
  vmware_content_deploy_ovf_template:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    ovf_template: rhel_test_template
    datastore: Shared_NFS_Volume
    folder: vm
    datacenter: Sample_DC_1
    name: Sample_VM
    resource_pool: test_rp
    storage_provisioning: eagerZeroedThick
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

from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible.module_utils._text import to_native
from ansible_collections.community.vmware.plugins.module_utils.vmware_rest_client import VmwareRestClient
from ansible_collections.community.vmware.plugins.module_utils.vmware import PyVmomi

HAS_VAUTOMATION = False
try:
    from com.vmware.vcenter.ovf_client import LibraryItem
    from com.vmware.vapi.std.errors_client import Error
    HAS_VAUTOMATION = True
except ImportError:
    pass


class VmwareContentDeployOvfTemplate(VmwareRestClient):
    def __init__(self, module):
        """Constructor."""
        super(VmwareContentDeployOvfTemplate, self).__init__(module)

        # Initialize member variables
        self.module = module
        self._pyv = PyVmomi(module=module)
        self._template_service = self.api_client.vcenter.vm_template.LibraryItems
        self._datacenter_id = None
        self._datastore_id = None
        self._library_item_id = None
        self._folder_id = None
        self._host_id = None
        self._cluster_id = None
        self._resourcepool_id = None
        self.result = {}

        # Turn on debug if not specified, but ANSIBLE_DEBUG is set
        if self.module._debug:
            self.warn('Enable debug output because ANSIBLE_DEBUG was set.')
            self.params['log_level'] = 'debug'
        self.log_level = self.params['log_level']
        if self.log_level == 'debug':
            # Turn on debugging
            self.result['debug'] = {}

        # Get parameters
        self.template = self.params.get('template')
        self.library = self.params.get('library')
        self.vm_name = self.params.get('name')
        self.datacenter = self.params.get('datacenter')
        self.datastore = self.params.get('datastore')
        self.datastore_cluster = self.params.get('datastore_cluster')
        self.folder = self.params.get('folder')
        self.resourcepool = self.params.get('resource_pool')
        self.cluster = self.params.get('cluster')
        self.host = self.params.get('host')
        self.storage_provisioning = self.params['storage_provisioning']
        if self.storage_provisioning == 'eagerzeroedthick':
            self.storage_provisioning = 'eagerZeroedThick'

        vm = self._pyv.get_vm()
        if vm:
            self.result['vm_deploy_info'] = dict(
                msg="Virtual Machine '%s' already Exists." % self.vm_name,
                vm_id=vm._moId,
            )
            self._fail(msg="Virtual Machine deployment failed")

    def deploy_vm_from_ovf_template(self):
        # Find the datacenter by the given datacenter name
        self._datacenter_id = self.get_datacenter_by_name(self.datacenter)
        if not self._datacenter_id:
            self._fail(msg="Failed to find the datacenter %s" % self.datacenter)

        # Find the datastore by the given datastore name
        if self.datastore:
            self._datastore_id = self.get_datastore_by_name(self.datacenter, self.datastore)
            if not self._datastore_id:
                self._fail(msg="Failed to find the datastore %s" % self.datastore)

        # Find the datastore by the given datastore cluster name
        if self.datastore_cluster and not self._datastore_id:
            dsc = self._pyv.find_datastore_cluster_by_name(self.datastore_cluster)
            if dsc:
                self.datastore = self._pyv.get_recommended_datastore(dsc)
                self._datastore_id = self.get_datastore_by_name(self.datacenter, self.datastore)
            else:
                self._fail(msg="Failed to find the datastore cluster %s" % self.datastore_cluster)

        if not self._datastore_id:
            self._fail(msg="Failed to find the datastore using either datastore or datastore cluster")

        # Find the LibraryItem (Template) by the given LibraryItem name
        if self.library:
            self._library_item_id = self.get_library_item_from_content_library_name(
                self.template, self.library
            )
            if not self._library_item_id:
                self._fail(msg="Failed to find the library Item %s in content library %s" % (self.template, self.library))
        else:
            self._library_item_id = self.get_library_item_by_name(self.template)
            if not self._library_item_id:
                self._fail(msg="Failed to find the library Item %s" % self.template)

        # Find the folder by the given FQPN folder name
        # The FQPN is I(datacenter)/I(folder type)/folder name/... for
        # example Lab/vm/someparent/myfolder is a vm folder in the Lab datacenter.
        folder_obj = self._pyv.find_folder_by_fqpn(self.folder, self.datacenter, folder_type='vm')
        if folder_obj:
            self._folder_id = folder_obj._moId
        if not self._folder_id:
            self._fail(msg="Failed to find the folder %s" % self.folder)

        # Find the Host by the given name
        if self.host:
            self._host_id = self.get_host_by_name(self.datacenter, self.host)
            if not self._host_id:
                self._fail(msg="Failed to find the Host %s" % self.host)

        # Find the Cluster by the given Cluster name
        if self.cluster:
            self._cluster_id = self.get_cluster_by_name(self.datacenter, self.cluster)
            if not self._cluster_id:
                self._fail(msg="Failed to find the Cluster %s" % self.cluster)
            cluster_obj = self.api_client.vcenter.Cluster.get(self._cluster_id)
            self._resourcepool_id = cluster_obj.resource_pool

        # Find the resourcepool by the given resourcepool name
        if self.resourcepool:
            self._resourcepool_id = self.get_resource_pool_by_name(self.datacenter, self.resourcepool, self.cluster, self.host)
            if not self._resourcepool_id:
                self._fail(msg="Failed to find the resource_pool %s" % self.resourcepool)

        if not self._resourcepool_id:
            self._fail(msg="Failed to find a resource pool either by name or cluster")

        deployment_target = LibraryItem.DeploymentTarget(
            resource_pool_id=self._resourcepool_id,
            folder_id=self._folder_id
        )

        self.ovf_summary = self.api_client.vcenter.ovf.LibraryItem.filter(
            ovf_library_item_id=self._library_item_id,
            target=deployment_target
        )

        self.deploy_spec = LibraryItem.ResourcePoolDeploymentSpec(
            name=self.vm_name,
            annotation=self.ovf_summary.annotation,
            accept_all_eula=True,
            network_mappings=None,
            storage_mappings=None,
            storage_provisioning=self.storage_provisioning,
            storage_profile_id=None,
            locale=None,
            flags=None,
            additional_parameters=None,
            default_datastore_id=self._datastore_id
        )

        response = {
            'succeeded': False
        }
        try:
            response = self.api_client.vcenter.ovf.LibraryItem.deploy(self._library_item_id, deployment_target, self.deploy_spec)
        except Error as error:
            self._fail(msg="%s" % self.get_error_message(error))
        except Exception as err:
            self._fail(msg="%s" % to_native(err))

        if not response.succeeded:
            self.result['vm_deploy_info'] = dict(
                msg="Virtual Machine deployment failed",
                vm_id=''
            )
            self._fail(msg="Virtual Machine deployment failed")
        self.result['changed'] = True
        self.result['vm_deploy_info'] = dict(
            msg="Deployed Virtual Machine '%s'." % self.vm_name,
            vm_id=response.resource_id.id,
        )
        self._exit()

    #
    # Wrap AnsibleModule methods
    #

    def _mod_debug(self):
        if self.log_level == 'debug':
            self.result['debug'].update(
                dict(
                    datacenter_id=self._datacenter_id,
                    datastore_id=self._datastore_id,
                    library_item_id=self._library_item_id,
                    folder_id=self._folder_id,
                    host_id=self._host_id,
                    cluster_id=self._cluster_id,
                    resourcepool_id=self._resourcepool_id,
                )
            )

    def _fail(self, msg):
        self._mod_debug()
        self.module.fail_json(msg=msg, **self.result)

    def _exit(self):
        self._mod_debug()
        self.module.exit_json(**self.result)


def main():
    argument_spec = VmwareRestClient.vmware_client_argument_spec()
    argument_spec.update(
        log_level=dict(
            type='str',
            choices=[
                'debug',
                'info',
                'normal',
            ],
            default='normal'
        ),
        template=dict(
            type='str',
            aliases=[
                'ovf',
                'ovf_template',
                'template_src'
            ],
            required=True
        ),
        library=dict(
            type='str',
            aliases=[
                'content_library',
                'content_library_src'
            ],
            required=False
        ),
        name=dict(
            type='str',
            aliases=[
                'vm_name'
            ],
            required=True
        ),
        datacenter=dict(
            type='str',
            required=True
        ),
        datastore=dict(
            type='str',
            required=False
        ),
        datastore_cluster=dict(
            type='str',
            required=False
        ),
        folder=dict(
            type='str',
            default='vm'
        ),
        host=dict(
            type='str',
            required=False
        ),
        resource_pool=dict(
            type='str',
            required=False
        ),
        cluster=dict(
            type='str',
            required=False
        ),
        storage_provisioning=dict(
            type='str',
            choices=[
                'thin',
                'thick',
                'eagerZeroedThick',
                'eagerzeroedthick'
            ],
            default='thin',
            fallback=(
                env_fallback,
                ['VMWARE_STORAGE_PROVISIONING']
            )
        ),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_one_of=[
            ['datastore', 'datastore_cluster'],
            ['host', 'cluster', 'resource_pool'],
        ],
    )

    result = {'failed': False, 'changed': False}
    vmware_contentlib_create = VmwareContentDeployOvfTemplate(module)
    if module.check_mode:
        result.update(
            vm_name=module.params['name'],
            changed=True,
            desired_operation='Create VM with PowerOff State',
        )
        module.exit_json(**result)
    vmware_contentlib_create.deploy_vm_from_ovf_template()


if __name__ == '__main__':
    main()

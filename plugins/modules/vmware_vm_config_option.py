#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2021, Ansible Project
# Copyright: (c) 2021, VMware, Inc. All Rights Reserved.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: vmware_vm_config_option
short_description: Return supported guest ID list and VM recommended config option for specific guest OS
description: >
   This module is used for getting the hardware versions supported for creation, the guest ID list supported by ESXi
   host for the most recent virtual hardware supported or specified hardware version, the VM recommended config options
   for specified guest OS ID.
author:
- Diane Wang (@Tomorrow9) <dianew@vmware.com>
version_added: '1.15.0'
notes:
- Tested on vSphere 6.5
- Tested on vSphere 6.7
- Known issue on vSphere 7.0 (https://github.com/vmware/pyvmomi/issues/915)
requirements:
- python >= 2.6
- PyVmomi
- System.View privilege
options:
  datacenter:
    description:
    - The datacenter name used to get specified cluster or host.
    - This parameter is case sensitive.
    default: ha-datacenter
    type: str
  cluster_name:
    description:
    - Name of the cluster.
    - If C(esxi_hostname) is not given, this parameter is required.
    type: str
  esxi_hostname:
    description:
    - ESXi hostname.
    - Obtain VM configure options on this ESXi host.
    - If C(cluster_name) is not given, this parameter is required.
    type: str
  get_hardware_versions:
    description:
    - Return the list of VM hardware versions supported for creation and the default hardware version on the
      specified entity.
    type: bool
    default: false
  get_guest_os_ids:
    description:
    - Return the list of guest OS IDs supported on the specified entity.
    - If C(hardware_version) is set, will return the corresponding guest OS ID list supported, or will return the
      guest OS ID list for the default hardware version.
    type: bool
    default: false
  get_config_options:
    description:
    - Return the dict of VM recommended config options for guest ID specified by C(guest_id) with hardware version
      specified by C(hardware_version) or the default hardware version.
    - When set to True, C(guest_id) must be set.
    type: bool
    default: false
  guest_id:
    description:
    - The guest OS ID from the returned list when C(get_guest_os_ids) is set to C(True), e.g., 'rhel8_64Guest'.
    - This parameter must be set when C(get_config_options) is set to C(True).
    type: str
  hardware_version:
    description:
    - The hardware version from the returned list when C(get_hardware_versions) is set to C(True), e.g., 'vmx-19'.
    type: str
extends_documentation_fragment:
- community.vmware.vmware.documentation

'''

EXAMPLES = r'''
- name: Get supported guest ID list on given ESXi host for with default hardware version
  community.vmware.vmware_vm_config_option:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    esxi_hostname: "{{ esxi_hostname }}"
    get_guest_os_ids: True
  delegate_to: localhost

- name: Get VM recommended config option for Windows 10 guest OS on given ESXi host
  community.vmware.vmware_vm_config_option:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    esxi_hostname: "{{ esxi_hostname }}"
    get_config_options: True
    guest_id: "windows9_64Guest"
  delegate_to: localhost
'''

RETURN = r'''
instance:
    description: metadata about the VM recommended configuration
    returned: always
    type: dict
    sample: None
'''

HAS_PYVMOMI = False
try:
    from pyVmomi import vim, vmodl
    HAS_PYVMOMI = True
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible_collections.community.vmware.plugins.module_utils.vmware import find_obj, vmware_argument_spec, PyVmomi
from ansible_collections.community.vmware.plugins.module_utils.vm_device_helper import PyVmomiDeviceHelper


class VmConfigOption(PyVmomi):
    def __init__(self, module):
        super(VmConfigOption, self).__init__(module)
        self.device_helper = PyVmomiDeviceHelper(self.module)
        self.ctl_device_type = self.device_helper.scsi_device_type.copy()
        self.ctl_device_type.update({'sata': self.device_helper.sata_device_type,
                                     'nvme': self.device_helper.nvme_device_type}
                                    )
        self.ctl_device_type.update(self.device_helper.usb_device_type)
        self.ctl_device_type.update(self.device_helper.nic_device_type)

    def get_hardware_versions(self, env_browser):
        support_create = []
        default_config = ''
        try:
            desc = env_browser.QueryConfigOptionDescriptor()
        except vmodl.RuntimeFault as runtime_fault:
            self.module.fail_json(msg=to_native(runtime_fault.msg))
        except Exception as generic_fault:
            self.module.fail_json(msg="Failed to obtain VM config option descriptor due to fault: %s" % generic_fault)
        if desc:
            for option_desc in desc:
                if option_desc.createSupported:
                    support_create = support_create + [option_desc.key]
                if option_desc.defaultConfigOption:
                    default_config = option_desc.key

        return support_create, default_config

    def get_config_option_by_spec(self, env_browser, guest_id=None, host=None, key=''):
        vm_config_option = None
        if guest_id is None:
            guest_id = []
        config_query_spec = vim.EnvironmentBrowser.ConfigOptionQuerySpec(guestId=guest_id, host=host, key=key)
        try:
            vm_config_option = env_browser.QueryConfigOptionEx(spec=config_query_spec)
        except vmodl.RuntimeFault as runtime_fault:
            self.module.fail_json(msg=to_native(runtime_fault.msg))
        except Exception as generic_fault:
            self.module.fail_json(msg="Failed to obtain VM config options due to fault: %s" % generic_fault)

        return vm_config_option

    def get_config_option_recommended(self, guest_os_desc, hwv_version=''):
        guest_os_option_dict = {}
        if guest_os_desc and len(guest_os_desc) != 0:
            default_disk_ctl = default_ethernet = default_cdrom_ctl = default_usb_ctl = ''
            for name, type in self.ctl_device_type.items():
                if type == guest_os_desc[0].recommendedDiskController:
                    default_disk_ctl = name
                if type == guest_os_desc[0].recommendedEthernetCard:
                    default_ethernet = name
                if type == guest_os_desc[0].recommendedCdromController:
                    default_cdrom_ctl = name
                if type == guest_os_desc[0].recommendedUSBController:
                    default_usb_ctl = name
            guest_os_option_dict = {
                'Hardware version': hwv_version,
                'Guest ID': guest_os_desc[0].id,
                'Guest fullname': guest_os_desc[0].fullName,
                'Default CPU cores per socket': guest_os_desc[0].numRecommendedCoresPerSocket,
                'Default CPU socket': guest_os_desc[0].numRecommendedPhysicalSockets,
                'Default memory in MB': guest_os_desc[0].recommendedMemMB,
                'Default firmware': guest_os_desc[0].recommendedFirmware,
                'Default secure boot': guest_os_desc[0].defaultSecureBoot,
                'Support secure boot': guest_os_desc[0].supportsSecureBoot,
                'Default disk controller': default_disk_ctl,
                'Default disk size in MB': guest_os_desc[0].recommendedDiskSizeMB,
                'Default network adapter': default_ethernet,
                'Default CDROM controller': default_cdrom_ctl,
                'Default USB controller': default_usb_ctl
            }

        return guest_os_option_dict

    def get_guest_id_list(self, guest_os_desc):
        gos_id_list = []
        if guest_os_desc:
            for gos_desc in guest_os_desc.guestOSDescriptor:
                gos_id_list = gos_id_list + [gos_desc.id]

        return gos_id_list

    def get_config_option_for_guest(self):
        results = {}
        guest_id = []
        host = None
        datacenter_name = self.params.get('datacenter')
        cluster_name = self.params.get('cluster_name')
        esxi_host_name = self.params.get('esxi_hostname')
        if self.params.get('guest_id'):
            guest_id = [self.params.get('guest_id')]

        if not self.params.get('get_hardware_versions') and not self.params.get('get_guest_os_ids') \
                and not self.params.get('get_config_options'):
            self.module.exit_json(msg="Please set at least one of these parameters 'get_hardware_versions',"
                                      " 'get_guest_os_ids', 'get_config_options' to True to get the desired info.")
        if self.params.get('get_config_options') and len(guest_id) == 0:
            self.module.fail_json(msg="Please set 'guest_id' when 'get_config_options' is set to True,"
                                      " to get the VM recommended config option for specific guest OS.")

        # Get the datacenter object
        datacenter = find_obj(self.content, [vim.Datacenter], datacenter_name)
        if not datacenter:
            self.module.fail_json(msg='Unable to find datacenter "%s"' % datacenter_name)
        # Get the cluster object
        if cluster_name:
            cluster = find_obj(self.content, [vim.ComputeResource], cluster_name, folder=datacenter)
            if not cluster:
                self.module.fail_json(msg='Unable to find cluster "%s"' % cluster_name)
        # If host is given, get the cluster object using the host
        elif esxi_host_name:
            host = find_obj(self.content, [vim.HostSystem], esxi_host_name, folder=datacenter)
            if not host:
                self.module.fail_json(msg='Unable to find host "%s"' % esxi_host_name)
            cluster = host.parent
        # Define the environment browser object the ComputeResource presents
        env_browser = cluster.environmentBrowser
        if env_browser is None:
            self.module.fail_json(msg="The environmentBrowser of the ComputeResource is None, so can not get the"
                                      " desired config option info, please check your vSphere environment.")
        # Get supported hardware versions list
        support_create_list, default_config = self.get_hardware_versions(env_browser=env_browser)
        if self.params.get('get_hardware_versions'):
            results.update({'Supported hardware versions': support_create_list,
                            'Default hardware version': default_config})

        if self.params.get('get_guest_os_ids') or self.params.get('get_config_options'):
            # Get supported guest ID list
            hardware_version = self.params.get('hardware_version', '')
            if hardware_version and len(support_create_list) != 0 and hardware_version not in support_create_list:
                self.module.fail_json(msg="Specified hardware version '%s' is not in the supported create list: %s"
                                          % (hardware_version, support_create_list))
            vm_config_option_all = self.get_config_option_by_spec(env_browser=env_browser, host=host,
                                                                  key=hardware_version)
            supported_gos_list = self.get_guest_id_list(guest_os_desc=vm_config_option_all)
            if self.params.get('get_guest_os_ids'):
                info_key = 'Supported guest IDs for %s' % vm_config_option_all.version
                results.update({info_key: supported_gos_list})

            if self.params.get('get_config_options') and len(guest_id) != 0:
                if supported_gos_list and guest_id[0] not in supported_gos_list:
                    self.module.fail_json(msg="Specified guest ID '%s' is not in the supported guest ID list: '%s'"
                                              % (guest_id[0], supported_gos_list))
                vm_config_option_guest = self.get_config_option_by_spec(env_browser=env_browser, host=host,
                                                                        guest_id=guest_id, key=hardware_version)
                guest_os_options = vm_config_option_guest.guestOSDescriptor
                guest_os_option_dict = self.get_config_option_recommended(guest_os_desc=guest_os_options,
                                                                          hwv_version=vm_config_option_guest.version)
                results.update({'Recommended config options': guest_os_option_dict})

        self.module.exit_json(changed=False, failed=False, instance=results)


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        datacenter=dict(type='str', default='ha-datacenter'),
        cluster_name=dict(type='str'),
        esxi_hostname=dict(type='str'),
        get_hardware_versions=dict(type='bool', default=False),
        get_guest_os_ids=dict(type='bool', default=False),
        get_config_options=dict(type='bool', default=False),
        guest_id=dict(type='str'),
        hardware_version=dict(type='str'),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_one_of=[
            ['cluster_name', 'esxi_hostname'],
        ]
    )
    vm_config_option_guest = VmConfigOption(module)
    vm_config_option_guest.get_config_option_for_guest()


if __name__ == "__main__":
    main()

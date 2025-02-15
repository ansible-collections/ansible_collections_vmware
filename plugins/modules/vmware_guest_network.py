#!/usr/bin/python

# Copyright: (c) 2020, Ansible Project
# Copyright: (c) 2019, Diane Wang <dianew@vmware.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: vmware_guest_network
short_description: Manage network adapters of specified virtual machine in given vCenter infrastructure
description:
  - This module is used to add, reconfigure, remove network adapter of given virtual machine.
author:
  - Diane Wang (@Tomorrow9) <dianew@vmware.com>
notes:
  - For backwards compatibility network_data is returned when using the gather_network_info parameter
options:
  name:
    description:
      - Name of virtual machine
      - Required if O(uuid) or O(moid) is not supplied.
    type: str
  uuid:
    description:
      - vm uuid
      - Required if O(name) or O(moid) is not supplied.
    type: str
  use_instance_uuid:
    description:
      - Whether to use the VMware instance UUID rather than the BIOS UUID.
    default: false
    type: bool
  moid:
    description:
      - Managed Object ID of the instance to manage if known, this is a unique identifier only within a single vCenter instance.
      - Required if O(uuid) or O(name) is not supplied.
    type: str
  folder:
    description:
      - Folder location of given VM, this is only required when there's multiple VM's with the same name.
    type: str
  datacenter:
    default: ha-datacenter
    description:
      - Datacenter the VM belongs to.
    type: str
  cluster:
    description:
      - Name of cluster where VM belongs to.
    type: str
  esxi_hostname:
    description:
      - The hostname of the ESXi host where the VM belongs to.
    type: str
  mac_address:
    description:
      - MAC address of the NIC that should be altered, if a MAC address is not supplied a new nic will be created.
      - Required when O(state=absent).
    type: str
  label:
    description:
      - 'Label of the NIC that should be altered. O(mac_address) or O(label) should be set to get the corresponding
        device to reconfigure.'
      - Alter the name of the network adapter.
    type: str
  vlan_id:
    description:
      - VLAN id associated with the network.
    type: int
  network_name:
    description:
      - Name of network in vSphere.
      - Work faster then o(vlan_id) for big infrastructure with many networks.
    type: str
  device_type:
    default: vmxnet3
    description:
      - Type of virtual network device.
      - 'Valid choices are - V(e1000), V(e1000e), V(pcnet32), V(vmxnet2), V(vmxnet3) (default), V(sriov), V(pvrdma).'
    type: str
  pvrdma_device_protocol:
    version_added: '3.3.0'
    description:
      - The PVRDMA device protocol used. Valid choices are - V(rocev1), V(rocev2).
      - This parameter is only used on the VM with hardware version >=14 and <= 19.
    type: str
  switch:
    description:
      - Name of the (dv)switch for destination network, this is only required for dvswitches.
    type: str
  guest_control:
    default: true
    description:
      - Enables guest control over whether the connectable device is connected.
    type: bool
  state:
    default: present
    choices: ['present', 'absent']
    description:
      - NIC state.
      - When V(present), a nic will be added if a mac address or label does not previously exists or is unset.
      - When V(absent), the O(mac_address) parameter has to be set.
    type: str
  start_connected:
    default: true
    description:
      - If NIC should be connected to network on startup.
    type: bool
  wake_onlan:
    default: false
    description:
      - Enable wake on LAN.
    type: bool
  connected:
    default: true
    description:
      - If NIC should be connected to the network.
    type: bool
  directpath_io:
    default: false
    description:
      - Enable Universal Pass-through (UPT).
      - Only compatible with the O(device_type=vmxnet3).
    type: bool
  physical_function_backing:
    type: str
    description:
      - If set, specifies the PCI ID of the physical function to use as backing for a SR-IOV network adapter.
      - This option is only compatible for SR-IOV network adapters.
  virtual_function_backing:
    type: str
    description:
      - If set, specifies the PCI ID of the physical function to use as backing for a SR-IOV network adapter.
      - This option is only compatible for SR-IOV network adapters.
  allow_guest_os_mtu_change:
    default: true
    type: bool
    description:
      - Allows the guest OS to change the MTU on a SR-IOV network adapter.
      - This option is only compatible for SR-IOV network adapters.
  force:
    default: false
    description:
      - Force adapter creation even if an existing adapter is attached to the same network.
    type: bool
  gather_network_info:
    aliases:
      - gather_network_facts
    default: false
    description:
      - Return information about current guest network adapters.
    type: bool
extends_documentation_fragment:
- community.vmware.vmware.documentation
'''

EXAMPLES = r'''
- name: change network for 00:50:56:11:22:33 on vm01.domain.fake
  community.vmware.vmware_guest_network:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    datacenter: "{{ datacenter_name }}"
    name: vm01.domain.fake
    mac_address: 00:50:56:11:22:33
    network_name: admin-network
    state: present

- name: add a nic on network with vlan id 2001 for 422d000d-2000-ffff-0000-b00000000000
  community.vmware.vmware_guest_network:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    datacenter: "{{ datacenter_name }}"
    uuid: 422d000d-2000-ffff-0000-b00000000000
    vlan_id: 2001

- name: remove nic with mac 00:50:56:11:22:33 from vm01.domain.fake
  community.vmware.vmware_guest_network:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    datacenter: "{{ datacenter_name }}"
    mac_address: 00:50:56:11:22:33
    name: vm01.domain.fake
    state: absent

- name: add multiple nics to vm01.domain.fake
  community.vmware.vmware_guest_network:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    datacenter: "{{ datacenter_name }}"
    name: vm01.domain.fake
    state: present
    vlan_id: "{{ item.vlan_id | default(omit) }}"
    network_name: "{{ item.network_name | default(omit) }}"
    connected: "{{ item.connected | default(omit) }}"
  loop:
    - vlan_id: 2000
      connected: false
    - network_name: guest-net
      connected: true
'''

RETURN = r'''
network_info:
  description: metadata about the virtual machine network adapters
  returned: always
  type: list
  sample:
    "network_info": [
        {
            "mac_address": "00:50:56:AA:AA:AA",
            "allow_guest_ctl": true,
            "connected": true,
            "device_type": "vmxnet3",
            "label": "Network adapter 2",
            "network_name": "admin-net",
            "start_connected": true,
            "switch": "vSwitch0",
            "unit_number": 8,
            "vlan_id": 10,
            "wake_onlan": false
        },
        {
            "mac_address": "00:50:56:BB:BB:BB",
            "allow_guest_ctl": true,
            "connected": true,
            "device_type": "vmxnet3",
            "label": "Network adapter 1",
            "network_name": "guest-net",
            "start_connected": true,
            "switch": "vSwitch0",
            "unit_number": 7,
            "vlan_id": 10,
            "wake_onlan": true
        }
    ]
network_data:
  description: For backwards compatibility, metadata about the virtual machine network adapters
  returned: when using gather_network_info parameter
  type: dict
  sample:
    "network_data": {
        '0': {
            "mac_addr": "00:50:56:AA:AA:AA",
            "mac_address": "00:50:56:AA:AA:AA",
            "allow_guest_ctl": true,
            "connected": true,
            "device_type": "vmxnet3",
            "label": "Network adapter 2",
            "name": "admin-net",
            "network_name": "admin-net",
            "start_connected": true,
            "switch": "vSwitch0",
            "unit_number": 8,
            "vlan_id": 10,
            "wake_onlan": false
        },
        '1': {
            "mac_addr": "00:50:56:BB:BB:BB",
            "mac_address": "00:50:56:BB:BB:BB",
            "allow_guest_ctl": true,
            "connected": true,
            "device_type": "vmxnet3",
            "label": "Network adapter 1",
            "name": "guest-net",
            "network_name": "guest-net",
            "start_connected": true,
            "switch": "vSwitch0",
            "unit_number": 7,
            "vlan_id": 10,
            "wake_onlan": true
        }
    }

'''

try:
    from pyVmomi import vim
except ImportError:
    pass

import copy
from ansible.module_utils._text import to_native
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.community.vmware.plugins.module_utils.vmware import PyVmomi, TaskError, vmware_argument_spec, wait_for_task
from ansible_collections.community.vmware.plugins.module_utils.vm_device_helper import PyVmomiDeviceHelper


class PyVmomiHelper(PyVmomi):
    def __init__(self, module):
        super(PyVmomiHelper, self).__init__(module)
        self.change_detected = False
        self.device_helper = PyVmomiDeviceHelper(self.module)

    def _get_network_object(self, vm_obj):
        '''
        return network object matching given parameters
        :param vm_obj: vm object
        :return: network object
        :rtype: object
        '''
        if not self.params['esxi_hostname'] or not self.params['cluster']:
            compute_resource = vm_obj.runtime.host
        else:
            compute_resource = self._get_compute_resource_by_name()

        pg_lookup = {}
        vlan_id = self.params['vlan_id']
        network_name = self.params['network_name']
        switch_name = self.params['switch']

        for pg in vm_obj.runtime.host.config.network.portgroup:
            pg_lookup[pg.spec.name] = {'switch': pg.spec.vswitchName, 'vlan_id': pg.spec.vlanId}

        if network_name:
            networks = self.find_network_by_name(network_name)
            for network in networks:
                if network in compute_resource.network:
                    if isinstance(network, vim.dvs.DistributedVirtualPortgroup):
                        dvs = network.config.distributedVirtualSwitch
                        if (switch_name and dvs.config.name == switch_name) or not switch_name:
                            return network
                    elif isinstance(network, vim.Network):
                        return network

        if compute_resource:
            for network in compute_resource.network:
                if isinstance(network, vim.dvs.DistributedVirtualPortgroup):
                    dvs = network.config.distributedVirtualSwitch
                    if (switch_name and dvs.config.name == switch_name) or not switch_name:
                        if network.config.name == network_name:
                            return network
                        if hasattr(network.config.defaultPortConfig.vlan, 'vlanId') and \
                           network.config.defaultPortConfig.vlan.vlanId == vlan_id:
                            return network
                        if hasattr(network.config.defaultPortConfig.vlan, 'pvlanId') and \
                           network.config.defaultPortConfig.vlan.pvlanId == vlan_id:
                            return network
                elif isinstance(network, vim.Network):
                    if network_name and network_name == network.name:
                        return network
                    if vlan_id:
                        for k in pg_lookup.keys():
                            if vlan_id == pg_lookup[k]['vlan_id']:
                                if k == network.name:
                                    return network
                                break
        return None

    def _get_vlanid_from_network(self, network):
        '''
        get the vlan id from network object
        :param network: network object to expect, either vim.Network or vim.dvs.DistributedVirtualPortgroup
        :return: vlan id as an integer
        :rtype: integer
        '''
        vlan_id = None
        if isinstance(network, vim.dvs.DistributedVirtualPortgroup):
            vlan_id = network.config.defaultPortConfig.vlan.vlanId

        if isinstance(network, vim.Network) and hasattr(network, 'host'):
            for host in network.host:
                for pg in host.config.network.portgroup:
                    if pg.spec.name == network.name:
                        vlan_id = pg.spec.vlanId
                        return vlan_id

        return vlan_id

    def _get_nics_from_vm(self, vm_obj):
        '''
        return a list of dictionaries containing vm nic info and
        a list of objects
        :param vm_obj: object containing virtual machine
        :return: list of dicts and list ith nic object(s)
        :rtype: list, list
        '''
        nic_info_lst = []
        nics = [nic for nic in vm_obj.config.hardware.device if isinstance(nic, vim.vm.device.VirtualEthernetCard)]
        for nic in nics:
            # common items of nic parameters
            d_item = dict(
                mac_address=nic.macAddress,
                label=nic.deviceInfo.label,
                unit_number=nic.unitNumber,
                wake_onlan=nic.wakeOnLanEnabled,
                allow_guest_ctl=nic.connectable.allowGuestControl,
                connected=nic.connectable.connected,
                start_connected=nic.connectable.startConnected,
            )
            # If NIC is a SR-IOV adapter
            if isinstance(nic, vim.vm.device.VirtualSriovEthernetCard):
                d_item['allow_guest_os_mtu_change'] = nic.allowGuestOSMtuChange
                if isinstance(nic.sriovBacking, vim.vm.device.VirtualSriovEthernetCard.SriovBackingInfo):
                    if isinstance(nic.sriovBacking.physicalFunctionBacking, vim.vm.device.VirtualPCIPassthrough):
                        d_item['physical_function_backing'] = nic.sriovBacking.physicalFunctionBacking.id
                    if isinstance(nic.sriovBacking.virtualFunctionBacking, vim.vm.device.VirtualPCIPassthrough):
                        d_item['virtual_function_backing'] = nic.sriovBacking.virtualFunctionBacking.id
            # If a distributed port group specified
            if isinstance(nic.backing, vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo):
                key = nic.backing.port.portgroupKey
                for portgroup in vm_obj.network:
                    if hasattr(portgroup, 'key') and portgroup.key == key:
                        d_item['network_name'] = portgroup.name
                        d_item['switch'] = portgroup.config.distributedVirtualSwitch.name
                        break
            # If an NSX-T port group specified
            elif isinstance(nic.backing, vim.vm.device.VirtualEthernetCard.OpaqueNetworkBackingInfo):
                d_item['network_name'] = nic.backing.opaqueNetworkId
                d_item['switch'] = nic.backing.opaqueNetworkType
            # If a port group specified
            elif isinstance(nic.backing, vim.vm.device.VirtualEthernetCard.NetworkBackingInfo):
                d_item['network_name'] = nic.backing.network.name
                d_item['vlan_id'] = self._get_vlanid_from_network(nic.backing.network)
                if isinstance(nic.backing.network, vim.Network):
                    for pg in vm_obj.runtime.host.config.network.portgroup:
                        if pg.spec.name == nic.backing.network.name:
                            d_item['switch'] = pg.spec.vswitchName
                            break

            for k in self.device_helper.nic_device_type:
                if isinstance(nic, self.device_helper.nic_device_type[k]):
                    d_item['device_type'] = k
                    # VirtualVmxnet3Vrdma extends VirtualVmxnet3
                    if k == 'vmxnet3':
                        continue
                    else:
                        break
            if d_item['device_type'] == 'pvrdma':
                d_item['device_protocol'] = nic.deviceProtocol

            nic_info_lst.append(d_item)

        nic_info_lst = sorted(nic_info_lst, key=lambda d: d['mac_address'] if (d['mac_address'] is not None) else '00:00:00:00:00:00')
        return nic_info_lst, nics

    def _get_compute_resource_by_name(self, recurse=True):
        '''
        get compute resource object with matching name of esxi_hostname or cluster
        parameters.
        :param recurse: recurse vmware content folder, default is True
        :return: object matching vim.ComputeResource or None if no match
        :rtype: object
        '''
        resource_name = None
        if self.params['esxi_hostname']:
            resource_name = self.params['esxi_hostname']

        if self.params['cluster']:
            resource_name = self.params['cluster']

        container = self.content.viewManager.CreateContainerView(self.content.rootFolder, [vim.ComputeResource], recurse)
        for obj in container.view:
            if self.params['esxi_hostname'] and isinstance(obj, vim.ClusterComputeResource) and hasattr(obj, 'host'):
                for host in obj.host:
                    if host.name == resource_name:
                        return obj

            if obj.name == resource_name:
                return obj

        return None

    def _new_nic_spec(self, vm_obj, nic_obj=None, network_params=None):
        network = self._get_network_object(vm_obj)

        if network_params:
            connected = network_params['connected']
            device_type = network_params['device_type'].lower()
            directpath_io = network_params['directpath_io']
            guest_control = network_params['guest_control']
            label = network_params['label']
            mac_address = network_params['mac_address']
            start_connected = network_params['start_connected']
            wake_onlan = network_params['wake_onlan']
            pf_backing = network_params['physical_function_backing']
            vf_backing = network_params['virtual_function_backing']
            allow_guest_os_mtu_change = network_params['allow_guest_os_mtu_change']
        else:
            connected = self.params['connected']
            device_type = self.params['device_type'].lower()
            directpath_io = self.params['directpath_io']
            guest_control = self.params['guest_control']
            label = self.params['label']
            mac_address = self.params['mac_address']
            start_connected = self.params['start_connected']
            wake_onlan = self.params['wake_onlan']
            pf_backing = self.params['physical_function_backing']
            vf_backing = self.params['virtual_function_backing']
            allow_guest_os_mtu_change = self.params['allow_guest_os_mtu_change']
            pvrdma_device_protocol = self.params['pvrdma_device_protocol']

        if not nic_obj:
            device_obj = self.device_helper.nic_device_type[device_type]
            nic_spec = vim.vm.device.VirtualDeviceSpec(
                device=device_obj()
            )
            if mac_address:
                nic_spec.device.addressType = 'manual'
                nic_spec.device.macAddress = mac_address

            if label:
                nic_spec.device.deviceInfo = vim.Description(
                    label=label
                )

            if device_type == 'pvrdma' and pvrdma_device_protocol:
                nic_spec.device.deviceProtocol = pvrdma_device_protocol
        else:
            nic_spec = vim.vm.device.VirtualDeviceSpec(
                operation=vim.vm.device.VirtualDeviceSpec.Operation.edit,
                device=nic_obj
            )
            if label and label != nic_obj.deviceInfo.label:
                nic_spec.device.deviceInfo = vim.Description(
                    label=label
                )
            if mac_address and mac_address != nic_obj.macAddress:
                nic_spec.device.addressType = 'manual'
                nic_spec.device.macAddress = mac_address

        nic_spec.device.backing = self._nic_backing_from_obj(network)
        nic_spec.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo(
            startConnected=start_connected,
            allowGuestControl=guest_control,
            connected=connected
        )
        nic_spec.device.wakeOnLanEnabled = wake_onlan

        if (pf_backing is not None or vf_backing is not None) and not isinstance(nic_spec.device, vim.vm.device.VirtualSriovEthernetCard):
            self.module_fail_json(msg='physical_function_backing, virtual_function_backing can only be used with the sriov device type')

        if isinstance(nic_spec.device, vim.vm.device.VirtualSriovEthernetCard):
            nic_spec.device.allowGuestOSMtuChange = allow_guest_os_mtu_change
            nic_spec.device.sriovBacking = vim.vm.device.VirtualSriovEthernetCard.SriovBackingInfo()
            if pf_backing is not None:
                nic_spec.device.sriovBacking.physicalFunctionBacking = vim.vm.device.VirtualPCIPassthrough.DeviceBackingInfo()
                nic_spec.device.sriovBacking.physicalFunctionBacking.id = pf_backing
            if vf_backing is not None:
                nic_spec.device.sriovBacking.virtualFunctionBacking = vim.vm.device.VirtualPCIPassthrough.DeviceBackingInfo()
                nic_spec.device.sriovBacking.virtualFunctionBacking.id = vf_backing

        if directpath_io and not isinstance(nic_spec.device, vim.vm.device.VirtualVmxnet3):
            self.module.fail_json(msg='directpath_io can only be used with the vmxnet3 device type')

        if directpath_io and isinstance(nic_spec.device, vim.vm.device.VirtualVmxnet3):
            nic_spec.device.uptCompatibilityEnabled = True
        return nic_spec

    def _nic_backing_from_obj(self, network_obj):
        rv = None
        if isinstance(network_obj, vim.dvs.DistributedVirtualPortgroup):
            rv = vim.VirtualEthernetCardDistributedVirtualPortBackingInfo(
                port=vim.DistributedVirtualSwitchPortConnection(
                    portgroupKey=network_obj.key,
                    switchUuid=network_obj.config.distributedVirtualSwitch.uuid
                )
            )
        elif isinstance(network_obj, vim.OpaqueNetwork):
            rv = vim.vm.device.VirtualEthernetCard.OpaqueNetworkBackingInfo(
                opaqueNetworkType='nsx.LogicalSwitch',
                opaqueNetworkId=network_obj.summary.opaqueNetworkId
            )
        elif isinstance(network_obj, vim.Network):
            rv = vim.vm.device.VirtualEthernetCard.NetworkBackingInfo(
                deviceName=network_obj.name,
                network=network_obj
            )
        return rv

    def _nic_absent(self, network_params=None):
        changed = False
        diff = {'before': {}, 'after': {}}
        if network_params:
            mac_address = network_params['mac_address']
        else:
            mac_address = self.params['mac_address']

        device_spec = None
        vm_obj = self.get_vm()
        if not vm_obj:
            self.module.fail_json(msg='could not find vm: {0}'.format(self.params['name']))
        nic_info, nic_obj_lst = self._get_nics_from_vm(vm_obj)

        for nic in nic_info:
            diff['before'].update({nic['mac_address']: copy.copy(nic)})

        network_info = copy.deepcopy(nic_info)

        for nic_obj in nic_obj_lst:
            if nic_obj.macAddress == mac_address:
                if self.module.check_mode:
                    changed = True
                    for nic in nic_info:
                        if nic.get('mac_address') != nic_obj.macAddress:
                            diff['after'].update({nic['mac_address']: copy.copy(nic)})
                    network_info = [nic for nic in nic_info if nic.get('mac_address') != nic_obj.macAddress]
                    return diff, changed, network_info
                device_spec = vim.vm.device.VirtualDeviceSpec(
                    device=nic_obj,
                    operation=vim.vm.device.VirtualDeviceSpec.Operation.remove
                )
                break

        if not device_spec:
            diff['after'] = diff['before']
            return diff, changed, network_info

        try:
            task = vm_obj.ReconfigVM_Task(vim.vm.ConfigSpec(deviceChange=[device_spec]))
            wait_for_task(task)
        except (vim.fault.InvalidDeviceSpec, vim.fault.RestrictedVersion) as e:
            self.module.fail_json(msg='failed to reconfigure guest', detail=e.msg)

        if task.info.state == 'error':
            self.module.fail_json(msg='failed to reconfigure guest', detail=task.info.error.msg)

        vm_obj = self.get_vm()
        nic_info, nic_obj_lst = self._get_nics_from_vm(vm_obj)

        for nic in nic_info:
            diff['after'].update({nic.get('mac_address'): copy.copy(nic)})

        network_info = nic_info
        if diff['after'] != diff['before']:
            changed = True

        return diff, changed, network_info

    def _get_nic_info(self):
        rv = {'network_info': []}
        vm_obj = self.get_vm()
        nic_info, nic_obj_lst = self._get_nics_from_vm(vm_obj)

        rv['network_info'] = nic_info
        return rv

    def _nic_present(self):
        changed = False
        diff = {'before': {}, 'after': {}}
        force = self.params['force']
        label = self.params['label']
        mac_address = self.params['mac_address']
        network_name = self.params['network_name']
        switch = self.params['switch']
        vlan_id = self.params['vlan_id']

        vm_obj = self.get_vm()
        if not vm_obj:
            self.module.fail_json(msg='could not find vm: {0}'.format(self.params['name']))

        if self.params['device_type'] == 'pvrdma':
            if int(vm_obj.config.version.split('vmx-')[-1]) > 19 or int(vm_obj.config.version.split('vmx-')[-1]) == 13:
                self.params['pvrdma_device_protocol'] = None
            else:
                if self.params['pvrdma_device_protocol'] and self.params['pvrdma_device_protocol'] not in ['rocev1', 'rocev2']:
                    self.module.fail_json(msg="Valid values of parameter 'pvrdma_device_protocol' are 'rocev1',"
                                              " 'rocev2' for VM with hardware version >= 14 and <= 19.")
                if self.params['pvrdma_device_protocol'] is None:
                    self.params['pvrdma_device_protocol'] = 'rocev2'

        network_obj = self._get_network_object(vm_obj)
        nic_info, nic_obj_lst = self._get_nics_from_vm(vm_obj)
        label_lst = [d.get('label') for d in nic_info]
        mac_addr_lst = [d.get('mac_address') for d in nic_info]
        vlan_id_lst = [d.get('vlan_id') for d in nic_info]
        network_name_lst = [d.get('network_name') for d in nic_info]

        # TODO: make checks below less inelegant
        if ((vlan_id and vlan_id in vlan_id_lst) or (network_name and network_name in network_name_lst)
                and not mac_address
                and not label
                and not force):
            for nic in nic_info:
                diff['before'].update({nic.get('mac_address'): copy.copy(nic)})
                diff['after'].update({nic.get('mac_address'): copy.copy(nic)})
            return diff, changed, nic_info

        if not network_obj and (network_name or vlan_id):
            self.module.fail_json(
                msg='unable to find specified network_name/vlan_id ({0}), check parameters'.format(
                    network_name or vlan_id
                )
            )

        for nic in nic_info:
            diff['before'].update({nic.get('mac_address'): copy.copy(nic)})

        if (mac_address and mac_address in mac_addr_lst) or (label and label in label_lst):
            for nic_obj in nic_obj_lst:
                if (mac_address and nic_obj.macAddress == mac_address) or (label and label == nic_obj.deviceInfo.label):
                    device_spec = self._new_nic_spec(vm_obj, nic_obj)

            # fabricate diff for check_mode
            if self.module.check_mode:
                for nic in nic_info:
                    nic_mac = nic.get('mac_address')
                    nic_label = nic.get('label')
                    if nic_mac == mac_address or nic_label == label:
                        diff['after'][nic_mac] = copy.deepcopy(nic)
                        diff['after'][nic_mac].update({'switch': switch or nic['switch']})
                        if network_obj:
                            diff['after'][nic_mac].update(
                                {
                                    'vlan_id': self._get_vlanid_from_network(network_obj),
                                    'network_name': network_obj.name
                                }
                            )
                    else:
                        diff['after'].update({nic_mac: copy.deepcopy(nic)})

        if (not mac_address or mac_address not in mac_addr_lst) and (not label or label not in label_lst):
            device_spec = self._new_nic_spec(vm_obj, None)
            device_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
            if self.module.check_mode:
                # fabricate diff/returns for checkmode
                diff['after'] = copy.deepcopy(diff['before'])
                nic_mac = mac_address
                if not nic_mac:
                    nic_mac = 'AA:BB:CC:DD:EE:FF'
                if not label:
                    label = 'check_mode_adapter'
                diff['after'].update(
                    {
                        nic_mac: {
                            'label': label,
                            'mac_address': nic_mac,
                            'unit_number': 40000
                        }
                    }
                )
                if network_obj:
                    diff['after'][nic_mac].update(
                        {
                            'vlan_id': self._get_vlanid_from_network(network_obj),
                            'network_name': network_obj.name
                        }
                    )

        if self.module.check_mode:
            network_info = [diff['after'][i] for i in diff['after']]
            if diff['after'] != diff['before']:
                changed = True
            return diff, changed, network_info

        if not self.module.check_mode:
            try:
                task = vm_obj.ReconfigVM_Task(vim.vm.ConfigSpec(deviceChange=[device_spec]))
                wait_for_task(task)
            except (vim.fault.InvalidDeviceSpec, vim.fault.RestrictedVersion) as e:
                self.module.fail_json(msg='failed to reconfigure guest', detail=e.msg)
            except TaskError as task_e:
                self.module.fail_json(msg=to_native(task_e))

            if task.info.state == 'error':
                self.module.fail_json(msg='failed to reconfigure guest', detail=task.info.error.msg)

            vm_obj = self.get_vm()
            network_info, nic_obj_lst = self._get_nics_from_vm(vm_obj)
            for nic in network_info:
                diff['after'].update({nic.get('mac_address'): copy.copy(nic)})

            if diff['after'] != diff['before']:
                changed = True
            return diff, changed, network_info


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        name=dict(type='str'),
        uuid=dict(type='str'),
        use_instance_uuid=dict(type='bool', default=False),
        moid=dict(type='str'),
        folder=dict(type='str'),
        datacenter=dict(type='str', default='ha-datacenter'),
        esxi_hostname=dict(type='str'),
        cluster=dict(type='str'),
        mac_address=dict(type='str'),
        vlan_id=dict(type='int'),
        network_name=dict(type='str'),
        device_type=dict(type='str', default='vmxnet3'),
        pvrdma_device_protocol=dict(type='str'),
        label=dict(type='str'),
        switch=dict(type='str'),
        connected=dict(type='bool', default=True),
        start_connected=dict(type='bool', default=True),
        wake_onlan=dict(type='bool', default=False),
        directpath_io=dict(type='bool', default=False),
        physical_function_backing=dict(type='str'),
        virtual_function_backing=dict(type='str'),
        allow_guest_os_mtu_change=dict(type='bool', default=True),
        force=dict(type='bool', default=False),
        gather_network_info=dict(type='bool', default=False, aliases=['gather_network_facts']),
        guest_control=dict(type='bool', default=True),
        state=dict(type='str', default='present', choices=['absent', 'present'])
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        mutually_exclusive=[
            ['vlan_id', 'network_name']
        ],
        required_one_of=[
            ['name', 'uuid', 'moid']
        ],
        supports_check_mode=True
    )

    pyv = PyVmomiHelper(module)

    if module.params['gather_network_info']:
        nics = pyv._get_nic_info()
        network_data = {}
        nics_sorted = sorted(nics.get('network_info'), key=lambda k: k['unit_number'])
        for n, i in enumerate(nics_sorted):
            key_name = '{0}'.format(n)
            network_data[key_name] = i
            network_data[key_name].update({'mac_addr': i['mac_address'], 'name': i['network_name']})

        module.exit_json(network_info=nics.get('network_info'), network_data=network_data, changed=False)

    if module.params['state'] == 'present':
        diff, changed, network_info = pyv._nic_present()

    if module.params['state'] == 'absent':
        if not module.params['mac_address']:
            module.fail_json(msg='parameter mac_address required when removing nics')
        diff, changed, network_info = pyv._nic_absent()

    module.exit_json(changed=changed, network_info=network_info, diff=diff)


if __name__ == '__main__':
    main()

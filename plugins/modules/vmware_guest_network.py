#!/usr/bin/python
#  Copyright: (c) 2020, Ansible Project
#  Copyright: (c) 2019, Diane Wang <dianew@vmware.com>
#  GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: vmware_guest_network
short_description: Manage network adapters of specified virtual machine in given vCenter infrastructure
description:
  - This module is used to add, reconfigure, remove network adapter of given virtual machine.
version_added: '1.0.0'
requirements:
  - "python >= 2.7"
  - "PyVmomi"
author:
  - Diane Wang (@Tomorrow9) <dianew@vmware.com>
notes:
  - Tested on vSphere 6.0, 6.5 and 6.7
  - For backwards compatibility network_data is returned when using the gather_network_info and networks parameters
options:
  name:
    description:
      - Name of virtual machine
      - Required if C(uuid) or C(moid) is not supplied.
    type: str
  uuid:
    description:
      - vm uuid
      - Required if C(name) or C(moid) is not supplied.
    type: str
  use_instance_uuid:
    description:
      - Whether to use the VMware instance UUID rather than the BIOS UUID.
    default: False
    type: bool
  moid:
    description:
      - Managed Object ID of the instance to manage if known, this is a unique identifier only within a single vCenter instance.
      - Required if C(uuid) or C(name) is not supplied.
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
      - Required when I(state=absent).
    type: str
  vlan_id:
    description:
      - VLAN id associated with the network.
    type: int
  network_name:
    description:
      - Name of network in vSphere.
    type: str
  device_type:
    default: vmxnet3
    description:
      - Type of virtual network device.
      - 'Valid choices are - C(e1000), C(e1000e), C(pcnet32), C(vmxnet2), C(vmxnet3) (default), C(sriov).'
    type: str
  label:
    description:
      - Alter the name of the network adapter.
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
    choices: [ 'present', 'absent' ]
    description:
      - NIC state.
      - When C(state=present), a nic will be added if a mac address or label does not previously exists or is unset.
      - When C(state=absent), the I(mac_address) parameter has to be set.
    type: str
  start_connected:
    default: True
    description:
      - If NIC should be connected to network on startup.
    type: bool
  wake_onlan:
    default: False
    description:
      - Enable wake on LAN.
    type: bool
  connected:
    default: True
    description:
      - If NIC should be connected to the network.
    type: bool
  directpath_io:
    default: False
    description:
      - Enable Universal Pass-through (UPT).
      - Only compatible with the C(vmxnet3) device type.
    type: bool
  force:
    default: false
    description:
      - Force adapter creation even if an existing adapter is attached to the same network.
    type: bool
  gather_network_info:
    aliases:
      - gather_network_facts
    default: False
    description:
      - Return information about current guest network adapters.
    type: bool
  networks:
    type: list
    elements: dict
    description:
      - This method will be deprecated, use loops in your playbook for multiple interfaces instead.
      - A list of network adapters.
      - C(mac) or C(label) or C(device_type) is required to reconfigure or remove an existing network adapter.
      - 'If there are multiple network adapters with the same C(device_type), you should set C(label) or C(mac) to match
         one of them, or will apply changes on all network adapters with the C(device_type) specified.'
      - 'C(mac), C(label), C(device_type) is the order of precedence from greatest to least if all set.'
    suboptions:
      mac:
        type: str
        description:
        - MAC address of the existing network adapter to be reconfigured or removed.
      label:
        type: str
        description:
        - Label of the existing network adapter to be reconfigured or removed, e.g., "Network adapter 1".
      device_type:
        type: str
        description:
        - 'Valid virtual network device types are C(e1000), C(e1000e), C(pcnet32), C(vmxnet2), C(vmxnet3) (default), C(sriov).'
        - Used to add new network adapter, reconfigure or remove the existing network adapter with this type.
        - If C(mac) and C(label) not specified or not find network adapter by C(mac) or C(label) will use this parameter.
      name:
        type: str
        description:
        - Name of the portgroup or distributed virtual portgroup for this interface.
        - When specifying distributed virtual portgroup make sure given C(esxi_hostname) or C(cluster) is associated with it.
      vlan:
        type: int
        description:
        - VLAN number for this interface.
      dvswitch_name:
        type: str
        description:
        - Name of the distributed vSwitch.
        - This value is required if multiple distributed portgroups exists with the same name.
      state:
        type: str
        description:
        - State of the network adapter.
        - If set to C(present), then will do reconfiguration for the specified network adapter.
        - If set to C(new), then will add the specified network adapter.
        - If set to C(absent), then will remove this network adapter.
      manual_mac:
        type: str
        description:
        - Manual specified MAC address of the network adapter when creating, or reconfiguring.
        - If not specified when creating new network adapter, mac address will be generated automatically.
        - When reconfigure MAC address, VM should be in powered off state.
      connected:
        type: bool
        description:
        - Indicates that virtual network adapter connects to the associated virtual machine.
      start_connected:
        type: bool
        description:
        - Indicates that virtual network adapter starts with associated virtual machine powers on.
      directpath_io:
        type: bool
        description:
        - If set, Universal Pass-Through (UPT or DirectPath I/O) will be enabled on the network adapter.
        - UPT is only compatible for Vmxnet3 adapter.
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
  returned: when using gather_network_info or networks parameters
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
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.community.vmware.plugins.module_utils.vmware import PyVmomi, vmware_argument_spec, wait_for_task


class PyVmomiHelper(PyVmomi):
    def __init__(self, module):
        super(PyVmomiHelper, self).__init__(module)
        self.change_detected = False
        self.nic_device_type = dict(
            pcnet32=vim.vm.device.VirtualPCNet32,
            vmxnet2=vim.vm.device.VirtualVmxnet2,
            vmxnet3=vim.vm.device.VirtualVmxnet3,
            e1000=vim.vm.device.VirtualE1000,
            e1000e=vim.vm.device.VirtualE1000e,
            sriov=vim.vm.device.VirtualSriovEthernetCard,
        )

    def _get_network_object(self, vm_obj, network_params=None):
        '''
        return network object matching given parameters
        :param vm_obj: vm object
        :param network_params: dict containing parameters from deprecated networks list method
        :return: network object
        :rtype: object
        '''
        if not self.params['esxi_hostname'] or not self.params['cluster']:
            compute_resource = vm_obj.runtime.host
        else:
            compute_resource = self._get_compute_resource_by_name()

        pg_lookup = {}
        if network_params:
            vlan_id = network_params['vlan_id']
            network_name = network_params['network_name']
            switch_name = network_params['switch']
        else:
            vlan_id = self.params['vlan_id']
            network_name = self.params['network_name']
            switch_name = self.params['switch']

        for pg in vm_obj.runtime.host.config.network.portgroup:
            pg_lookup[pg.spec.name] = {'switch': pg.spec.vswitchName, 'vlan_id': pg.spec.vlanId}

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

            for k in self.nic_device_type:
                if isinstance(nic, self.nic_device_type[k]):
                    d_item['device_type'] = k
                    break

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
        network = self._get_network_object(vm_obj, network_params)

        if network_params:
            connected = network_params['connected']
            device_type = network_params['device_type'].lower()
            directpath_io = network_params['directpath_io']
            guest_control = network_params['guest_control']
            label = network_params['label']
            mac_address = network_params['mac_address']
            start_connected = network_params['start_connected']
            wake_onlan = network_params['wake_onlan']
        else:
            connected = self.params['connected']
            device_type = self.params['device_type'].lower()
            directpath_io = self.params['directpath_io']
            guest_control = self.params['guest_control']
            label = self.params['label']
            mac_address = self.params['mac_address']
            start_connected = self.params['start_connected']
            wake_onlan = self.params['wake_onlan']

        if not nic_obj:
            device_obj = self.nic_device_type[device_type]
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

    def _deprectated_list_config(self):
        '''
        this only exists to handle the old way of configuring interfaces, which
        should be deprectated in favour of using loops in the playbook instead of
        feeding lists directly into the module.
        '''
        diff = {'before': {}, 'after': {}}
        changed = False
        for i in self.params['networks']:
            network_params = {}
            network_params['mac_address'] = i.get('mac') or i.get('manual_mac')
            network_params['network_name'] = i.get('name')
            network_params['vlan_id'] = i.get('vlan')
            network_params['switch'] = i.get('dvswitch_name')
            network_params['guest_control'] = i.get('allow_guest_control', self.params['guest_control'])

            for k in ['connected', 'device_type', 'directpath_io', 'force', 'label', 'start_connected', 'state', 'wake_onlan']:
                network_params[k] = i.get(k, self.params[k])

            if network_params['state'] in ['new', 'present']:
                n_diff, n_changed, network_info = self._nic_present(network_params)
                diff['before'].update(n_diff['before'])
                diff['after'] = n_diff['after']
                if n_changed:
                    changed = True

            if network_params['state'] == 'absent':
                n_diff, n_changed, network_info = self._nic_absent(network_params)
                diff['before'].update(n_diff['before'])
                diff['after'] = n_diff['after']
                if n_changed:
                    changed = True

        return diff, changed, network_info

    def _nic_present(self, network_params=None):
        changed = False
        diff = {'before': {}, 'after': {}}
        # backwards compatibility, clean up when params['networks']
        # has been removed
        if network_params:
            force = network_params['force']
            label = network_params['label']
            mac_address = network_params['mac_address']
            network_name = network_params['network_name']
            switch = network_params['switch']
            vlan_id = network_params['vlan_id']
        else:
            force = self.params['force']
            label = self.params['label']
            mac_address = self.params['mac_address']
            network_name = self.params['network_name']
            switch = self.params['switch']
            vlan_id = self.params['vlan_id']

        vm_obj = self.get_vm()
        if not vm_obj:
            self.module.fail_json(msg='could not find vm: {0}'.format(self.params['name']))

        network_obj = self._get_network_object(vm_obj, network_params)
        nic_info, nic_obj_lst = self._get_nics_from_vm(vm_obj)
        label_lst = [d.get('label') for d in nic_info]
        mac_addr_lst = [d.get('mac_address') for d in nic_info]
        vlan_id_lst = [d.get('vlan_id') for d in nic_info]
        network_name_lst = [d.get('network_name') for d in nic_info]

        # TODO: make checks below less inelegant
        if ((vlan_id in vlan_id_lst or network_name in network_name_lst)
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
                    device_spec = self._new_nic_spec(vm_obj, nic_obj, network_params)

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
            device_spec = self._new_nic_spec(vm_obj, None, network_params)
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
                            'vlan_id': self._get_vlanid_from_network(network_obj),
                            'network_name': network_obj.name,
                            'label': label,
                            'mac_address': nic_mac,
                            'unit_number': 40000
                        }
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
        label=dict(type='str'),
        switch=dict(type='str'),
        connected=dict(type='bool', default=True),
        start_connected=dict(type='bool', default=True),
        wake_onlan=dict(type='bool', default=False),
        directpath_io=dict(type='bool', default=False),
        force=dict(type='bool', default=False),
        gather_network_info=dict(type='bool', default=False, aliases=['gather_network_facts']),
        networks=dict(type='list', default=[], elements='dict'),
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

    if module.params['networks']:
        network_data = {}
        module.deprecate(
            msg='The old way of configuring interfaces by supplying an arbitrary list will be removed, loops should be used to handle multiple interfaces',
            version='2.0.0',
            collection_name='community.vmware'
        )
        diff, changed, network_info = pyv._deprectated_list_config()
        nd = copy.deepcopy(network_info)
        nics_sorted = sorted(nd, key=lambda k: k['unit_number'])
        for n, i in enumerate(nics_sorted):
            key_name = '{0}'.format(n)
            network_data[key_name] = i
            network_data[key_name].update({'mac_addr': i['mac_address'], 'name': i['network_name']})

        module.exit_json(changed=changed, network_info=network_info, network_data=network_data, diff=diff)

    if module.params['state'] == 'present':
        diff, changed, network_info = pyv._nic_present()

    if module.params['state'] == 'absent':
        if not module.params['mac_address']:
            module.fail_json(msg='parameter mac_address required when removing nics')
        diff, changed, network_info = pyv._nic_absent()

    module.exit_json(changed=changed, network_info=network_info, diff=diff)


if __name__ == '__main__':
    main()

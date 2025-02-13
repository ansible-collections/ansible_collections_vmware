#!/usr/bin/python
# -*- coding: utf-8 -*-

# This module is also sponsored by E.T.A.I. (www.etai.fr)
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: guest
short_description: Manages virtual machines in vCenter
description: >
   This module can be used to create and delete new virtual machines,
   and to manage some very basic configuration.
author:
- Loic Blot (@nerzhul) <loic.blot@unix-experience.fr>
- Philippe Dellaert (@pdellaert) <philippe@dellaert.org>
- Abhijeet Kasurde (@Akasurde) <akasurde@redhat.com>
- Mario Lenz (@mariolenz) <m@riolenz.de>
notes:
    - Please make sure that the user used for M(community.vmware.guest) has the correct level of privileges.
    - For example, following is the list of minimum privileges required by users to create virtual machines.
    - "   DataStore > Allocate Space"
    - "   Virtual Machine > Configuration > Add New Disk"
    - "   Virtual Machine > Configuration > Add or Remove Device"
    - "   Virtual Machine > Inventory > Create New"
    - "   Network > Assign Network"
    - "   Resource > Assign Virtual Machine to Resource Pool"
    - "Module may require additional privileges as well, which may be required for gathering facts - e.g. ESXi configurations."
    - In order to change the VM's parameters (e.g. number of CPUs), the VM must be powered off unless the hot-add
      support is enabled and the O(state=present) must be used to apply the changes.
options:
  state:
    description:
    - If V(present) and virtual machine does not exists, virtual machine is deployed with the given parameters.
    - If V(present) and virtual machine exists, ensure the virtual machine configurations conforms to task arguments.
    - If V(absent) and virtual machine exists, then the specified virtual machine is removed with it's associated components.
    default: present
    type: str
    choices: [ absent, present ]
  name:
    description:
    - Name of the virtual machine to work with.
    - Virtual machine names in vCenter are not necessarily unique, which may be problematic.
    - If multiple virtual machines with same name exists, then O(folder) is required parameter to
      identify uniqueness of the virtual machine.
    type: str
    required: true
  folder:
    description:
    - Destination folder, absolute path to find an existing guest or create the new guest.
    - "The folder should include the datacenter. ESXi's datacenter is ha-datacenter."
    - 'If multiple machines are found with same name, this parameter is used to identify'
    - 'uniqueness of the virtual machine.'
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
  hardware:
    type: dict
    default: {}
    description:
    - "Manage virtual machine's hardware attributes."
    suboptions:
        hotadd_cpu:
            type: bool
            description: Allow virtual CPUs to be added while the virtual machine is running.
        hotadd_memory:
            type: bool
            description: Allow memory to be added while the virtual machine is running.
        memory_mb:
            type: int
            description: Amount of memory in MB.
        num_cpus:
            type: int
            description:
            - Number of CPUs.
            - Must be a multiple of O(hardware.num_cpu_cores_per_socket).
            - For example, to create a VM with 2 sockets of 4 cores, specify O(hardware.num_cpus) as 8 and O(hardware.num_cpu_cores_per_socket) as 4.
        num_cpu_cores_per_socket:
            type: int
            description: Number of Cores Per Socket.
        cpu_shares_level:
            type: str
            choices: [ 'low', 'normal', 'high', 'custom' ]
            description:
            - The allocation level of CPU resources for the virtual machine.
        cpu_shares:
            type: int
            description:
            - The number of shares of CPU allocated to this virtual machine
            - cpu_shares_level will automatically be set to 'custom'
        vpmc_enabled:
            type: bool
            description: Enable virtual CPU Performance Counters.
        secure_boot:
            type: bool
            description: Whether to enable or disable (U)EFI secure boot.
        memory_reservation_lock:
            type: bool
            description:
            - If set V(true), memory resource reservation for the virtual machine.
        max_connections:
            type: int
            description:
            - Maximum number of active remote display connections for the virtual machines.
        mem_limit:
            type: int
            description:
            - The memory utilization of a virtual machine will not exceed this limit.
            - Unit is MB.
        mem_reservation:
            type: int
            description: The amount of memory resource that is guaranteed available to the virtual machine.
            aliases: [ 'memory_reservation' ]
        mem_shares_level:
            type: str
            description:
            - The allocation level of memory resources for the virtual machine.
            choices: [ 'low', 'normal', 'high', 'custom' ]
        mem_shares:
            type: int
            description:
            - The number of shares of memory allocated to this virtual machine
            - mem_shares_level will automatically be set to 'custom'
        cpu_limit:
            type: int
            description:
            - The CPU utilization of a virtual machine will not exceed this limit.
            - Unit is MHz.
        cpu_reservation:
            type: int
            description: The amount of CPU resource that is guaranteed available to the virtual machine.
        version:
            type: str
            description:
            - The Virtual machine hardware versions.
            - Default is 10 (ESXi 5.5 and onwards).
            - If set to V(latest), the specified virtual machine will be upgraded to the most current hardware version supported on the host.
            - Please check VMware documentation for correct virtual machine hardware version.
            - Incorrect hardware version may lead to failure in deployment. If hardware version is already equal to the given.
        boot_firmware:
            type: str
            description: Choose which firmware should be used to boot the virtual machine.
            choices: [ 'bios', 'efi' ]
        nested_virt:
            type: bool
            description:
            - Enable nested virtualization.
        virt_based_security:
            type: bool
            description:
            - Enable Virtualization Based Security feature for Windows on ESXi 6.7 and later, from hardware version 14.
            - Supported Guest OS are Windows 10 64 bit, Windows Server 2016, Windows Server 2019 and later.
            - The firmware of virtual machine must be EFI and secure boot must be enabled.
            - Virtualization Based Security depends on nested virtualization and Intel Virtualization Technology for Directed I/O.
            - Deploy on unsupported ESXi, hardware version or firmware may lead to failure or deployed VM with unexpected configurations.
        iommu:
            type: bool
            description: Flag to specify if I/O MMU is enabled for this virtual machine.
  encryption:
    type: dict
    default: {}
    description:
    - Manage virtual machine encryption settings
    suboptions:
        encrypted_vmotion:
            type: str
            description: Controls encryption for live migrations with vmotion
            choices: ['disabled', 'opportunistic', 'required']
        encrypted_ft:
            type: str
            description: Controls encryption for fault tolerance replication
            choices: ['disabled', 'opportunistic', 'required']
  guest_id:
    type: str
    description:
    - Set the guest ID.
    - >
         Valid values are referenced here:
         U(https://code.vmware.com/apis/358/doc/vim.vm.GuestOsDescriptor.GuestOsIdentifier.html)
  resource_pool:
    description:
    - Use the given resource pool for virtual machine operation.
    - Resource pool should be child of the selected host parent.
    - When not specified I(Resources) is taken as default value.
    type: str
  force:
    description:
    - Ignore warnings and complete the actions.
    - This parameter is useful while removing virtual machine which is powered on state.
    - 'This module reflects the VMware vCenter API and UI workflow, as such, in some cases the `force` flag will
       be mandatory to perform the action to ensure you are certain the action has to be taken, no matter what the consequence.
       This is specifically the case for removing a powered on the virtual machine when O(state=absent).'
    default: false
    type: bool
  delete_from_inventory:
    description:
    - Whether to delete Virtual machine from inventory or delete from disk.
    default: false
    type: bool
  datacenter:
    description:
    - Destination datacenter for the deploy operation.
    default: ha-datacenter
    type: str
  cluster:
    description:
    - The cluster name where the virtual machine will run.
    - This is a required parameter, if O(esxi_hostname) is not set.
    - O(esxi_hostname) and O(cluster) are mutually exclusive parameters.
    type: str
  esxi_hostname:
    description:
    - The ESXi hostname where the virtual machine will run.
    - This is a required parameter, if O(cluster) is not set.
    - O(esxi_hostname) and O(cluster) are mutually exclusive parameters.
    type: str
  datastore:
    description:
    - Specify datastore or datastore cluster to provision virtual machine.
    type: str
extends_documentation_fragment:
- community.vmware.vmware.documentation

'''

EXAMPLES = r'''
- name: Create a virtual machine on given ESXi hostname
  community.vmware.guest:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    folder: /DC1/vm/
    name: test_vm_0001
    state: poweredon
    guest_id: centos64Guest
    # This is hostname of particular ESXi server on which user wants VM to be deployed
    esxi_hostname: "{{ esxi_hostname }}"
    hardware:
      memory_mb: 512
      num_cpus: 4
      scsi: paravirtual
  delegate_to: localhost
  register: deploy_vm

- name: Remove a virtual machine from inventory
  community.vmware.guest:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    name: vm_name
    delete_from_inventory: true
    state: absent
  delegate_to: localhost
'''

RETURN = r'''
instance:
    description: metadata about the new virtual machine
    returned: always
    type: dict
    sample: None
'''

import time

HAS_PYVMOMI = False
try:
    from pyVmomi import vim, vmodl
    HAS_PYVMOMI = True
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_text, to_native
from ansible_collections.community.vmware.plugins.module_utils.vmware import (
    find_obj,
    gather_vm_facts,
    get_all_objs,
    compile_folder_path_for_object,
    serialize_spec,
    vmware_argument_spec,
    set_vm_power_state,
    PyVmomi,
    wait_for_vm_ip,
)
from ansible_collections.community.vmware.plugins.module_utils.vm_device_helper import PyVmomiDeviceHelper


class PyVmomiCache(object):
    """ This class caches references to objects which are requested multiples times but not modified """

    def __init__(self, content, dc_name=None):
        self.content = content
        self.dc_name = dc_name
        self.clusters = {}
        self.esx_hosts = {}
        self.parent_datacenters = {}

    def find_obj(self, content, types, name, confine_to_datacenter=True):
        """ Wrapper around find_obj to set datacenter context """
        result = find_obj(content, types, name)
        if result and confine_to_datacenter:
            if to_text(self.get_parent_datacenter(result).name) != to_text(self.dc_name):
                result = None
                objects = self.get_all_objs(content, types, confine_to_datacenter=True)
                for obj in objects:
                    if name is None or to_text(obj.name) == to_text(name):
                        return obj
        return result

    def get_all_objs(self, content, types, confine_to_datacenter=True):
        """ Wrapper around get_all_objs to set datacenter context """
        objects = get_all_objs(content, types)
        if confine_to_datacenter:
            if hasattr(objects, 'items'):
                # resource pools come back as a dictionary
                # make a copy
                for k, v in tuple(objects.items()):
                    parent_dc = self.get_parent_datacenter(k)
                    if parent_dc.name != self.dc_name:
                        del objects[k]
            else:
                # everything else should be a list
                objects = [x for x in objects if self.get_parent_datacenter(x).name == self.dc_name]

        return objects

    def get_cluster(self, cluster):
        if cluster not in self.clusters:
            self.clusters[cluster] = self.find_obj(self.content, [vim.ClusterComputeResource], cluster)

        return self.clusters[cluster]

    def get_esx_host(self, host):
        if host not in self.esx_hosts:
            self.esx_hosts[host] = self.find_obj(self.content, [vim.HostSystem], host)

        return self.esx_hosts[host]

    def get_parent_datacenter(self, obj):
        """ Walk the parent tree to find the objects datacenter """
        if isinstance(obj, vim.Datacenter):
            return obj
        if obj in self.parent_datacenters:
            return self.parent_datacenters[obj]
        datacenter = None
        while True:
            if not hasattr(obj, 'parent'):
                break
            obj = obj.parent
            if isinstance(obj, vim.Datacenter):
                datacenter = obj
                break
        self.parent_datacenters[obj] = datacenter
        return datacenter


class PyVmomiHelper(PyVmomi):
    def __init__(self, module):
        super(PyVmomiHelper, self).__init__(module)
        self.device_helper = PyVmomiDeviceHelper(self.module)
        self.configspec = None
        self.relospec = None
        self.change_detected = False  # a change was detected and needs to be applied through reconfiguration
        self.change_applied = False   # a change was applied meaning at least one task succeeded
        self.tracked_changes = {}     # dict of changes made or would-be-made in check mode, updated when change_applied is set
        self.customspec = None
        self.cache = PyVmomiCache(self.content, dc_name=self.params['datacenter'])

    def gather_facts(self, vm):
        return gather_vm_facts(self.content, vm)

    def remove_vm(self, vm, delete_from_inventory=False):
        # https://www.vmware.com/support/developer/converter-sdk/conv60_apireference/vim.ManagedEntity.html#destroy
        if vm.summary.runtime.powerState.lower() == 'poweredon':
            self.module.fail_json(msg="Virtual machine %s found in 'powered on' state, "
                                      "please use 'force' parameter to remove or poweroff VM "
                                      "and try removing VM again." % vm.name)
        # Delete VM from Inventory
        if delete_from_inventory:
            try:
                vm.UnregisterVM()
            except (vim.fault.TaskInProgress,
                    vmodl.RuntimeFault) as e:
                return {'changed': self.change_applied, 'failed': True, 'msg': e.msg, 'op': 'UnregisterVM'}
            self.change_applied = True
            return {'changed': self.change_applied, 'failed': False}
        # Delete VM from Disk
        task = vm.Destroy()
        self.wait_for_task(task)
        if task.info.state == 'error':
            return {'changed': self.change_applied, 'failed': True, 'msg': task.info.error.msg, 'op': 'destroy'}
        else:
            return {'changed': self.change_applied, 'failed': False}

    def configure_guestid(self, vm_obj, vm_creation=False):
        if vm_creation and self.params['guest_id'] is None:
            self.module.fail_json(msg="guest_id attribute is mandatory for VM creation")

        if self.params['guest_id'] and \
                (vm_obj is None or self.params['guest_id'].lower() != vm_obj.summary.config.guestId.lower()):
            self.change_detected = True
            self.configspec.guestId = self.params['guest_id']

    def configure_resource_alloc_info(self, vm_obj):
        """
        Function to configure resource allocation information about virtual machine
        :param vm_obj: VM object in case of reconfigure, None in case of deploy
        :return: None
        """
        rai_change_detected = False
        memory_allocation = vim.ResourceAllocationInfo()
        cpu_allocation = vim.ResourceAllocationInfo()

        memory_shares_info = vim.SharesInfo()
        cpu_shares_info = vim.SharesInfo()

        mem_shares_level = self.params['hardware']['mem_shares_level']
        if mem_shares_level is not None:
            memory_shares_info.level = mem_shares_level
            memory_allocation.shares = memory_shares_info

            if vm_obj is None or \
                    memory_allocation.shares.level != vm_obj.config.memoryAllocation.shares.level:
                rai_change_detected = True

        cpu_shares_level = self.params['hardware']['cpu_shares_level']
        if cpu_shares_level is not None:
            cpu_shares_info.level = cpu_shares_level
            cpu_allocation.shares = cpu_shares_info
            if vm_obj is None or \
                    cpu_allocation.shares.level != vm_obj.config.cpuAllocation.shares.level:
                rai_change_detected = True

        mem_shares = self.params['hardware']['mem_shares']
        if mem_shares is not None:
            memory_shares_info.level = 'custom'
            memory_shares_info.shares = mem_shares
            memory_allocation.shares = memory_shares_info
            if vm_obj is None or \
                    memory_allocation.shares != vm_obj.config.memoryAllocation.shares:
                rai_change_detected = True

        cpu_shares = self.params['hardware']['cpu_shares']
        if cpu_shares is not None:
            cpu_shares_info.level = 'custom'
            cpu_shares_info.shares = cpu_shares
            cpu_allocation.shares = cpu_shares_info
            if vm_obj is None or \
                    cpu_allocation.shares != vm_obj.config.cpuAllocation.shares:
                rai_change_detected = True

        mem_limit = self.params['hardware']['mem_limit']
        if mem_limit is not None:
            memory_allocation.limit = mem_limit
            if vm_obj is None or \
                    memory_allocation.limit != vm_obj.config.memoryAllocation.limit:
                rai_change_detected = True

        mem_reservation = self.params['hardware']['mem_reservation']
        if mem_reservation is not None:
            memory_allocation.reservation = mem_reservation
            if vm_obj is None or \
                    memory_allocation.reservation != vm_obj.config.memoryAllocation.reservation:
                rai_change_detected = True

        cpu_limit = self.params['hardware']['cpu_limit']
        if cpu_limit is not None:
            cpu_allocation.limit = cpu_limit
            if vm_obj is None or \
                    cpu_allocation.limit != vm_obj.config.cpuAllocation.limit:
                rai_change_detected = True

        cpu_reservation = self.params['hardware']['cpu_reservation']
        if cpu_reservation is not None:
            cpu_allocation.reservation = cpu_reservation
            if vm_obj is None or \
                    cpu_allocation.reservation != vm_obj.config.cpuAllocation.reservation:
                rai_change_detected = True

        if rai_change_detected:
            self.configspec.memoryAllocation = memory_allocation
            self.configspec.cpuAllocation = cpu_allocation
            self.change_detected = True

    def configure_cpu_and_memory(self, vm_obj, vm_creation=False):
        # set cpu/memory/etc
        num_cpus = self.params['hardware']['num_cpus']
        if num_cpus is not None:
            # check VM power state and cpu hot-add/hot-remove state before re-config VM
            # Allow VM to be powered on during this check when in check mode, when no changes will actually be made
            if vm_obj and vm_obj.runtime.powerState == vim.VirtualMachinePowerState.poweredOn and not self.module.check_mode:
                if not vm_obj.config.cpuHotRemoveEnabled and num_cpus < vm_obj.config.hardware.numCPU:
                    self.module.fail_json(msg="Configured cpu number is less than the cpu number of the VM, "
                                              "cpuHotRemove is not enabled")
                if not vm_obj.config.cpuHotAddEnabled and num_cpus > vm_obj.config.hardware.numCPU:
                    self.module.fail_json(msg="Configured cpu number is more than the cpu number of the VM, "
                                              "cpuHotAdd is not enabled")

            num_cpu_cores_per_socket = self.params['hardware']['num_cpu_cores_per_socket']
            if num_cpu_cores_per_socket is not None:
                if num_cpus % num_cpu_cores_per_socket != 0:
                    self.module.fail_json(msg="hardware.num_cpus attribute should be a multiple "
                                              "of hardware.num_cpu_cores_per_socket")
                if vm_obj is None or num_cpu_cores_per_socket != vm_obj.config.hardware.numCoresPerSocket:
                    self.change_detected = True
                    self.configspec.numCoresPerSocket = num_cpu_cores_per_socket
            if vm_obj is None or num_cpus != vm_obj.config.hardware.numCPU:
                self.change_detected = True
                self.configspec.numCPUs = num_cpus
        # num_cpu is mandatory for VM creation
        elif vm_creation:
            self.module.fail_json(msg="hardware.num_cpus attribute is mandatory for VM creation")

        memory_mb = self.params['hardware']['memory_mb']
        if memory_mb is not None:
            # check VM power state and memory hotadd state before re-config VM
            if vm_obj and vm_obj.runtime.powerState == vim.VirtualMachinePowerState.poweredOn:
                if vm_obj.config.memoryHotAddEnabled and memory_mb < vm_obj.config.hardware.memoryMB:
                    self.module.fail_json(msg="Configured memory is less than memory size of the VM, "
                                              "operation is not supported")
                # Allow VM to be powered on during this check when in check mode, when no changes will actually be made
                elif not vm_obj.config.memoryHotAddEnabled and memory_mb != vm_obj.config.hardware.memoryMB and not self.module.check_mode:
                    self.module.fail_json(msg="memoryHotAdd is not enabled")
            if vm_obj is None or memory_mb != vm_obj.config.hardware.memoryMB:
                self.change_detected = True
                self.configspec.memoryMB = memory_mb
        # memory_mb is mandatory for VM creation
        elif vm_creation:
            self.module.fail_json(msg="hardware.memory_mb attribute is mandatory for VM creation")

        hotadd_memory = self.params['hardware']['hotadd_memory']
        if hotadd_memory is not None:
            # Allow VM to be powered on during this check when in check mode, when no changes will actually be made
            if vm_obj and vm_obj.runtime.powerState == vim.VirtualMachinePowerState.poweredOn and \
                    vm_obj.config.memoryHotAddEnabled != hotadd_memory and not self.module.check_mode:
                self.module.fail_json(msg="Configure hotadd memory operation is not supported when VM is power on")
            if vm_obj is None or hotadd_memory != vm_obj.config.memoryHotAddEnabled:
                self.change_detected = True
                self.configspec.memoryHotAddEnabled = hotadd_memory

        hotadd_cpu = self.params['hardware']['hotadd_cpu']
        if hotadd_cpu is not None:
            # Allow VM to be powered on during this check when in check mode, when no changes will actually be made
            if vm_obj and vm_obj.runtime.powerState == vim.VirtualMachinePowerState.poweredOn and \
                    vm_obj.config.cpuHotAddEnabled != hotadd_cpu and not self.module.check_mode:
                self.module.fail_json(msg="Configure hotadd cpu operation is not supported when VM is power on")
            if vm_obj is None or hotadd_cpu != vm_obj.config.cpuHotAddEnabled:
                self.change_detected = True
                self.configspec.cpuHotAddEnabled = hotadd_cpu

        memory_reservation_lock = self.params['hardware']['memory_reservation_lock']
        if memory_reservation_lock is not None:
            if vm_obj is None or memory_reservation_lock != vm_obj.config.memoryReservationLockedToMax:
                self.change_detected = True
                self.configspec.memoryReservationLockedToMax = memory_reservation_lock

        vpmc_enabled = self.params['hardware']['vpmc_enabled']
        if vpmc_enabled is not None:
            # Allow VM to be powered on during this check when in check mode, when no changes will actually be made
            if vm_obj and vm_obj.runtime.powerState == vim.VirtualMachinePowerState.poweredOn and \
                    vm_obj.config.vPMCEnabled != vpmc_enabled and not self.module.check_mode:
                self.module.fail_json(msg="Configure vPMC cpu operation is not supported when VM is power on")
            if vm_obj is None or vpmc_enabled != vm_obj.config.vPMCEnabled:
                self.change_detected = True
                self.configspec.vPMCEnabled = vpmc_enabled

        boot_firmware = self.params['hardware']['boot_firmware']
        if boot_firmware is not None:
            # boot firmware re-config can cause boot issue
            if vm_obj is not None:
                return
            self.configspec.firmware = boot_firmware
            self.change_detected = True

    def configure_hardware_params(self, vm_obj):
        """
        Function to configure hardware related configuration of virtual machine
        Args:
            vm_obj: virtual machine object
        """
        max_connections = self.params['hardware']['max_connections']
        if max_connections is not None:
            if vm_obj is None or max_connections != vm_obj.config.maxMksConnections:
                self.change_detected = True
                self.configspec.maxMksConnections = max_connections

        nested_virt = self.params['hardware']['nested_virt']
        if nested_virt is not None:
            if vm_obj is None or nested_virt != bool(vm_obj.config.nestedHVEnabled):
                self.change_detected = True
                self.configspec.nestedHVEnabled = nested_virt

        temp_version = self.params['hardware']['version']
        if temp_version is not None:
            new_version = None
            if temp_version.lower() == 'latest':
                # Check is to make sure vm_obj is not of type template
                if vm_obj and not vm_obj.config.template:
                    config_option_descriptors = vm_obj.environmentBrowser.QueryConfigOptionDescriptor()
                    available_hw_versions = [int(option_desc.key.split("-")[1]) for option_desc in config_option_descriptors if option_desc.upgradeSupported]
                    temp_version = max(available_hw_versions)
            else:
                try:
                    temp_version = int(temp_version)
                except ValueError:
                    self.module.fail_json(msg="Failed to set hardware.version '%s' value as valid"
                                          " values are either 'latest' or a number."
                                          " Please check VMware documentation for valid VM hardware versions." % temp_version)

            if isinstance(temp_version, int):
                # Hardware version is denoted as "vmx-10"
                new_version = "vmx-%02d" % temp_version

            if vm_obj is None:
                self.change_detected = True
                self.configspec.version = new_version
            # Check is to make sure vm_obj is not of type template
            elif not vm_obj.config.template:
                # VM exists and we need to update the hardware version
                current_version = vm_obj.config.version
                # Hardware version is denoted as "vmx-10"
                version_digit = int(current_version.split("-", 1)[-1])
                if temp_version < version_digit:
                    self.module.fail_json(msg="Current hardware version '%d' which is greater than the specified"
                                          " version '%d'. Downgrading hardware version is"
                                          " not supported. Please specify version greater"
                                          " than the current version." % (version_digit,
                                                                          temp_version))
                elif temp_version > version_digit:
                    self.change_detected = True
                    self.tracked_changes['hardware.version'] = temp_version
                    self.configspec.version = new_version
                    # Only perform the upgrade if not in check mode.
                    if not self.module.check_mode:
                        task = vm_obj.UpgradeVM_Task(new_version)
                        self.wait_for_task(task)
                        if task.info.state == 'error':
                            return {'changed': self.change_applied, 'failed': True, 'msg': task.info.error.msg, 'op': 'upgrade'}
                        self.change_applied = True

        secure_boot = self.params['hardware']['secure_boot']
        if secure_boot is not None:
            if vm_obj is None or secure_boot != vm_obj.config.bootOptions.efiSecureBootEnabled:
                self.change_detected = True
                self.configspec.bootOptions = vim.vm.BootOptions()
                self.configspec.bootOptions.efiSecureBootEnabled = secure_boot

        iommu = self.params['hardware']['iommu']
        if iommu is not None:
            if vm_obj is None or iommu != vm_obj.config.flags.vvtdEnabled:
                self.change_detected = True
                if self.configspec.flags is None:
                    self.configspec.flags = vim.vm.FlagInfo()
                self.configspec.flags.vvtdEnabled = iommu

        virt_based_security = self.params['hardware']['virt_based_security']
        if virt_based_security is not None:
            if vm_obj is None or virt_based_security != vm_obj.config.flags.vbsEnabled:
                self.change_detected = True
                if self.configspec.flags is None:
                    self.configspec.flags = vim.vm.FlagInfo()
                self.configspec.flags.vbsEnabled = virt_based_security

    def configure_encryption_params(self, vm_obj):

        encrypted_vmotion = self.params['encryption']['encrypted_vmotion']
        if encrypted_vmotion is not None:
            if vm_obj is None or encrypted_vmotion != vm_obj.config.migrateEncryption:
                self.change_detected = True
                self.configspec.migrateEncryption = encrypted_vmotion

        encrypted_ft = self.params['encryption']['encrypted_ft']
        if encrypted_ft is not None:
            if encrypted_ft == "disabled":
                encrypted_ft_cfg = "ftEncryptionDisabled"
            elif encrypted_ft == "opportunistic":
                encrypted_ft_cfg = "ftEncryptionOpportunistic"
            elif encrypted_ft == "required":
                encrypted_ft_cfg = "ftEncryptionRequired"
            if vm_obj is None or encrypted_ft_cfg != vm_obj.config.ftEncryptionMode:
                self.change_detected = True
                self.configspec.ftEncryptionMode = encrypted_ft_cfg

    def select_host(self):
        hostsystem = self.cache.get_esx_host(self.params['esxi_hostname'])
        if not hostsystem:
            self.module.fail_json(msg='Failed to find ESX host "%(esxi_hostname)s"' % self.params)
        if hostsystem.runtime.connectionState != 'connected' or hostsystem.runtime.inMaintenanceMode:
            self.module.fail_json(msg='ESXi "%(esxi_hostname)s" is in invalid state or in maintenance mode.' % self.params)
        return hostsystem

    def select_datastore(self, vm_obj=None):
        datastore = None
        datastore_name = None

        datastores = []

        if self.params['cluster']:
            cluster = self.find_cluster_by_name(self.params['cluster'], self.content)

            for host in cluster.host:
                for mi in host.configManager.storageSystem.fileSystemVolumeInfo.mountInfo:
                    if mi.volume.type == "VMFS" or mi.volume.type == "NFS":
                        datastores.append(self.cache.find_obj(self.content, [vim.Datastore], mi.volume.name))
        elif self.params['esxi_hostname']:
            host = self.find_hostsystem_by_name(self.params['esxi_hostname'])

            for mi in host.configManager.storageSystem.fileSystemVolumeInfo.mountInfo:
                if mi.volume.type == "VMFS" or mi.volume.type == "NFS":
                    datastores.append(self.cache.find_obj(self.content, [vim.Datastore], mi.volume.name))
        else:
            datastores = self.cache.get_all_objs(self.content, [vim.Datastore])
            datastores = [x for x in datastores if self.cache.get_parent_datacenter(x).name == self.params['datacenter']]

        datastore_freespace = 0
        for ds in datastores:
            if not self.is_datastore_valid(datastore_obj=ds):
                continue

            if (ds.summary.freeSpace > datastore_freespace) or (ds.summary.freeSpace == datastore_freespace and not datastore):
                datastore = ds
                datastore_name = datastore.name
                datastore_freespace = ds.summary.freeSpace

        if not datastore:
            self.module.fail_json(msg="Failed to find a matching datastore")

        return datastore, datastore_name

    def obj_has_parent(self, obj, parent):
        if obj is None and parent is None:
            raise AssertionError()
        current_parent = obj

        while True:
            if current_parent.name == parent.name:
                return True

            # Check if we have reached till root folder
            moid = current_parent._moId
            if moid in ['group-d1', 'ha-folder-root']:
                return False

            current_parent = current_parent.parent
            if current_parent is None:
                return False

    def find_folder(self, searchpath):
        """ Walk inventory objects one position of the searchpath at a time """

        # split the searchpath so we can iterate through it
        paths = [x.replace('/', '') for x in searchpath.split('/')]
        paths_total = len(paths) - 1
        position = 0

        # recursive walk while looking for next element in searchpath
        root = self.content.rootFolder
        while root and position <= paths_total:
            change = False
            if hasattr(root, 'childEntity'):
                for child in root.childEntity:
                    if child.name == paths[position]:
                        root = child
                        position += 1
                        change = True
                        break
            elif isinstance(root, vim.Datacenter):
                if hasattr(root, 'vmFolder'):
                    if root.vmFolder.name == paths[position]:
                        root = root.vmFolder
                        position += 1
                        change = True
            else:
                root = None

            if not change:
                root = None

        return root

    def get_resource_pool(self, cluster=None, host=None, resource_pool=None):
        """ Get a resource pool, filter on cluster, esxi_hostname or resource_pool if given """

        cluster_name = cluster or self.params.get('cluster', None)
        host_name = host or self.params.get('esxi_hostname', None)
        resource_pool_name = resource_pool or self.params.get('resource_pool', None)

        # get the datacenter object
        datacenter = find_obj(self.content, [vim.Datacenter], self.params['datacenter'])
        if not datacenter:
            self.module.fail_json(msg='Unable to find datacenter "%s"' % self.params['datacenter'])

        # if cluster is given, get the cluster object
        if cluster_name:
            cluster = find_obj(self.content, [vim.ComputeResource], cluster_name, folder=datacenter)
            if not cluster:
                self.module.fail_json(msg='Unable to find cluster "%s"' % cluster_name)
        # if host is given, get the cluster object using the host
        elif host_name:
            host = find_obj(self.content, [vim.HostSystem], host_name, folder=datacenter)
            if not host:
                self.module.fail_json(msg='Unable to find host "%s"' % host_name)
            cluster = host.parent
        else:
            cluster = None

        # get resource pools limiting search to cluster or datacenter
        resource_pool = find_obj(self.content, [vim.ResourcePool], resource_pool_name, folder=cluster or datacenter)
        if not resource_pool:
            if resource_pool_name:
                self.module.fail_json(msg='Unable to find resource_pool "%s"' % resource_pool_name)
            else:
                self.module.fail_json(msg='Unable to find resource pool, need esxi_hostname, resource_pool, or cluster')
        return resource_pool

    def deploy_vm(self):
        # https://github.com/vmware/pyvmomi-community-samples/blob/master/samples/clone_vm.py
        # https://www.vmware.com/support/developer/vc-sdk/visdk25pubs/ReferenceGuide/vim.vm.CloneSpec.html
        # https://www.vmware.com/support/developer/vc-sdk/visdk25pubs/ReferenceGuide/vim.vm.ConfigSpec.html
        # https://www.vmware.com/support/developer/vc-sdk/visdk41pubs/ApiReference/vim.vm.RelocateSpec.html

        # FIXME:
        #   - static IPs

        self.folder = self.params.get('folder', None)
        if self.folder is None:
            self.module.fail_json(msg="Folder is required parameter while deploying new virtual machine")

        # Prepend / if it was missing from the folder path, also strip trailing slashes
        if not self.folder.startswith('/'):
            self.folder = '/%(folder)s' % self.params
        self.folder = self.folder.rstrip('/')

        datacenter = self.cache.find_obj(self.content, [vim.Datacenter], self.params['datacenter'])
        if datacenter is None:
            self.module.fail_json(msg='No datacenter named %(datacenter)s was found' % self.params)

        dcpath = compile_folder_path_for_object(datacenter)

        # Nested folder does not have trailing /
        if not dcpath.endswith('/'):
            dcpath += '/'

        # Check for full path first in case it was already supplied
        if self.folder.startswith(
            dcpath + self.params["datacenter"] + "/vm"
        ) or self.folder.startswith(dcpath + "/" + self.params["datacenter"] + "/vm"):
            fullpath = self.folder
        elif self.folder.startswith("/vm/") or self.folder == "/vm":
            fullpath = "%s%s%s" % (dcpath, self.params["datacenter"], self.folder)
        elif self.folder.startswith("/"):
            fullpath = "%s%s/vm%s" % (dcpath, self.params["datacenter"], self.folder)
        else:
            fullpath = "%s%s/vm/%s" % (dcpath, self.params["datacenter"], self.folder)

        f_obj = self.content.searchIndex.FindByInventoryPath(fullpath)

        # abort if no strategy was successful
        if f_obj is None:
            # Add some debugging values in failure.
            details = {
                'datacenter': datacenter.name,
                'datacenter_path': dcpath,
                'folder': self.folder,
                'full_search_path': fullpath,
            }
            self.module.fail_json(msg='No folder %s matched in the search path : %s' % (self.folder, fullpath),
                                  details=details)

        destfolder = f_obj

        vm_obj = None

        # always get a resource_pool
        resource_pool = self.get_resource_pool()

        # set the destination datastore for VM
        if self.params['datastore']:
            # Give precedence to datastore value provided by user
            # User may want to deploy VM to specific datastore.
            datastore_name = self.params['datastore']
            # Check if user has provided datastore cluster first
            datastore_cluster = self.cache.find_obj(self.content, [vim.StoragePod], datastore_name)
            if datastore_cluster:
                # If user specified datastore cluster so get recommended datastore
                datastore_name = self.get_recommended_datastore(datastore_cluster_obj=datastore_cluster)
            # Check if get_recommended_datastore or user specified datastore exists or not
            datastore = self.cache.find_obj(self.content, [vim.Datastore], datastore_name)
        else:
            (datastore, datastore_name) = self.select_datastore(vm_obj)

        self.configspec = vim.vm.ConfigSpec()
        self.configspec.deviceChange = []
        # create the relocation spec
        self.relospec = vim.vm.RelocateSpec()
        self.relospec.deviceChange = []
        self.configure_guestid(vm_obj=vm_obj, vm_creation=True)
        self.configure_cpu_and_memory(vm_obj=vm_obj, vm_creation=True)
        self.configure_hardware_params(vm_obj=vm_obj)
        self.configure_encryption_params(vm_obj=vm_obj)
        self.configure_resource_alloc_info(vm_obj=vm_obj)

        clonespec = None
        clone_method = None
        try:
            # ConfigSpec require name for VM creation
            self.configspec.name = self.params['name']
            self.configspec.files = vim.vm.FileInfo(logDirectory=None,
                                                    snapshotDirectory=None,
                                                    suspendDirectory=None,
                                                    vmPathName="[" + datastore_name + "]")
            esx_host = None
            # Only select specific host when ESXi hostname is provided
            if self.params['esxi_hostname']:
                esx_host = self.select_host()

            clone_method = 'CreateVM_Task'
            try:
                task = destfolder.CreateVM_Task(config=self.configspec, pool=resource_pool, host=esx_host)
            except vmodl.fault.InvalidRequest as e:
                self.module.fail_json(msg="Failed to create virtual machine due to invalid configuration "
                                          "parameter %s" % to_native(e.msg))
            except vim.fault.RestrictedVersion as e:
                self.module.fail_json(msg="Failed to create virtual machine due to "
                                          "product versioning restrictions: %s" % to_native(e.msg))
            self.change_detected = True
            self.wait_for_task(task)
        except TypeError as e:
            self.module.fail_json(msg="TypeError was returned, please ensure to give correct inputs. %s" % to_text(e))

        if task.info.state == 'error':
            # https://kb.vmware.com/selfservice/microsites/search.do?language=en_US&cmd=displayKC&externalId=2021361
            # https://kb.vmware.com/selfservice/microsites/search.do?language=en_US&cmd=displayKC&externalId=2173

            # provide these to the user for debugging
            clonespec_json = serialize_spec(clonespec)
            configspec_json = serialize_spec(self.configspec)
            kwargs = {
                'changed': self.change_applied,
                'failed': True,
                'msg': task.info.error.msg,
                'clonespec': clonespec_json,
                'configspec': configspec_json,
                'clone_method': clone_method
            }

            return kwargs

    def reconfigure_vm(self):
        self.configspec = vim.vm.ConfigSpec()
        self.configspec.deviceChange = []
        # create the relocation spec
        self.relospec = vim.vm.RelocateSpec()
        self.relospec.deviceChange = []
        self.configure_guestid(vm_obj=self.current_vm_obj)
        self.configure_cpu_and_memory(vm_obj=self.current_vm_obj)
        self.configure_hardware_params(vm_obj=self.current_vm_obj)
        self.configure_encryption_params(vm_obj=self.current_vm_obj)
        self.configure_resource_alloc_info(vm_obj=self.current_vm_obj)

        if self.params['resource_pool']:
            self.relospec.pool = self.get_resource_pool()

            if self.relospec.pool != self.current_vm_obj.resourcePool:
                self.tracked_changes['resourcePool'] = str(self.relospec.pool)
                if self.module.check_mode:
                    self.change_applied = True
                else:
                    task = self.current_vm_obj.RelocateVM_Task(spec=self.relospec)
                    self.wait_for_task(task)
                    if task.info.state == 'error':
                        return {'changed': self.change_applied, 'failed': True, 'msg': task.info.error.msg, 'op': 'relocate'}

        # Only send VMware task if we see a modification
        if self.change_detected:
            self.tracked_changes['configspec'] = str(self.configspec)
            if self.module.check_mode:
                self.change_applied = True
            else:
                task = None
                try:
                    task = self.current_vm_obj.ReconfigVM_Task(spec=self.configspec)
                except vim.fault.RestrictedVersion as e:
                    self.module.fail_json(msg="Failed to reconfigure virtual machine due to"
                                              " product versioning restrictions: %s" % to_native(e.msg))
                self.wait_for_task(task)
                if task.info.state == 'error':
                    return {'changed': self.change_applied, 'failed': True, 'msg': task.info.error.msg, 'op': 'reconfig'}

        # Rename VM
        if self.params['uuid'] and self.params['name'] and self.params['name'] != self.current_vm_obj.config.name:
            self.tracked_changes['name'] = self.params['name']
            if self.module.check_mode:
                self.change_applied = True
            else:
                task = self.current_vm_obj.Rename_Task(self.params['name'])
                self.wait_for_task(task)
                if task.info.state == 'error':
                    return {'changed': self.change_applied, 'failed': True, 'msg': task.info.error.msg, 'op': 'rename'}

        vm_facts = self.gather_facts(self.current_vm_obj)
        return {'changed': self.change_applied, 'failed': False, 'instance': vm_facts, 'changes': self.tracked_changes}

    def wait_for_task(self, task, poll_interval=1):
        """
        Wait for a VMware task to complete.  Terminal states are 'error' and 'success'.

        Inputs:
          - task: the task to wait for
          - poll_interval: polling interval to check the task, in seconds

        Modifies:
          - self.change_applied
        """
        # https://www.vmware.com/support/developer/vc-sdk/visdk25pubs/ReferenceGuide/vim.Task.html
        # https://www.vmware.com/support/developer/vc-sdk/visdk25pubs/ReferenceGuide/vim.TaskInfo.html
        # https://github.com/virtdevninja/pyvmomi-community-samples/blob/master/samples/tools/tasks.py
        while task.info.state not in ['error', 'success']:
            time.sleep(poll_interval)
        self.change_applied = self.change_applied or task.info.state == 'success'

    def get_vm_events(self, vm, eventTypeIdList):
        byEntity = vim.event.EventFilterSpec.ByEntity(entity=vm, recursion="self")
        filterSpec = vim.event.EventFilterSpec(entity=byEntity, eventTypeId=eventTypeIdList)
        eventManager = self.content.eventManager
        return eventManager.QueryEvent(filterSpec)


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        state=dict(type='str', default='present',
                   choices=['absent', 'present']),
        name=dict(type='str', required=True),
        folder=dict(type='str'),
        guest_id=dict(type='str'),
        hardware=dict(
            type='dict',
            default={},
            options=dict(
                boot_firmware=dict(type='str', choices=['bios', 'efi']),
                cpu_limit=dict(type='int'),
                cpu_reservation=dict(type='int'),
                hotadd_cpu=dict(type='bool'),
                hotadd_memory=dict(type='bool'),
                vpmc_enabled=dict(type='bool'),
                max_connections=dict(type='int'),
                mem_limit=dict(type='int'),
                cpu_shares_level=dict(type='str', choices=['low', 'normal', 'high', 'custom']),
                mem_shares_level=dict(type='str', choices=['low', 'normal', 'high', 'custom']),
                cpu_shares=dict(type='int'),
                mem_shares=dict(type='int'),
                mem_reservation=dict(type='int', aliases=['memory_reservation']),
                memory_mb=dict(type='int'),
                memory_reservation_lock=dict(type='bool'),
                nested_virt=dict(type='bool'),
                num_cpu_cores_per_socket=dict(type='int'),
                num_cpus=dict(type='int'),
                secure_boot=dict(type='bool'),
                version=dict(type='str'),
                virt_based_security=dict(type='bool'),
                iommu=dict(type='bool')
            )),
        encryption=dict(
            type='dict',
            default={},
            options=dict(
                encrypted_vmotion=dict(type='str', choices=['disabled', 'opportunistic', 'required']),
                encrypted_ft=dict(type='str', choices=['disabled', 'opportunistic', 'required'])
            )),
        force=dict(type='bool', default=False),
        datacenter=dict(type='str', default='ha-datacenter'),
        esxi_hostname=dict(type='str'),
        cluster=dict(type='str'),
        resource_pool=dict(type='str'),
        datastore=dict(type='str'),
        delete_from_inventory=dict(type='bool', default=False),
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True,
                           mutually_exclusive=[
                               ['cluster', 'esxi_hostname'],
                           ],
                           required_one_of=[
                               ['cluster', 'esxi_hostname'],
                           ],
                           )
    result = {'failed': False, 'changed': False}
    pyv = PyVmomiHelper(module)

    # Check requirements for virtualization based security
    if pyv.params['hardware']['virt_based_security']:
        if not pyv.params['hardware']['nested_virt']:
            pyv.module.fail_json(msg="Virtualization based security requires nested virtualization. Please enable nested_virt.")

        if not pyv.params['hardware']['secure_boot']:
            pyv.module.fail_json(msg="Virtualization based security requires (U)EFI secure boot. Please enable secure_boot.")

        if not pyv.params['hardware']['iommu']:
            pyv.module.fail_json(msg="Virtualization based security requires I/O MMU. Please enable iommu.")

    # Check if the VM exists before continuing
    vm = pyv.get_vm()

    # VM already exists
    if vm:
        if module.params['state'] == 'absent':
            # destroy it
            if module.check_mode:
                result.update(
                    vm_name=vm.name,
                    changed=True,
                    current_powerstate=vm.summary.runtime.powerState.lower(),
                    desired_operation='remove_vm',
                )
                module.exit_json(**result)
            if module.params['force']:
                # has to be poweredoff first
                set_vm_power_state(pyv.content, vm, 'poweredoff', module.params['force'])
            result = pyv.remove_vm(vm, module.params['delete_from_inventory'])
        elif module.params['state'] == 'present':
            # Note that check_mode is handled inside reconfigure_vm
            result = pyv.reconfigure_vm()
        elif module.params['state'] in ['poweredon', 'powered-on', 'poweredoff',
                                        'powered-off', 'restarted', 'suspended',
                                        'shutdownguest', 'shutdown-guest',
                                        'rebootguest', 'reboot-guest']:
            if module.check_mode:
                # Identify if the power state would have changed if not in check mode
                current_powerstate = vm.summary.runtime.powerState.lower()
                powerstate_will_change = False
                if ((current_powerstate == 'poweredon' and module.params['state'] not in ['poweredon', 'powered-on'])
                        or (current_powerstate == 'poweredoff' and module.params['state']
                            not in ['poweredoff', 'powered-off', 'shutdownguest', 'shutdown-guest'])
                        or (current_powerstate == 'suspended' and module.params['state'] != 'suspended')):
                    powerstate_will_change = True

                result.update(
                    vm_name=vm.name,
                    changed=powerstate_will_change,
                    current_powerstate=current_powerstate,
                    desired_operation='set_vm_power_state',
                )
                module.exit_json(**result)
            # set powerstate
            tmp_result = set_vm_power_state(pyv.content, vm, module.params['state'], module.params['force'], module.params['state_change_timeout'])
            if tmp_result['changed']:
                result["changed"] = True
                if module.params['state'] in ['poweredon', 'powered-on', 'restarted', 'rebootguest', 'reboot-guest'] and module.params['wait_for_ip_address']:
                    wait_result = wait_for_vm_ip(pyv.content, vm, module.params['wait_for_ip_address_timeout'])
                    if not wait_result:
                        module.fail_json(msg='Waiting for IP address timed out')
                    tmp_result['instance'] = wait_result
            if not tmp_result["failed"]:
                result["failed"] = False
            result['instance'] = tmp_result['instance']
            if tmp_result["failed"]:
                result["failed"] = True
                result["msg"] = tmp_result["msg"]
        else:
            # This should not happen
            raise AssertionError()
    # VM doesn't exist
    else:
        if module.params['state'] in ['poweredon', 'powered-on', 'poweredoff', 'powered-off',
                                      'present', 'restarted', 'suspended']:
            if module.check_mode:
                result.update(
                    changed=True,
                    desired_operation='deploy_vm',
                )
                module.exit_json(**result)
            result = pyv.deploy_vm()
            if result['failed']:
                module.fail_json(msg='Failed to create a virtual machine : %s' % result['msg'])

    if result['failed']:
        module.fail_json(**result)
    else:
        module.exit_json(**result)


if __name__ == '__main__':
    main()

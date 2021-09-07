#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Ansible Project
# Copyright: (c) 2018, Abhijeet Kasurde <akasurde@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: vmware_guest_disk
short_description: Manage disks related to virtual machine in given vCenter infrastructure
description:
    - This module can be used to add, remove and update disks belonging to given virtual machine.
    - All parameters and VMware object names are case sensitive.
    - This module is destructive in nature, please read documentation carefully before proceeding.
    - Be careful while removing disk specified as this may lead to data loss.
author:
    - Abhijeet Kasurde (@Akasurde) <akasurde@redhat.com>
notes:
    - Tested on vSphere 6.0 and 6.5
requirements:
    - "python >= 2.6"
    - PyVmomi
options:
   name:
     description:
     - Name of the virtual machine.
     - This is a required parameter, if parameter C(uuid) or C(moid) is not supplied.
     type: str
   uuid:
     description:
     - UUID of the instance to gather facts if known, this is VMware's unique identifier.
     - This is a required parameter, if parameter C(name) or C(moid) is not supplied.
     type: str
   moid:
     description:
     - Managed Object ID of the instance to manage if known, this is a unique identifier only within a single vCenter instance.
     - This is required if C(name) or C(uuid) is not supplied.
     type: str
   folder:
     description:
     - Destination folder, absolute or relative path to find an existing guest.
     - This is a required parameter, only if multiple VMs are found with same name.
     - The folder should include the datacenter. ESX's datacenter is ha-datacenter
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
   datacenter:
     description:
     - The datacenter name to which virtual machine belongs to.
     required: True
     type: str
   use_instance_uuid:
     description:
     - Whether to use the VMware instance UUID rather than the BIOS UUID.
     default: false
     type: bool
   disk:
     description:
     - A list of disks to add or remove.
     - The virtual disk related information is provided using this list.
     - All values and parameters are case sensitive.
     suboptions:
       size:
         description:
           - Disk storage size.
           - If size specified then unit must be specified. There is no space allowed in between size number and unit.
           - Only first occurrence in disk element will be considered, even if there are multiple size* parameters available.
         type: str
       size_kb:
         description: Disk storage size in kb.
         type: int
       size_mb:
         description: Disk storage size in mb.
         type: int
       size_gb:
         description: Disk storage size in gb.
         type: int
       size_tb:
         description: Disk storage size in tb.
         type: int
       type:
         description:
         - The type of disk, if not specified then use C(thick) type for new disk, no eagerzero.
         - The disk type C(rdm) is added in version 1.13.0.
         type: str
         choices: ['thin', 'eagerzeroedthick', 'thick', 'rdm' ]
       disk_mode:
         description:
           - Type of disk mode. If not specified then use C(persistent) mode for new disk.
           - If set to 'persistent' mode, changes are immediately and permanently written to the virtual disk.
           - If set to 'independent_persistent' mode, same as persistent, but not affected by snapshots.
           - If set to 'independent_nonpersistent' mode, changes to virtual disk are made to a redo log and discarded
             at power off, but not affected by snapshots.
         type: str
         choices: ['persistent', 'independent_persistent', 'independent_nonpersistent']
       rdm_path:
         description:
         - Path of LUN for Raw Device Mapping required for disk type C(rdm).
         - Only valid if C(type) is set to C(rdm).
         type: str
       cluster_disk:
         description:
           - This value allows for the sharing of an RDM between two machines.
           - The primary machine holding the RDM uses the default C(False).
           - The secondary machine holding the RDM uses C(True).
         type: bool
         default: False
         version_added: '1.15.0'
       compatibility_mode:
         description: Compatibility mode for raw devices. Required for disk type 'rdm'
         type: str
         choices: ['physicalMode','virtualMode']
       sharing:
         description:
           - The sharing mode of the virtual disk.
           - Setting sharing means that multiple virtual machines can write to the virtual disk.
           - Sharing can only be set if C(type) is set to C(eagerzeroedthick)or C(rdm).
         type: bool
         default: False
       datastore:
         description: Name of datastore or datastore cluster to be used for the disk.
         type: str
       autoselect_datastore:
         description: Select the less used datastore. Specify only if C(datastore) is not specified.
         type: bool
       scsi_controller:
         description:
           - SCSI controller number. Only 4 SCSI controllers are allowed per VM.
           - Care should be taken while specifying 'scsi_controller' is 0 and 'unit_number' as 0 as this disk may contain OS.
         type: int
         choices: [0, 1, 2, 3]
       bus_sharing:
         description:
           - Only functions with Paravirtual SCSI Controller.
           - Allows for the sharing of the scsi bus between two virtual machines.
         type: str
         choices: ['noSharing', 'physicalSharing', 'virtualSharing']
         default: 'noSharing'
       unit_number:
         description:
           - Disk Unit Number.
           - Valid value range from 0 to 15, except 7 for SCSI Controller.
           - Valid value range from 0 to 64, except 7 for Paravirtual SCSI Controller on Virtual Hardware version 14 or higher
           - Valid value range from 0 to 29 for SATA controller.
           - Valid value range from 0 to 14 for NVME controller.
         type: int
         required: True
       scsi_type:
         description:
           - Type of SCSI controller. This value is required only for the first occurrence of SCSI Controller.
           - This value is ignored, if SCSI Controller is already present or C(state) is C(absent).
         type: str
         choices: ['buslogic', 'lsilogic', 'lsilogicsas', 'paravirtual']
       destroy:
         description: If C(state) is C(absent), make sure the disk file is deleted from the datastore. Added in version 2.10.
         type: bool
         default: True
       filename:
         description:
           - Existing disk image to be used. Filename must already exist on the datastore.
           - Specify filename string in C([datastore_name] path/to/file.vmdk) format. Added in version 2.10.
         type: str
       state:
         description:
           - State of disk.
           - If set to 'absent', disk will be removed permanently from virtual machine configuration and from VMware storage.
           - If set to 'present', disk will be added if not present at given Controller and Unit Number.
           - or disk exists with different size, disk size is increased, reducing disk size is not allowed.
         type: str
         choices: ['present', 'absent']
         default: 'present'
       controller_type:
         description:
           - This parameter is added for managing disks attaching other types of controllers, e.g., SATA or NVMe.
           - If either C(controller_type) or C(scsi_type) is not specified, then use C(paravirtual) type.
         type: str
         choices: ['buslogic', 'lsilogic', 'lsilogicsas', 'paravirtual', 'sata', 'nvme']
       controller_number:
         description: This parameter is used with C(controller_type) for specifying controller bus number.
         type: int
         choices: [0, 1, 2, 3]
       iolimit:
         description: Section specifies the shares and limit for storage I/O resource.
         suboptions:
           limit:
             description: Section specifies values for limit where the utilization of a virtual machine will not exceed, even if there are available resources.
             type: int
           shares:
             description: Specifies different types of shares user can add for the given disk.
             suboptions:
               level:
                 description: Specifies different level for the shares section.
                 type: str
                 choices: ['low', 'normal', 'high', 'custom']
               level_value:
                 description: Custom value when C(level) is set as C(custom).
                 type: int
             type: dict
         type: dict
       shares:
         description: Section for iolimit section tells about what are all different types of shares user can add for disk.
         suboptions:
           level:
             description: Tells about different level for the shares section.
             type: str
             choices: ['low', 'normal', 'high', 'custom']
           level_value:
             description: Custom value when C(level) is set as C(custom).
             type: int
         type: dict
     default: []
     type: list
     elements: dict
extends_documentation_fragment:
- community.vmware.vmware.documentation
'''

EXAMPLES = r'''
- name: Add disks to virtual machine using UUID
  community.vmware.vmware_guest_disk:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    datacenter: "{{ datacenter_name }}"
    uuid: 421e4592-c069-924d-ce20-7e7533fab926
    disk:
      - size_mb: 10
        type: thin
        datastore: datacluster0
        state: present
        scsi_controller: 1
        unit_number: 1
        scsi_type: 'paravirtual'
        disk_mode: 'persistent'
      - size_gb: 10
        type: eagerzeroedthick
        state: present
        autoselect_datastore: True
        scsi_controller: 2
        scsi_type: 'buslogic'
        unit_number: 12
        disk_mode: 'independent_persistent'
      - size: 10Gb
        type: eagerzeroedthick
        state: present
        autoselect_datastore: True
        scsi_controller: 2
        scsi_type: 'buslogic'
        unit_number: 1
        disk_mode: 'independent_nonpersistent'
      - filename: "[datastore1] path/to/existing/disk.vmdk"
  delegate_to: localhost
  register: disk_facts

- name: Add disks with specified shares to the virtual machine
  community.vmware.vmware_guest_disk:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    datacenter: "{{ datacenter_name }}"
    disk:
      - size_gb: 1
        type: thin
        datastore: datacluster0
        state: present
        scsi_controller: 1
        unit_number: 1
        disk_mode: 'independent_persistent'
        shares:
          level: custom
          level_value: 1300
  delegate_to: localhost
  register: test_custom_shares

- name: Add physical raw device mapping to virtual machine using name
  community.vmware.vmware_guest_disk:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    datacenter: "{{ datacenter_name }}"
    validate_certs: no
    name: "Test_VM"
    disk:
      - type: rdm
        state: present
        scsi_controller: 1
        unit_number: 5
        rdm_path: /vmfs/devices/disks/naa.060000003b1234efb453
        compatibility_mode: 'physicalMode'

- name: Add virtual raw device mapping to virtual machine using name and virtual mode
  community.vmware.vmware_guest_disk:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    datacenter: "{{ datacenter_name }}"
    validate_certs: no
    name: "Test_VM"
    disk:
      - type: rdm
        state: present
        scsi_controller: 1
        unit_number: 5
        rdm_path: /vmfs/devices/disks/naa.060000003b1234efb453
        compatibility_mode: 'virtualMode'
        disk_mode: 'persistent'

- name: Add raw device mapping to virtual machine with Physical bus sharing
  community.vmware.vmware_guest_disk:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    datacenter: "{{ datacenter_name }}"
    validate_certs: no
    name: "Test_VM"
    disk:
      - type: rdm
        state: present
        scsi_controller: 1
        unit_number: 5
        rdm_path: /vmfs/devices/disks/naa.060000003b1234efb453
        compatibility_mode: 'virtualMode'
        disk_mode: 'persistent'
        bus_sharing: physicalSharing

- name: Add raw device mapping to virtual machine with Physical bus sharing and clustered disk
  community.vmware.vmware_guest_disk:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    datacenter: "{{ datacenter_name }}"
    validate_certs: no
    name: "Test_VM"
    disk:
      - type: rdm
        state: present
        scsi_controller: 1
        unit_number: 5
        compatibility_mode: 'virtualMode'
        disk_mode: 'persistent'
        bus_sharing: physicalSharing
        filename: "[datastore1] path/to/rdm/disk-marker.vmdk"

- name: create new disk with custom IO limits and shares in IO Limits
  community.vmware.vmware_guest_disk:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    datacenter: "{{ datacenter_name }}"
    disk:
      - size_gb: 1
        type: thin
        datastore: datacluster0
        state: present
        scsi_controller: 1
        unit_number: 1
        disk_mode: 'independent_persistent'
        iolimit:
            limit: 1506
            shares:
              level: custom
              level_value: 1305
  delegate_to: localhost
  register: test_custom_IoLimit_shares

- name: Remove disks from virtual machine using name
  community.vmware.vmware_guest_disk:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    datacenter: "{{ datacenter_name }}"
    name: VM_225
    disk:
      - state: absent
        scsi_controller: 1
        unit_number: 1
  delegate_to: localhost
  register: disk_facts

- name: Remove disk from virtual machine using moid
  community.vmware.vmware_guest_disk:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    datacenter: "{{ datacenter_name }}"
    moid: vm-42
    disk:
      - state: absent
        scsi_controller: 1
        unit_number: 1
  delegate_to: localhost
  register: disk_facts

- name: Remove disk from virtual machine but keep the VMDK file on the datastore
  community.vmware.vmware_guest_disk:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    datacenter: "{{ datacenter_name }}"
    name: VM_225
    disk:
      - state: absent
        scsi_controller: 1
        unit_number: 2
        destroy: no
  delegate_to: localhost
  register: disk_facts

- name: Add disks to virtual machine using UUID to SATA and NVMe controller
  community.vmware.vmware_guest_disk:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    datacenter: "{{ datacenter_name }}"
    validate_certs: no
    uuid: 421e4592-c069-924d-ce20-7e7533fab926
    disk:
      - size_mb: 256
        type: thin
        datastore: datacluster0
        state: present
        controller_type: sata
        controller_number: 1
        unit_number: 1
        disk_mode: 'persistent'
      - size_gb: 1
        state: present
        autoselect_datastore: True
        controller_type: nvme
        controller_number: 2
        unit_number: 3
        disk_mode: 'independent_persistent'
  delegate_to: localhost
  register: disk_facts
'''

RETURN = r'''
disk_status:
    description: metadata about the virtual machine's disks after managing them
    returned: always
    type: dict
    sample: {
        "0": {
            "backing_datastore": "datastore2",
            "backing_disk_mode": "persistent",
            "backing_eagerlyscrub": false,
            "backing_filename": "[datastore2] VM_225/VM_225.vmdk",
            "backing_thinprovisioned": false,
            "backing_writethrough": false,
            "backing_uuid": "421e4592-c069-924d-ce20-7e7533fab926",
            "capacity_in_bytes": 10485760,
            "capacity_in_kb": 10240,
            "controller_key": 1000,
            "key": 2000,
            "label": "Hard disk 1",
            "summary": "10,240 KB",
            "unit_number": 0
        },
    }
'''

import re
try:
    from pyVmomi import vim
except ImportError:
    pass

from random import randint
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible_collections.community.vmware.plugins.module_utils.vmware import PyVmomi, vmware_argument_spec,\
    wait_for_task, find_obj, get_all_objs, get_parent_datacenter
from ansible_collections.community.vmware.plugins.module_utils.vm_device_helper import PyVmomiDeviceHelper


class PyVmomiHelper(PyVmomi):
    def __init__(self, module):
        super(PyVmomiHelper, self).__init__(module)
        self.device_helper = PyVmomiDeviceHelper(self.module)
        self.desired_disks = self.params['disk']  # Match with vmware_guest parameter
        self.vm = None
        self.ctl_device_type = self.device_helper.scsi_device_type.copy()
        self.ctl_device_type.update({'sata': self.device_helper.sata_device_type, 'nvme': self.device_helper.nvme_device_type})
        self.config_spec = vim.vm.ConfigSpec()
        self.config_spec.deviceChange = []

    def find_disk_by_key(self, disk_key, disk_unit_number):
        found_disk = None
        for device in self.vm.config.hardware.device:
            if isinstance(device, vim.vm.device.VirtualDisk) and device.key == disk_key:
                if device.unitNumber == disk_unit_number:
                    found_disk = device
                    break

        return found_disk

    @staticmethod
    def create_disk(ctl_key, disk):
        """
        Create Virtual Device Spec for virtual disk
        Args:
            ctl_key: Unique SCSI Controller Key
            disk: The disk configurations dict

        Returns: Virtual Device Spec for virtual disk

        """
        disk_spec = vim.vm.device.VirtualDeviceSpec()
        disk_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
        disk_spec.device = vim.vm.device.VirtualDisk()
        disk_spec.device.key = -randint(20000, 24999)

        # Check if RDM first as changing backing later on will erase some settings like disk_mode
        if disk['disk_type'] == 'rdm':
            disk_spec.device.backing = vim.vm.device.VirtualDisk.RawDiskMappingVer1BackingInfo()
            disk_spec.device.backing.deviceName = disk['rdm_path']
            disk_spec.device.backing.compatibilityMode = disk['compatibility_mode']
        else:
            disk_spec.device.backing = vim.vm.device.VirtualDisk.FlatVer2BackingInfo()

        disk_spec.device.backing.diskMode = disk['disk_mode']
        disk_spec.device.backing.sharing = disk['sharing']
        disk_spec.device.controllerKey = ctl_key
        disk_spec.device.unitNumber = disk['disk_unit_number']

        if disk['disk_type'] == 'thin':
            disk_spec.device.backing.thinProvisioned = True
        elif disk['disk_type'] == 'eagerzeroedthick':
            disk_spec.device.backing.eagerlyScrub = True

        return disk_spec

    def reconfigure_vm(self, config_spec, device_type):
        """
        Reconfigure virtual machine after modifying device spec
        Args:
            config_spec: Config Spec
            device_type: Type of device being modified

        Returns: Boolean status 'changed' and actual task result

        """
        changed, results = (False, '')
        try:
            # Perform actual VM reconfiguration
            task = self.vm.ReconfigVM_Task(spec=config_spec)
            changed, results = wait_for_task(task)
        except vim.fault.InvalidDeviceSpec as invalid_device_spec:
            self.module.fail_json(msg="Failed to manage '%s' on given virtual machine due to invalid"
                                      " device spec : %s" % (device_type, to_native(invalid_device_spec.msg)),
                                      details="Please check ESXi server logs for more details.")
        except vim.fault.RestrictedVersion as e:
            self.module.fail_json(msg="Failed to reconfigure virtual machine due to"
                                      " product versioning restrictions: %s" % to_native(e.msg))

        return changed, results

    def get_ioandshares_diskconfig(self, disk_spec, disk):
        io_disk_spec = vim.StorageResourceManager.IOAllocationInfo()
        if 'iolimit' in disk:
            io_disk_spec.limit = disk['iolimit']['limit']
            if 'shares' in disk['iolimit']:
                shares_spec = vim.SharesInfo()
                shares_spec.level = disk['iolimit']['shares']['level']
                if shares_spec.level == 'custom':
                    shares_spec.shares = disk['iolimit']['shares']['level_value']
                io_disk_spec.shares = shares_spec
            disk_spec.device.storageIOAllocation = io_disk_spec
        if 'shares' in disk:
            shares_spec = vim.SharesInfo()
            shares_spec.level = disk['shares']['level']
            if shares_spec.level == 'custom':
                shares_spec.shares = disk['shares']['level_value']
            io_disk_spec.shares = shares_spec
            disk_spec.device.storageIOAllocation = io_disk_spec
        return disk_spec

    def get_sharing(self, disk, disk_type, disk_index):
        """
        Get the sharing mode of the virtual disk
        Args:
            disk: Virtual disk data object
            disk_type: Disk type of the virtual disk
            disk_index: Disk unit number at which disk needs to be attached

        Returns:
            sharing_mode: The sharing mode of the virtual disk

        """
        sharing = disk.get('sharing')
        if sharing and disk_type != 'eagerzeroedthick' and disk_type != 'rdm':
            self.module.fail_json(msg="Invalid 'sharing' mode specified for disk index [%s]. 'disk_mode'"
                                      " must be 'eagerzeroedthick' or 'rdm' when 'sharing'." % disk_index)
        if sharing:
            sharing_mode = 'sharingMultiWriter'
        else:
            sharing_mode = 'sharingNone'
        return sharing_mode

    def ensure_disks(self, vm_obj=None):
        """
        Manage internal state of virtual machine disks
        Args:
            vm_obj: Managed object of virtual machine

        """
        # Set vm object
        self.vm = vm_obj
        vm_files_datastore = self.vm.config.files.vmPathName.split(' ')[0].strip('[]')
        # Sanitize user input
        disk_data = self.sanitize_disk_inputs()
        ctl_changed = False
        disk_change_list = list()
        results = dict(changed=False, disk_data=None, disk_changes=dict())
        new_added_disk_ctl = list()

        # Deal with controller
        for disk in disk_data:
            ctl_found = False
            # check if disk controller is in the new adding queue
            for new_ctl in new_added_disk_ctl:
                if new_ctl['controller_type'] == disk['controller_type'] and new_ctl['controller_number'] == disk['controller_number']:
                    ctl_found = True
                    break
            # check if disk controller already exists
            if not ctl_found:
                for device in self.vm.config.hardware.device:
                    if isinstance(device, self.ctl_device_type[disk['controller_type']]):
                        if device.busNumber == disk['controller_number']:
                            ctl_found = True
                            break
            # create disk controller when not found and disk state is present
            if not ctl_found and disk['state'] == 'present':
                # Create new controller
                if disk['controller_type'] in self.device_helper.scsi_device_type.keys():
                    ctl_spec = self.device_helper.create_scsi_controller(disk['controller_type'], disk['controller_number'], disk['bus_sharing'])
                elif disk['controller_type'] == 'sata':
                    ctl_spec = self.device_helper.create_sata_controller(disk['controller_number'])
                elif disk['controller_type'] == 'nvme':
                    ctl_spec = self.device_helper.create_nvme_controller(disk['controller_number'])
                new_added_disk_ctl.append({'controller_type': disk['controller_type'], 'controller_number': disk['controller_number']})
                ctl_changed = True
                self.config_spec.deviceChange.append(ctl_spec)
            elif not ctl_found and disk['state'] == 'absent':
                self.module.fail_json(msg="Not found 'controller_type': '%s', 'controller_number': '%s', so can not"
                                          " remove this disk, please make sure 'controller_type' and"
                                          " 'controller_number' are correct." % (disk['controller_type'], disk['controller_number']))
        if ctl_changed:
            self.reconfigure_vm(self.config_spec, 'Disk Controller')
            self.config_spec = vim.vm.ConfigSpec()
            self.config_spec.deviceChange = []

        # Deal with Disks
        for disk in disk_data:
            disk_found = False
            disk_change = False
            ctl_found = False
            for device in self.vm.config.hardware.device:
                if isinstance(device, self.ctl_device_type[disk['controller_type']]) and device.busNumber == disk['controller_number']:
                    for disk_key in device.device:
                        disk_device = self.find_disk_by_key(disk_key, disk['disk_unit_number'])
                        if disk_device is not None:
                            disk_found = True
                            if disk['state'] == 'present':
                                disk_spec = vim.vm.device.VirtualDeviceSpec()
                                # set the operation to edit so that it knows to keep other settings
                                disk_spec.device = disk_device
                                # If this is an RDM ignore disk size
                                if disk['disk_type'] != 'rdm':
                                    if disk['size'] < disk_spec.device.capacityInKB:
                                        self.module.fail_json(msg="Given disk size at disk index [%s] is smaller than found"
                                                                  " (%d < %d). Reducing disks is not allowed."
                                                                  % (disk['disk_index'], disk['size'],
                                                                      disk_spec.device.capacityInKB))
                                    if disk['size'] != disk_spec.device.capacityInKB:
                                        disk_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
                                        disk_spec = self.get_ioandshares_diskconfig(disk_spec, disk)
                                        disk_spec.device.capacityInKB = disk['size']
                                        self.config_spec.deviceChange.append(disk_spec)
                                        disk_change = True
                                        disk_change_list.append(disk_change)
                                        results['disk_changes'][disk['disk_index']] = "Disk reconfigured."

                            elif disk['state'] == 'absent':
                                # Disk already exists, deleting
                                disk_spec = vim.vm.device.VirtualDeviceSpec()
                                disk_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.remove
                                if disk['destroy'] is True:
                                    disk_spec.fileOperation = vim.vm.device.VirtualDeviceSpec.FileOperation.destroy
                                disk_spec.device = disk_device
                                self.config_spec.deviceChange.append(disk_spec)
                                disk_change = True
                                disk_change_list.append(disk_change)
                                results['disk_changes'][disk['disk_index']] = "Disk deleted."
                            break

                    if disk_found:
                        break
                    if not disk_found and disk['state'] == 'present':
                        # Add new disk
                        disk_spec = self.create_disk(device.key, disk)
                        # get Storage DRS recommended datastore from the datastore cluster
                        if disk['disk_type'] == 'rdm':
                            # Since RDMs can be shared between two machines cluster_disk with rdm will
                            # invoke a copy of the existing disk instead of trying to create a new one which causes
                            # file lock issues in VSphere. This ensures we dont add a "create" operation.
                            if disk['filename'] is not None and disk['cluster_disk'] is True:
                                disk_spec.device.backing.fileName = disk['filename']
                            else:
                                disk_spec.fileOperation = vim.vm.device.VirtualDeviceSpec.FileOperation.create
                        else:
                            if disk['filename'] is None:
                                if disk['datastore_cluster'] is not None:
                                    datastore_name = self.get_recommended_datastore(datastore_cluster_obj=disk['datastore_cluster'], disk_spec_obj=disk_spec)
                                    disk['datastore'] = find_obj(self.content, [vim.Datastore], datastore_name)

                                disk_spec.fileOperation = vim.vm.device.VirtualDeviceSpec.FileOperation.create
                                disk_spec.device.capacityInKB = disk['size']
                                # Set backing filename when datastore is configured and not the same as VM datastore
                                # If datastore is not configured or backing filename is not set, default is VM datastore
                                if disk['datastore'] is not None and disk['datastore'].name != vm_files_datastore:
                                    disk_spec.device.backing.datastore = disk['datastore']
                                    disk_spec.device.backing.fileName = "[%s] %s/%s_%s_%s_%s.vmdk" % (disk['datastore'].name,
                                                                                                      self.vm.name,
                                                                                                      self.vm.name,
                                                                                                      device.key,
                                                                                                      str(disk['disk_unit_number']),
                                                                                                      str(randint(1, 10000)))
                            elif disk['filename'] is not None:
                                disk_spec.device.backing.fileName = disk['filename']
                            disk_spec = self.get_ioandshares_diskconfig(disk_spec, disk)

                        self.config_spec.deviceChange.append(disk_spec)
                        disk_change = True
                        disk_change_list.append(disk_change)
                        results['disk_changes'][disk['disk_index']] = "Disk created."
                        break
                    if not disk_found and disk['state'] == 'absent':
                        self.module.fail_json(msg="Not found disk with 'controller_type': '%s',"
                                                  " 'controller_number': '%s', 'unit_number': '%s' to remove."
                                                  % (disk['controller_type'], disk['controller_number'], disk['disk_unit_number']))
            if disk_change:
                # Adding multiple disks in a single attempt raises weird errors
                # So adding single disk at a time.
                self.reconfigure_vm(self.config_spec, 'disks')
                self.config_spec = vim.vm.ConfigSpec()
                self.config_spec.deviceChange = []
        if any(disk_change_list):
            results['changed'] = True
        results['disk_data'] = self.gather_disk_facts(vm_obj=self.vm)
        self.module.exit_json(**results)

    def sanitize_disk_inputs(self):
        """
        Check correctness of disk input provided by user

        Returns: A list of dictionary containing disk information

        """
        disks_data = list()
        if not self.desired_disks:
            self.module.exit_json(changed=False, msg="No disks provided for virtual machine '%s' for management."
                                                     % self.vm.name)

        for disk_index, disk in enumerate(self.desired_disks):
            # Initialize default value for disk
            current_disk = dict(disk_index=disk_index,
                                state='present',
                                destroy=True,
                                filename=None,
                                datastore_cluster=None,
                                datastore=None,
                                autoselect_datastore=True,
                                disk_unit_number=0,
                                controller_number=0,
                                disk_mode='persistent',
                                disk_type='thick',
                                sharing=False,
                                bus_sharing='noSharing',
                                cluster_disk=False)
            # Check state
            if disk['state'] is not None:
                current_disk['state'] = disk['state']

            # Check controller type
            if disk['scsi_type'] is not None and disk['controller_type'] is None:
                current_disk['controller_type'] = disk['scsi_type']
            elif disk['scsi_type'] is None and disk['controller_type'] is None:
                current_disk['controller_type'] = 'paravirtual'
            elif disk['controller_type'] is not None and disk['scsi_type'] is None:
                current_disk['controller_type'] = disk['controller_type']
            else:
                self.module.fail_json(msg="Please specify either 'scsi_type' or 'controller_type' for disk index [%s]."
                                          % disk_index)

            # Check controller bus number
            if disk['scsi_controller'] is not None and disk['controller_number'] is None and disk['controller_type'] is None:
                temp_disk_controller = disk['scsi_controller']
            elif disk['controller_number'] is not None and disk['scsi_controller'] is None and disk['scsi_type'] is None:
                temp_disk_controller = disk['controller_number']
            else:
                self.module.fail_json(msg="Please specify 'scsi_controller' with 'scsi_type', or 'controller_number'"
                                          " with 'controller_type' under disk parameter for disk index [%s], which is"
                                          " required while creating or configuring disk." % disk_index)
            try:
                disk_controller = int(temp_disk_controller)
            except ValueError:
                self.module.fail_json(msg="Invalid controller bus number '%s' specified"
                                          " for disk index [%s]" % (temp_disk_controller, disk_index))
            current_disk['controller_number'] = disk_controller

            try:
                temp_disk_unit_number = int(disk['unit_number'])
            except ValueError:
                self.module.fail_json(msg="Invalid Disk unit number ID '%s' specified at index [%s]."
                                          % (disk['unit_number'], disk_index))
            if current_disk['controller_type'] in self.device_helper.scsi_device_type.keys():
                # the Paravirtual SCSI Controller Supports up to 64 disks in vSphere 6.7. Using hardware
                # version 14 or higher from the vm config should catch this appropriately.
                hw_version = int(self.vm.config.version.split('-')[1])
                if current_disk['controller_type'] == 'paravirtual' and hw_version >= 14:
                    if temp_disk_unit_number not in range(0, 64):
                        self.module.fail_json(msg="Invalid Disk unit number ID specified for disk [%s] at index [%s],"
                                                  " please specify value between 0 to 64 only (excluding 7)."
                                                  % (temp_disk_unit_number, disk_index))
                    if temp_disk_unit_number == 7:
                        self.module.fail_json(msg="Invalid Disk unit number ID specified for disk at index [%s], please"
                                                  " specify value other than 7 as it is reserved for SCSI Controller."
                                                  % disk_index)

                else:
                    if temp_disk_unit_number not in range(0, 16):
                        self.module.fail_json(msg="Invalid Disk unit number ID specified for disk [%s] at index [%s],"
                                                  " please specify value between 0 to 15 only (excluding 7)."
                                                  % (temp_disk_unit_number, disk_index))
                    if temp_disk_unit_number == 7:
                        self.module.fail_json(msg="Invalid Disk unit number ID specified for disk at index [%s], please"
                                                  " specify value other than 7 as it is reserved for SCSI Controller."
                                                  % disk_index)
            elif current_disk['controller_type'] == 'sata' and temp_disk_unit_number not in range(0, 30):
                self.module.fail_json(msg="Invalid Disk unit number ID specified for SATA disk [%s] at index [%s],"
                                          " please specify value between 0 to 29" % (temp_disk_unit_number, disk_index))
            elif current_disk['controller_type'] == 'nvme' and temp_disk_unit_number not in range(0, 15):
                self.module.fail_json(msg="Invalid Disk unit number ID specified for NVMe disk [%s] at index [%s],"
                                          " please specify value between 0 to 14" % (temp_disk_unit_number, disk_index))
            current_disk['disk_unit_number'] = temp_disk_unit_number

            # By default destroy file from datastore if 'destroy' parameter is not provided
            if current_disk['state'] == 'absent':
                current_disk['destroy'] = disk.get('destroy', True)
            elif current_disk['state'] == 'present':
                # Select datastore or datastore cluster
                if disk['datastore'] is not None:
                    if disk['autoselect_datastore'] is not None:
                        self.module.fail_json(msg="Please specify either 'datastore' or 'autoselect_datastore' for"
                                                  " disk index [%s]" % disk_index)
                    # Check if given value is datastore or datastore cluster
                    datastore_name = disk['datastore']
                    datastore_cluster = find_obj(self.content, [vim.StoragePod], datastore_name)
                    datastore = find_obj(self.content, [vim.Datastore], datastore_name)
                    if datastore is None and datastore_cluster is None:
                        self.module.fail_json(msg="Failed to find datastore or datastore cluster named '%s' "
                                                  "in given configuration." % disk['datastore'])
                    if datastore_cluster:
                        # If user specified datastore cluster, keep track of that for determining datastore later
                        current_disk['datastore_cluster'] = datastore_cluster
                    elif datastore:
                        ds_datacenter = get_parent_datacenter(datastore)
                        if ds_datacenter.name != self.module.params['datacenter']:
                            self.module.fail_json(msg="Get datastore '%s' in datacenter '%s', not the configured"
                                                      " datacenter '%s'" % (datastore.name, ds_datacenter.name,
                                                                            self.module.params['datacenter']))
                        current_disk['datastore'] = datastore
                    current_disk['autoselect_datastore'] = False
                elif disk['autoselect_datastore'] is not None:
                    # Find datastore which fits requirement
                    datastores = get_all_objs(self.content, [vim.Datastore])
                    if not datastores:
                        self.module.fail_json(msg="Failed to gather information about available datastores in given"
                                                  " datacenter '%s'." % self.module.params['datacenter'])
                    datastore = None
                    datastore_freespace = 0
                    for ds in datastores:
                        if ds.summary.freeSpace > datastore_freespace:
                            # If datastore field is provided, filter destination datastores
                            datastore = ds
                            datastore_freespace = ds.summary.freeSpace
                    current_disk['datastore'] = datastore

                if disk['filename'] is not None:
                    current_disk['filename'] = disk['filename']

                if [x for x in disk.keys() if ((x.startswith('size_') or x == 'size') and disk[x] is not None)]:
                    # size, size_tb, size_gb, size_mb, size_kb
                    disk_size_parse_failed = False
                    if disk['size'] is not None:
                        size_regex = re.compile(r'(\d+(?:\.\d+)?)([tgmkTGMK][bB])')
                        disk_size_m = size_regex.match(disk['size'])
                        if disk_size_m:
                            expected = disk_size_m.group(1)
                            unit = disk_size_m.group(2)
                        else:
                            disk_size_parse_failed = True
                        try:
                            if re.match(r'\d+\.\d+', expected):
                                # We found float value in string, let's typecast it
                                expected = float(expected)
                            else:
                                # We found int value in string, let's typecast it
                                expected = int(expected)
                        except (TypeError, ValueError, NameError):
                            disk_size_parse_failed = True
                    else:
                        # Even multiple size_ parameter provided by user,
                        # consider first value only
                        param = [x for x in disk.keys() if (x.startswith('size_') and disk[x] is not None)][0]
                        unit = param.split('_')[-1]
                        disk_size = disk[param]
                        if isinstance(disk_size, (float, int)):
                            disk_size = str(disk_size)

                        try:
                            if re.match(r'\d+\.\d+', disk_size):
                                # We found float value in string, let's typecast it
                                expected = float(disk_size)
                            else:
                                # We found int value in string, let's typecast it
                                expected = int(disk_size)
                        except (TypeError, ValueError, NameError):
                            disk_size_parse_failed = True

                    if disk_size_parse_failed:
                        # Common failure
                        self.module.fail_json(msg="Failed to parse disk size for disk index [%s],"
                                                  " please review value provided"
                                                  " using documentation." % disk_index)

                    disk_units = dict(tb=3, gb=2, mb=1, kb=0)
                    unit = unit.lower()
                    if unit in disk_units:
                        current_disk['size'] = expected * (1024 ** disk_units[unit])
                    else:
                        self.module.fail_json(msg="%s is not a supported unit for disk size for disk index [%s]."
                                                  " Supported units are ['%s']." % (unit, disk_index, "', '".join(disk_units.keys())))
                elif current_disk['filename'] is None and disk['type'] != 'rdm':
                    # No size found but disk, fail. Excepting RDMs because the cluster_disk will need a filename.
                    self.module.fail_json(msg="No size, size_kb, size_mb, size_gb or size_tb"
                                              " attribute found into disk index [%s] configuration." % disk_index)

                # Type of Disk
                if disk['type'] is not None:
                    current_disk['disk_type'] = disk['type']
                # Mode of Disk
                if disk['disk_mode'] is not None:
                    current_disk['disk_mode'] = disk['disk_mode']
                # Sharing mode of disk
                current_disk['sharing'] = self.get_sharing(disk, current_disk['disk_type'], disk_index)

                if disk['shares'] is not None:
                    current_disk['shares'] = disk['shares']
                if disk['iolimit'] is not None:
                    current_disk['iolimit'] = disk['iolimit']

                # Deal with RDM disk needs. RDMS require some different values compared to Virtual Disks
                if disk['type'] == 'rdm':
                    compatibility_mode = disk.get('compatibility_mode', 'physicalMode')
                    if compatibility_mode not in ['physicalMode', 'virtualMode']:
                        self.module.fail_json(msg="Invalid 'compatibility_mode' specified for disk index [%s]. Please specify"
                                              "'compatibility_mode' value from ['physicalMode', 'virtualMode']." % disk_index)
                    current_disk['compatibility_mode'] = compatibility_mode

                    # RDMs need a path
                    if 'rdm_path'not in disk and 'filename' not in disk:
                        self.module.fail_json(msg="rdm_path and/or 'filename' needs must be specified when using disk type 'rdm'"
                                              "for disk index [%s]" % disk_index)
                    else:
                        current_disk['rdm_path'] = disk.get('rdm_path')

                    if disk['filename'] and disk['rdm_path'] is None and disk['cluster_disk'] is False:
                        self.module.fail_json(msg=" 'filename' requires setting 'cluster_disk' to True when using disk type 'rdm' without a"
                                              "'rdm_path' for disk index [%s]" % disk_index)
                    else:
                        current_disk['cluster_disk'] = disk.get('cluster_disk')

                # Enable Physical or virtuals SCSI Bus Sharing
                if disk['bus_sharing']:
                    bus_sharing = disk.get('bus_sharing', 'noSharing')
                    if bus_sharing not in ['noSharing', 'physicalSharing', 'virtualSharing']:
                        self.module.fail_json(msg="Invalid SCSI 'bus_sharing' specied for disk index [%s]. Please specify"
                                              "'bus_sharing' value from['noSharing', 'physicalSharing', 'virtualSharing']." % disk_index)
                    current_disk['bus_sharing'] = bus_sharing

            disks_data.append(current_disk)
        return disks_data

    def get_recommended_datastore(self, datastore_cluster_obj, disk_spec_obj):
        """
        Return Storage DRS recommended datastore from datastore cluster
        Args:
            datastore_cluster_obj: datastore cluster managed object

        Returns: Name of recommended datastore from the given datastore cluster,
                 Returns None if no datastore recommendation found.

        """
        # Check if Datastore Cluster provided by user is SDRS ready
        sdrs_status = datastore_cluster_obj.podStorageDrsEntry.storageDrsConfig.podConfig.enabled
        if sdrs_status:
            # We can get storage recommendation only if SDRS is enabled on given datastorage cluster
            disk_loc = vim.storageDrs.PodSelectionSpec.DiskLocator()
            pod_config = vim.storageDrs.PodSelectionSpec.VmPodConfig()
            pod_config.storagePod = datastore_cluster_obj
            pod_config.disk = [disk_loc]
            pod_sel_spec = vim.storageDrs.PodSelectionSpec()
            pod_sel_spec.initialVmConfig = [pod_config]
            storage_spec = vim.storageDrs.StoragePlacementSpec()
            storage_spec.configSpec = vim.vm.ConfigSpec()
            storage_spec.configSpec.deviceChange.append(disk_spec_obj)
            storage_spec.resourcePool = self.vm.resourcePool
            storage_spec.podSelectionSpec = pod_sel_spec
            storage_spec.vm = self.vm
            storage_spec.type = 'reconfigure'

            try:
                rec = self.content.storageResourceManager.RecommendDatastores(storageSpec=storage_spec)
                rec_action = rec.recommendations[0].action[0]
                return rec_action.destination.name
            except Exception:
                # There is some error so we fall back to general workflow
                pass
        datastore = None
        datastore_freespace = 0
        for ds in datastore_cluster_obj.childEntity:
            if ds.summary.freeSpace > datastore_freespace:
                # If datastore field is provided, filter destination datastores
                datastore = ds
                datastore_freespace = ds.summary.freeSpace
        if datastore:
            return datastore.name
        return None

    @staticmethod
    def gather_disk_facts(vm_obj):
        """
        Gather facts about VM's disks
        Args:
            vm_obj: Managed object of virtual machine

        Returns: A list of dict containing disks information

        """
        disks_facts = dict()
        if vm_obj is None:
            return disks_facts

        disk_index = 0
        for disk in vm_obj.config.hardware.device:
            if isinstance(disk, vim.vm.device.VirtualDisk):
                if disk.storageIOAllocation is None:
                    disk.storageIOAllocation = vim.StorageResourceManager.IOAllocationInfo()
                    disk.storageIOAllocation.shares = vim.SharesInfo()

                if disk.shares is None:
                    disk.shares = vim.SharesInfo()

                disks_facts[disk_index] = dict(
                    key=disk.key,
                    label=disk.deviceInfo.label,
                    summary=disk.deviceInfo.summary,
                    backing_filename=disk.backing.fileName,
                    backing_datastore=disk.backing.datastore.name,
                    backing_disk_mode=disk.backing.diskMode,
                    backing_sharing=disk.backing.sharing,
                    backing_uuid=disk.backing.uuid,
                    controller_key=disk.controllerKey,
                    unit_number=disk.unitNumber,
                    iolimit_limit=disk.storageIOAllocation.limit,
                    iolimit_shares_level=disk.storageIOAllocation.shares.level,
                    iolimit_shares_limit=disk.storageIOAllocation.shares.shares,
                    shares_level=disk.shares.level,
                    shares_limit=disk.shares.shares,
                    capacity_in_kb=disk.capacityInKB,
                    capacity_in_bytes=disk.capacityInBytes,
                )
                if isinstance(disk.backing, vim.vm.device.VirtualDisk.RawDiskMappingVer1BackingInfo):
                    disks_facts[disk_index].update(backing_devicename=disk.backing.deviceName,
                                                   backing_compatibility_mode=disk.backing.compatibilityMode)

                else:
                    disks_facts[disk_index].update(backing_writethrough=disk.backing.writeThrough,
                                                   backing_thinprovisioned=disk.backing.thinProvisioned,
                                                   backing_eagerlyscrub=bool(disk.backing.eagerlyScrub))
                disk_index += 1
        return disks_facts


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        name=dict(type='str'),
        uuid=dict(type='str'),
        moid=dict(type='str'),
        folder=dict(type='str'),
        datacenter=dict(type='str', required=True),
        use_instance_uuid=dict(type='bool', default=False),
        disk=dict(
            type='list',
            default=[],
            elements='dict',
            options=dict(
                size=dict(type='str'),
                size_kb=dict(type='int'),
                size_mb=dict(type='int'),
                size_gb=dict(type='int'),
                size_tb=dict(type='int'),
                type=dict(type='str', choices=['thin', 'eagerzeroedthick', 'thick', 'rdm']),
                disk_mode=dict(type='str', choices=['persistent', 'independent_persistent', 'independent_nonpersistent']),
                compatibility_mode=dict(type='str', choices=['physicalMode', 'virtualMode']),
                rdm_path=dict(type='str'),
                sharing=dict(type='bool', default=False),
                datastore=dict(type='str'),
                autoselect_datastore=dict(type='bool'),
                scsi_controller=dict(type='int', choices=[0, 1, 2, 3]),
                unit_number=dict(type='int', required=True),
                scsi_type=dict(type='str', choices=['buslogic', 'lsilogic', 'paravirtual', 'lsilogicsas']),
                destroy=dict(type='bool', default=True),
                filename=dict(type='str'),
                state=dict(type='str', default='present', choices=['present', 'absent']),
                controller_type=dict(type='str', choices=['buslogic', 'lsilogic', 'paravirtual', 'lsilogicsas', 'sata', 'nvme']),
                controller_number=dict(type='int', choices=[0, 1, 2, 3]),
                bus_sharing=dict(type='str', choices=['noSharing', 'physicalSharing', 'virtualSharing'], default='noSharing'),
                cluster_disk=dict(type='bool', default=False),
                iolimit=dict(
                    type='dict',
                    options=dict(
                        limit=dict(type='int'),
                        shares=dict(
                            type='dict',
                            options=dict(
                                level=dict(type='str', choices=['low', 'high', 'normal', 'custom']),
                                level_value=dict(type='int'),
                            ),
                        ),
                    )),
                shares=dict(
                    type='dict',
                    options=dict(
                        level=dict(type='str', choices=['low', 'high', 'normal', 'custom']),
                        level_value=dict(type='int'),
                    ),
                ),
            ),
        ),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=[['name', 'uuid', 'moid']],
    )

    if module.params['folder']:
        # FindByInventoryPath() does not require an absolute path
        # so we should leave the input folder path unmodified
        module.params['folder'] = module.params['folder'].rstrip('/')

    pyv = PyVmomiHelper(module)
    # Check if the VM exists before continuing
    vm = pyv.get_vm()

    if not vm:
        # We unable to find the virtual machine user specified
        # Bail out
        vm_id = (module.params.get('name') or module.params.get('uuid') or module.params.get('moid'))
        module.fail_json(msg="Unable to manage disks for non-existing"
                             " virtual machine '%s'." % vm_id)

    # VM exists
    try:
        pyv.ensure_disks(vm_obj=vm)
    except Exception as exc:
        module.fail_json(msg="Failed to manage disks for virtual machine"
                             " '%s' with exception : %s" % (vm.name,
                                                            to_native(exc)))


if __name__ == '__main__':
    main()

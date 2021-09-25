#!/usr/bin/python
#  -*- coding: utf-8 -*-
#  Copyright: (c) 2018, Ansible Project
#  Copyright: (c) 2018, Diane Wang <dianew@vmware.com>
#  GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: vmware_guest_vgpu
short_description: Modify vGPU video card profile of the specified virtual machine in the given vCenter infrastructure
description:
    - This module is used to reconfigure vGPU card profile of the given virtual machine.
    - All parameters and VMware object names are case sensitive.
    - VM must be power off M(community.vmware.vmware_guest) module can perform that task.
author:
    - Mohamed Alibi (@Medalibi)
    - Unknown (@matancarmeli7)
notes:
    - Tested on vSphere 6.7
requirements:
    - "python >= 3.6"
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
       - The folder should include the datacenter. ESXi server's datacenter is ha-datacenter.
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
     default: ha-datacenter
     description:
       - The datacenter name to which virtual machine belongs to.
       - This parameter is case sensitive.
     type: str
   state:
     default: present
     choices: [ 'present', 'absent' ]
     description:
       - vGPU profile state.
       - When C(state=present), the selected vGPU profile will be added if the VM hosted ESXi host Nvidia GPU offer it.
       - When C(state=absent), the selected vGPU profile gets removed from the VM.
     type: str
   vgpu:
     description:
       - Required for any operation.
     choices: [ 'grid_m10-8q', 'grid_m60-4q', 'grid_m10-2a' ]
     type: str
   force:
     description:
       - Force operation.
     default: False
     type: bool
   use_instance_uuid:
     description:
       - Whether to use the VMware instance UUID rather than the BIOS UUID.
     default: False
     type: bool
   cluster:
     description:
       - The cluster name where the virtual machine is running.
     type: str
   esxi_hostname:
     description:
       - The ESXi hostname where the virtual machine is running.
     type: str
extends_documentation_fragment:
- community.vmware.vmware.documentation
version_added: '1.9.0'
"""

EXAMPLES = r"""
- name: Add vGPU profile to VM
  community.vmware.vmware_guest_vgpu:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    datacenter: "{{ datacenter_name }}"
    validate_certs: no
    name: UbuntuTest
    vgpu: 'grid_m10-8q'
    state: present
  delegate_to: localhost
  register: vgpu_info

- name: Remove vGPU profile to VM
  community.vmware.vmware_guest_vgpu:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    datacenter: "{{ datacenter_name }}"
    validate_certs: no
    name: UbuntuTest
    vgpu: 'grid_m10-8q'
    state: absent
  delegate_to: localhost
  register: vgpu_info
"""

RETURN = r"""
vgpu_info:
    description: metadata about the virtual machine's vGPU profile
    returned: always
    type: dict
    sample: {
        "vgpu": {
            "Controller_Key": 100,
            "Key": 13000,
            "Label": "PCI device 0",
            "Summary": "NVIDIA GRID vGPU grid_m10-8q",
            "Unit_Number": 18,
            "Vgpu": "grid_m10-8q"
        }
    }
"""

try:
    from pyVmomi import vim
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.community.vmware.plugins.module_utils.vmware import (
    PyVmomi,
    vmware_argument_spec,
    wait_for_task,
)


class PyVmomiHelper(PyVmomi):
    def __init__(self, module):
        super(PyVmomiHelper, self).__init__(module)

    def _gather_vgpu_profile_facts(self, vm_obj):
        """
        Gather facts about VM's vGPU profile settings
        Args:
            vm_obj: Managed object of virtual machine
        Returns: vGPU profile and its facts
        """
        vgpu_info = dict()
        for vgpu_VirtualDevice_obj in vm_obj.config.hardware.device:
            if hasattr(vgpu_VirtualDevice_obj.backing, "vgpu"):
                vgpu_info = dict(
                    Vgpu=vgpu_VirtualDevice_obj.backing.vgpu,
                    Key=vgpu_VirtualDevice_obj.key,
                    Summary=vgpu_VirtualDevice_obj.deviceInfo.summary,
                    Label=vgpu_VirtualDevice_obj.deviceInfo.label,
                    Unit_Number=vgpu_VirtualDevice_obj.unitNumber,
                    Controller_Key=vgpu_VirtualDevice_obj.controllerKey,
                )
                break
        return vgpu_info

    def _vgpu_absent(self, vm_obj):
        """
        Remove vGPU profile of virtual machine.
        Args:
            vm_obj: Managed object of virtual machine
        Returns: Operation results and vGPU facts
        """
        result = {}
        vgpu_prfl = self.params["vgpu"]
        vgpu_VirtualDevice_obj = self._get_vgpu_VirtualDevice_object(vm_obj, vgpu_prfl)
        if vgpu_VirtualDevice_obj is None:
            changed = False
            failed = False
        else:
            vgpu_fact = self._gather_vgpu_profile_facts(vm_obj)
            changed, failed = self._remove_vgpu_profile_from_vm(
                vm_obj, vgpu_VirtualDevice_obj, vgpu_prfl
            )
        result = {"changed": changed, "failed": failed, "vgpu": vgpu_fact}
        return result

    def _remove_vgpu_profile_from_vm(self, vm_obj, vgpu_VirtualDevice_obj, vgpu_prfl):
        """
        Remove vGPU profile of virtual machine
        Args:
            vm_obj: Managed object of virtual machine
            vgpu_VirtualDevice_obj: vGPU profile object holding its facts
            vgpu_prfl: vGPU profile name
        Returns: Operation results
        """
        changed = False
        failed = False
        vm_current_vgpu_profile = self._get_vgpu_profile_in_the_vm(vm_obj)
        if vgpu_prfl in vm_current_vgpu_profile:
            vdspec = vim.vm.device.VirtualDeviceSpec()
            vmConfigSpec = vim.vm.ConfigSpec()
            vdspec.operation = "remove"
            vdspec.device = vgpu_VirtualDevice_obj
            vmConfigSpec.deviceChange.append(vdspec)

            try:
                task = vm_obj.ReconfigVM_Task(spec=vmConfigSpec)
                wait_for_task(task)
                changed = True
                return changed, failed
            except Exception as exc:
                failed = True
                self.module.fail_json(
                    msg="Failed to delete vGPU profile"
                    " '%s' from vm %s." % (vgpu_prfl, vm_obj.name),
                    detail=exc.msg,
                )
        return changed, failed

    def _vgpu_present(self, vm_obj):
        """
        Add vGPU profile to virtual machine.
        Args:
            vm_obj: Managed object of virtual machine
        Returns: Operation results and vGPU facts
        """
        result = {}
        vgpu_prfl = self.params["vgpu"]
        vgpu_profile_name = self._get_vgpu_profiles_name(vm_obj, vgpu_prfl)
        if vgpu_profile_name is None:
            self.module.fail_json(
                msg="vGPU Profile '%s'" " does not exist." % vgpu_prfl
            )

        changed, failed = self._add_vgpu_profile_to_vm(
            vm_obj, vgpu_profile_name, vgpu_prfl
        )
        vgpu_fact = self._gather_vgpu_profile_facts(vm_obj)
        result = {"changed": changed, "failed": failed, "vgpu": vgpu_fact}
        return result

    def _add_vgpu_profile_to_vm(self, vm_obj, vgpu_profile_name, vgpu_prfl):
        """
        Add vGPU profile of virtual machine
        Args:
            vm_obj: Managed object of virtual machine
            vgpu_profile_name: vGPU profile object name from ESXi server list
            vgpu_prfl: vGPU profile name
        Returns: Operation results
        """
        changed = False
        failed = False
        vm_current_vgpu_profile = self._get_vgpu_profile_in_the_vm(vm_obj)
        if self.params["force"] or vgpu_prfl not in vm_current_vgpu_profile:
            vgpu_p = vgpu_profile_name.vgpu
            backing = vim.VirtualPCIPassthroughVmiopBackingInfo(vgpu=vgpu_p)
            summary = "NVIDIA GRID vGPU " + vgpu_prfl
            deviceInfo = vim.Description(summary=summary, label="PCI device 0")
            hba_object = vim.VirtualPCIPassthrough(
                backing=backing, deviceInfo=deviceInfo
            )
            new_device_config = vim.VirtualDeviceConfigSpec(device=hba_object)
            new_device_config.operation = "add"
            vmConfigSpec = vim.vm.ConfigSpec()
            vmConfigSpec.deviceChange = [new_device_config]
            vmConfigSpec.memoryReservationLockedToMax = True

            try:
                task = vm_obj.ReconfigVM_Task(spec=vmConfigSpec)
                wait_for_task(task)
                changed = True
            except Exception as exc:
                failed = True
                self.module.fail_json(
                    msg="Failed to add vGPU Profile"
                    " '%s' to vm %s." % (vgpu_prfl, vm_obj.name),
                    detail=exc.msg,
                )
        else:
            return changed, failed
        return changed, failed

    def _get_vgpu_profile_in_the_vm(self, vm_obj):
        """
        Get vGPU profile object of virtual machine
        Args:
            vm_obj: Managed object of virtual machine
        Returns: vGPU profile name
        """
        vm_current_vgpu_profile = []
        for vgpu_VirtualDevice_obj in vm_obj.config.hardware.device:
            if hasattr(vgpu_VirtualDevice_obj.backing, "vgpu"):
                vm_current_vgpu_profile.append(vgpu_VirtualDevice_obj.backing.vgpu)
        return vm_current_vgpu_profile

    def _get_vgpu_VirtualDevice_object(self, vm_obj, vgpu_prfl):
        """
        Get current vGPU profile object of virtual machine
        Args:
            vm_obj: Managed object of virtual machine
            vgpu_prfl: vGPU profile name
        Returns: vGPU profile name of virtual machine
        """
        for vgpu_VirtualDevice_obj in vm_obj.config.hardware.device:
            if hasattr(vgpu_VirtualDevice_obj.backing, "vgpu"):
                if vgpu_VirtualDevice_obj.backing.vgpu == vgpu_prfl:
                    return vgpu_VirtualDevice_obj
        return None

    def _get_vgpu_profiles_name(self, vm_obj, vgpu_prfl):
        """
        Get matched vGPU profile object of ESXi host
        Args:
            vm_obj: Managed object of virtual machine
            vgpu_prfl: vGPU profile name
        Returns: vGPU profile object
        """
        vm_host = vm_obj.runtime.host
        vgpu_profiles = vm_host.config.sharedGpuCapabilities
        for vgpu_profile_name in vgpu_profiles:
            if vgpu_profile_name.vgpu == vgpu_prfl:
                return vgpu_profile_name
        return None


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        name=dict(type="str"),
        uuid=dict(type="str"),
        use_instance_uuid=dict(type="bool", default=False),
        moid=dict(type="str"),
        folder=dict(type="str"),
        datacenter=dict(type="str", default="ha-datacenter"),
        esxi_hostname=dict(type="str"),
        cluster=dict(type="str"),
        vgpu=dict(type="str", choices=["grid_m10-8q", "grid_m60-4q", "grid_m10-2a"]),
        force=dict(type="bool", default=False),
        state=dict(type="str", default="present", choices=["absent", "present"]),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        mutually_exclusive=[["cluster", "esxi_hostname"]],
        required_one_of=[["name", "uuid", "moid"]],
    )

    pyv = PyVmomiHelper(module)
    vm = pyv.get_vm()

    if not vm:
        vm_id = (
            module.params.get("uuid")
            or module.params.get("name")
            or module.params.get("moid")
        )
        module.fail_json(
            msg="Unable to manage vGPU profile for non-existing VM %s" % vm_id
        )

    if module.params["state"] == "present":
        result = pyv._vgpu_present(vm)
    elif module.params["state"] == "absent":
        result = pyv._vgpu_absent(vm)

    if "failed" not in result:
        result["failed"] = False

    if result["failed"]:
        module.fail_json(**result)
    else:
        module.exit_json(**result)


if __name__ == "__main__":
    main()

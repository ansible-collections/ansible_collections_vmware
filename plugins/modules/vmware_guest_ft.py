#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

DOCUMENTATION = r'''
module: vmware_guest_ft
short_description: Fault Tolerance for specified VM.
description: This module is used for enable or disable the Fault Tolerance for an existing  Virtual Machine.
author:
     - Christian Neugum (@digifuchsi)
     - Valentin Yonev (@valentinJonev)
notes:
    - Tested on vSphere 5.5, 6.5, 7.0
requirements:
    - "python >= 2.6"
    - PyVmomi
options:
    virtual_machine_name:
        description: Name of the Virtual Machine
        type: str
        required: True
    state:
        description:
        - present - represents that Fault Tolerance should be enabled
        - absent - disables the Fault Tolerance
        choices: [ present, absent ]
        default: present
        type: str
'''

EXAMPLES = r'''
- name: enable FT on VM
  vmware_guest_ft:
    virtual_machine_name: VM1
    state: present
  delegate_to: localhost
'''

import time

__metaclass__ = type


try:
    from pyVim.task import WaitForTask
    from pyVmomi import vim, vmodl, PyVmomi
    # from tools import tasks
    from ansible.module_utils._text import to_native
except ImportError as e:
    raise e

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.community.vmware.plugins.module_utils.vmware import (vmware_argument_spec, find_object_by_name, wait_for_task)


class VMwareFTManagement(PyVmomi):

    def __init__(self, module):
        super(VMwareFTManagement, self).__init__(module)
        self.vm_name = module.params['virtual_machine_name']
        self.state = module.params['state']
        self.disable_error_msg = None
        self.counter = 0

    def process_state(self):
        ft_state = {
            'absent': self.execute_disable_ft,

            'present': self.enable_ft
        }

        try:
            ft_state[self.state]()
        except vmodl.RuntimeFault as runtime_fault:
            self.module.fail_json(msg=to_native(runtime_fault.msg))
        except vmodl.MethodFault as method_fault:
            self.module.fail_json(msg=to_native(method_fault.msg))
        except Exception as e:
            self.module.fail_json(msg=to_native(e))

    def find_vm_by_name(self, content, vm_name, folder=None, recurse=True):
        return find_object_by_name(content, vm_name, [vim.VirtualMachine], folder=folder, recurse=recurse)

    def _wait_for_task(self, task, error_msg=None):
        while task.info.state not in [vim.TaskInfo.State.success,
                                      vim.TaskInfo.State.error]:
            time.sleep(.1)
        if task.info.state == vim.TaskInfo.State.error:
            self.module.fail_json(msg=error_msg)

    def execute_disable_ft(self):
        while True:
            result = self.disable_ft()
            if result:
                self.module.exit_json(changed=True, msg="Successfully disabled FT for VM")

    def disable_ft(self, vm=None):
        try:
            if not vm:
                vm = self.find_vm_by_name(self.content, self.vm_name)
            # Role = 1 refers to the main VM, Role = 2 refers to the secondary VM
            if vm.config.ftInfo.role != 1:
                vm = vm.config.ftInfo.primaryVM

            task = vm.TurnOffFaultToleranceForVM_Task()
            wait_for_task(task)
            return True

        except Exception:
            if self.counter >= 3:
                self.module.fail_json(msg='Unable to disable FT for VM. Please check error logs for more details')
            time.sleep(15)
            self.counter += 1
            return self.disable_ft(vm)

    def enable_ft(self):

        vm = self.find_vm_by_name(self.content, self.vm_name)

        try:
            task = vm.CreateSecondaryVMEx_Task()
            self._wait_for_task(task, "Could not enable FT for VM")

            for task in vm.recentTask:
                if task.info.descriptionId == 'FaultTolerance.PowerOnSecondaryLRO':
                    WaitForTask(task)

            self.module.exit_json(changed=True, msg="Successfully enabled FT for VM")
        except Exception as e:
            self.module.fail_json(msg='Unable to set FT for VM. Error: {}'.format(e))


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(dict(
                         virtual_machine_name=dict(required=True, type='str'),
                         validate_certs=dict(required=False, type='bool', default=False),
                         state=dict(default='present',
                                    choices=['present', 'absent'],
                                    type='str')
                         )
                         )

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    manager = VMwareFTManagement(module)
    manager.process_state()


if __name__ == '__main__':
    main()

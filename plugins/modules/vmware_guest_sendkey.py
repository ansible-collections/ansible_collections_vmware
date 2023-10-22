#!/usr/bin/python
#  -*- coding: utf-8 -*-

# Copyright: (c) 2018, Ansible Project
# Copyright: (c) 2018, Diane Wang <dianew@vmware.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: vmware_guest_sendkey
short_description: Send USB HID codes to the Virtual Machine's keyboard.
description:
    - This module is used to send keystrokes to given virtual machine.
    - All parameters and VMware object names are case sensitive.
author:
    - Diane Wang (@Tomorrow9) <dianew@vmware.com>
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
   cluster:
     description:
     - The name of cluster where the virtual machine is running.
     - This is a required parameter, if C(esxi_hostname) is not set.
     - C(esxi_hostname) and C(cluster) are mutually exclusive parameters.
     type: str
   esxi_hostname:
     description:
     - The ESXi hostname where the virtual machine is running.
     - This is a required parameter, if C(cluster) is not set.
     - C(esxi_hostname) and C(cluster) are mutually exclusive parameters.
     type: str
   datacenter:
     description:
     - The datacenter name to which virtual machine belongs to.
     type: str
   string_send:
     description:
     - The string will be sent to the virtual machine.
     - This string can contain valid special character, alphabet and digit on the keyboard.
     - 'C(<WAIT>) special string: add an arbitrary pause before sending any additional keys.'
     - Use C(<WAIT>), C(<WAITxx>) and C(<WAITxxT>) , where xx = integer and T is s, m or h for seconds, minutes and hours of pause respectively.
     - You can add any type of C(keys_send) value between C('<>') too.
     - 'Example: 123<RETURN><WAIT>testing<WAIT><RETURN><WAIT1m>.'
     - 'Escape by adding C(\) in front of key: C(\)<WAIT> C(\)<TAB>.'
     type: str
   keys_send:
     description:
     - The list of the keys will be sent to the virtual machine.
     - 'Valid values are C(ENTER), C(ESC), C(BACKSPACE), C(TAB), C(SPACE), C(CAPSLOCK), C(HOME), C(DELETE), C(END), C(CTRL_ALT_DEL),
        C(CTRL_C), C(CTRL_X) and C(F1) to C(F12), C(RIGHTARROW), C(LEFTARROW), C(DOWNARROW), C(UPARROW).'
     - If both C(keys_send) and C(string_send) are specified, keys in C(keys_send) list will be sent in front of the C(string_send).
     - Values C(HOME) and C(END) are added in version 1.17.0.
     type: list
     default: []
     elements: str
   strings_send:
     description:
     - A list of strings will be sent to the virtual machine.
     - If both C(string_send) and C(strings_send) are specified, keys in C(string_send) will be sent in front of the C(strings_send) list.
     type: list
     elements: str
   sleep_time:
     description:
     - Sleep time in seconds ( or fraction of seconds ) between two keys or string sent to the virtual machine.
     - API is faster than actual key or string send to virtual machine, this parameter allow to control
       delay between keys and/or strings.
     type: float
     default: 0
extends_documentation_fragment:
- community.vmware.vmware.documentation

'''

EXAMPLES = r'''
- name: Send list of keys to virtual machine
  community.vmware.vmware_guest_sendkey:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    datacenter: "{{ datacenter_name }}"
    folder: "{{ folder_name }}"
    name: "{{ vm_name }}"
    keys_send:
      - TAB
      - TAB
      - ENTER
  delegate_to: localhost
  register: keys_num_sent

- name: Send list of keys to virtual machine using MoID
  community.vmware.vmware_guest_sendkey:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    datacenter: "{{ datacenter_name }}"
    folder: "{{ folder_name }}"
    moid: vm-42
    keys_send:
      - CTRL_ALT_DEL
  delegate_to: localhost
  register: ctrl_alt_del_sent

- name: Send a string to virtual machine
  community.vmware.vmware_guest_sendkey:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    datacenter: "{{ datacenter_name }}"
    folder: "{{ folder_name }}"
    name: "{{ vm_name }}"
    string_send: "user_logon"
  delegate_to: localhost
  register: keys_num_sent

- name: Send a list of strings to virtual machine
  community.vmware.vmware_guest_sendkey:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    datacenter: "{{ datacenter_name }}"
    folder: "{{ folder_name }}"
    name: "{{ vm_name }}"
    strings_send:
      - "user_logon"
      - "<WAIT2s><ENTER>"
      - "<TAB>"
      - "<NONKEY>\\<TAB>SOMETHING<ENTER>"
  delegate_to: localhost
  register: keys_num_sent
'''

RETURN = r'''
sendkey_info:
    description: display the keys and the number of keys sent to the virtual machine
    returned: always
    type: dict
    sample: {
            "virtual_machine": "test_vm",
            "keys_send": [
                "SPACE",
                "DOWNARROW",
                "DOWNARROW",
                "ENTER"
            ],
            "string_send": null,
            "keys_send_number": 4,
            "returned_keys_send_number": 4,
    }
'''

import time
import re
try:
    from pyVmomi import vim, vmodl
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible_collections.community.vmware.plugins.module_utils.vmware import PyVmomi, vmware_argument_spec


class PyVmomiHelper(PyVmomi):
    def __init__(self, module):
        super(PyVmomiHelper, self).__init__(module)
        self.change_detected = False
        self.num_keys_send = 0
        # HID usage tables https://www.usb.org/sites/default/files/documents/hut1_12v2.pdf
        # define valid characters and keys value, hex_code, key value and key modifier
        self.keys_hid_code = [
            (('a', 'A'), '0x04', [('a', []), ('A', ['LEFTSHIFT'])]),
            (('b', 'B'), '0x05', [('b', []), ('B', ['LEFTSHIFT'])]),
            (('c', 'C'), '0x06', [('c', []), ('C', ['LEFTSHIFT'])]),
            (('d', 'D'), '0x07', [('d', []), ('D', ['LEFTSHIFT'])]),
            (('e', 'E'), '0x08', [('e', []), ('E', ['LEFTSHIFT'])]),
            (('f', 'F'), '0x09', [('f', []), ('F', ['LEFTSHIFT'])]),
            (('g', 'G'), '0x0a', [('g', []), ('G', ['LEFTSHIFT'])]),
            (('h', 'H'), '0x0b', [('h', []), ('H', ['LEFTSHIFT'])]),
            (('i', 'I'), '0x0c', [('i', []), ('I', ['LEFTSHIFT'])]),
            (('j', 'J'), '0x0d', [('j', []), ('J', ['LEFTSHIFT'])]),
            (('k', 'K'), '0x0e', [('k', []), ('K', ['LEFTSHIFT'])]),
            (('l', 'L'), '0x0f', [('l', []), ('L', ['LEFTSHIFT'])]),
            (('m', 'M'), '0x10', [('m', []), ('M', ['LEFTSHIFT'])]),
            (('n', 'N'), '0x11', [('n', []), ('N', ['LEFTSHIFT'])]),
            (('o', 'O'), '0x12', [('o', []), ('O', ['LEFTSHIFT'])]),
            (('p', 'P'), '0x13', [('p', []), ('P', ['LEFTSHIFT'])]),
            (('q', 'Q'), '0x14', [('q', []), ('Q', ['LEFTSHIFT'])]),
            (('r', 'R'), '0x15', [('r', []), ('R', ['LEFTSHIFT'])]),
            (('s', 'S'), '0x16', [('s', []), ('S', ['LEFTSHIFT'])]),
            (('t', 'T'), '0x17', [('t', []), ('T', ['LEFTSHIFT'])]),
            (('u', 'U'), '0x18', [('u', []), ('U', ['LEFTSHIFT'])]),
            (('v', 'V'), '0x19', [('v', []), ('V', ['LEFTSHIFT'])]),
            (('w', 'W'), '0x1a', [('w', []), ('W', ['LEFTSHIFT'])]),
            (('x', 'X'), '0x1b', [('x', []), ('X', ['LEFTSHIFT'])]),
            (('y', 'Y'), '0x1c', [('y', []), ('Y', ['LEFTSHIFT'])]),
            (('z', 'Z'), '0x1d', [('z', []), ('Z', ['LEFTSHIFT'])]),
            (('1', '!'), '0x1e', [('1', []), ('!', ['LEFTSHIFT'])]),
            (('2', '@'), '0x1f', [('2', []), ('@', ['LEFTSHIFT'])]),
            (('3', '#'), '0x20', [('3', []), ('#', ['LEFTSHIFT'])]),
            (('4', '$'), '0x21', [('4', []), ('$', ['LEFTSHIFT'])]),
            (('5', '%'), '0x22', [('5', []), ('%', ['LEFTSHIFT'])]),
            (('6', '^'), '0x23', [('6', []), ('^', ['LEFTSHIFT'])]),
            (('7', '&'), '0x24', [('7', []), ('&', ['LEFTSHIFT'])]),
            (('8', '*'), '0x25', [('8', []), ('*', ['LEFTSHIFT'])]),
            (('9', '('), '0x26', [('9', []), ('(', ['LEFTSHIFT'])]),
            (('0', ')'), '0x27', [('0', []), (')', ['LEFTSHIFT'])]),
            (('-', '_'), '0x2d', [('-', []), ('_', ['LEFTSHIFT'])]),
            (('=', '+'), '0x2e', [('=', []), ('+', ['LEFTSHIFT'])]),
            (('[', '{'), '0x2f', [('[', []), ('{', ['LEFTSHIFT'])]),
            ((']', '}'), '0x30', [(']', []), ('}', ['LEFTSHIFT'])]),
            (('\\', '|'), '0x31', [('\\', []), ('|', ['LEFTSHIFT'])]),
            ((';', ':'), '0x33', [(';', []), (':', ['LEFTSHIFT'])]),
            (('\'', '"'), '0x34', [('\'', []), ('"', ['LEFTSHIFT'])]),
            (('`', '~'), '0x35', [('`', []), ('~', ['LEFTSHIFT'])]),
            ((',', '<'), '0x36', [(',', []), ('<', ['LEFTSHIFT'])]),
            (('.', '>'), '0x37', [('.', []), ('>', ['LEFTSHIFT'])]),
            (('/', '?'), '0x38', [('/', []), ('?', ['LEFTSHIFT'])]),
            ('ENTER', '0x28', [('', [])]),
            ('ESC', '0x29', [('', [])]),
            ('BACKSPACE', '0x2a', [('', [])]),
            ('TAB', '0x2b', [('', [])]),
            ('SPACE', '0x2c', [(' ', [])]),
            ('CAPSLOCK', '0x39', [('', [])]),
            ('F1', '0x3a', [('', [])]),
            ('F2', '0x3b', [('', [])]),
            ('F3', '0x3c', [('', [])]),
            ('F4', '0x3d', [('', [])]),
            ('F5', '0x3e', [('', [])]),
            ('F6', '0x3f', [('', [])]),
            ('F7', '0x40', [('', [])]),
            ('F8', '0x41', [('', [])]),
            ('F9', '0x42', [('', [])]),
            ('F10', '0x43', [('', [])]),
            ('F11', '0x44', [('', [])]),
            ('F12', '0x45', [('', [])]),
            ('HOME', '0x4a', [('', [])]),
            ('DELETE', '0x4c', [('', [])]),
            ('END', '0x4d', [('', [])]),
            ('CTRL_ALT_DEL', '0x4c', [('', ['CTRL', 'ALT'])]),
            ('CTRL_C', '0x06', [('', ['CTRL'])]),
            ('CTRL_X', '0x1b', [('', ['CTRL'])]),
            ('RIGHTARROW', '0x4f', [('', [])]),
            ('LEFTARROW', '0x50', [('', [])]),
            ('DOWNARROW', '0x51', [('', [])]),
            ('UPARROW', '0x52', [('', [])]),
        ]

    @staticmethod
    def hid_to_hex(hid_code):
        return int(hid_code, 16) << 16 | 0o0007

    def get_hid_from_key(self, key):
        if key == ' ':
            return '0x2c', []
        for keys_name, key_code, keys_value in self.keys_hid_code:
            if isinstance(keys_name, tuple):
                for keys in keys_value:
                    if key == keys[0]:
                        return key_code, keys[1]
            else:
                if key == keys_name:
                    return key_code, keys_value[0][1]

    def get_key_event(self, hid_code, modifiers):
        key_event = vim.UsbScanCodeSpecKeyEvent()
        key_modifier = vim.UsbScanCodeSpecModifierType()
        key_modifier.leftAlt = False
        key_modifier.leftControl = False
        key_modifier.leftGui = False
        key_modifier.leftShift = False
        key_modifier.rightAlt = False
        key_modifier.rightControl = False
        key_modifier.rightGui = False
        key_modifier.rightShift = False
        # rightShift, rightControl, rightAlt, leftGui, rightGui are not used
        if "LEFTSHIFT" in modifiers:
            key_modifier.leftShift = True
        if "CTRL" in modifiers:
            key_modifier.leftControl = True
        if "ALT" in modifiers:
            key_modifier.leftAlt = True
        key_event.modifiers = key_modifier
        key_event.usbHidCode = self.hid_to_hex(hid_code)

        return key_event

    def get_sendkey_facts(self, vm_obj, returned_value=0):
        sendkey_facts = dict()
        if vm_obj is not None:
            sendkey_facts = dict(
                virtual_machine=vm_obj.name,
                keys_send=self.params['keys_send'],
                string_send=self.params['string_send'],
                keys_send_number=self.num_keys_send,
                returned_keys_send_number=returned_value,
            )

        return sendkey_facts

    def send_key_events(self, vm_obj, key_queue, sleep_time=0):
        """
        Send USB HID Scan codes individually to prevent dropping or cobblering
        """
        send_keys = 0
        for item in key_queue:
            if isinstance(item, (str,)):
                match = re.match(r"^WAIT($|([0-9]+)(h|m|s|$))", item)
                if match:
                    wtime = int(match.groups()[1]) if (match.groups()[1]) else 1
                    wtype = match.groups()[2]
                    if wtype:
                        if wtype == 's':
                            pass
                        elif (wtype == 'h'):
                            wtime *= 3600
                        elif (wtype == 'm'):
                            wtime *= 60
                        else:
                            self.module.fail_json(msg="value %s in <%s> should be absent or 'h' or 'm' ." % (wtype, item))
                    time.sleep(wtime)
                else:
                    self.module.fail_json(msg="value of %s should be a <WAIT*> statement." % (item))
            else:
                usb_spec = vim.UsbScanCodeSpec()
                usb_spec.keyEvents.append(item)
                send_keys += vm_obj.PutUsbScanCodes(usb_spec)
                # Sleep in between key / string send event
                time.sleep(sleep_time)
        return send_keys

    def send_key_to_vm(self, vm_obj):
        key_event = None
        num_keys_returned = 0
        key_queue = []
        if self.params['keys_send']:
            for specified_key in self.params['keys_send']:
                key_found = False
                for keys in self.keys_hid_code:
                    if (isinstance(keys[0], tuple) and specified_key in keys[0]) or \
                            (not isinstance(keys[0], tuple) and specified_key == keys[0]):
                        hid_code, modifiers = self.get_hid_from_key(specified_key)
                        key_event = self.get_key_event(hid_code, modifiers)
                        key_queue.append(key_event)
                        self.num_keys_send += 1
                        key_found = True
                        break
                if not key_found:
                    self.module.fail_json(msg="keys_send parameter: '%s' in %s not supported."
                                              % (specified_key, self.params['keys_send']))

        if self.params['string_send']:
            self.params['strings_send'].insert(0, self.params['string_send'])

        if self.params['strings_send']:
            for str_item in self.params['strings_send']:
                for str_part in re.split(r'(\\?\<\w+\>)', str_item):
                    str_special = re.match(r'^(\<\w+\>)', str_part)
                    if (str_special):
                        str_replaced = re.sub(r'^\<(\w+)\>', r'\1', str_special.group())
                        if (str_replaced.startswith("WAIT")):
                            key_queue.append(str_replaced)
                            continue
                        else:
                            # code reused from keys_send... is there a better approach?
                            key_found = False
                            for keys in self.keys_hid_code:
                                if (isinstance(keys[0], tuple) and str_replaced in keys[0]) or \
                                        (not isinstance(keys[0], tuple) and str_replaced == keys[0]):
                                    hid_code, modifiers = self.get_hid_from_key(str_replaced)
                                    key_event = self.get_key_event(hid_code, modifiers)
                                    key_queue.append(key_event)
                                    self.num_keys_send += 1
                                    key_found = True
                                    break
                            if not key_found:
                                self.module.fail_json(msg="string(s)_send(keys_send) parameter: '%s' in %s not supported."
                                                          % (str_replaced, str_special))
                    else:
                        fixed_str = re.sub(r'^\\(\<)', r'\1', str_part)
                        for char in fixed_str:
                            key_found = False
                            for keys in self.keys_hid_code:
                                if (isinstance(keys[0], tuple) and char in keys[0]) or char == ' ':
                                    hid_code, modifiers = self.get_hid_from_key(char)
                                    key_event = self.get_key_event(hid_code, modifiers)
                                    key_queue.append(key_event)
                                    self.num_keys_send += 1
                                    key_found = True
                                    break
                            if not key_found:
                                self.module.fail_json(msg="string(s)_send parameter: '%s' contains char: '%s' not supported."
                                                          % (fixed_str, char))

        if key_queue:
            try:
                num_keys_returned = self.send_key_events(vm_obj=vm_obj, key_queue=key_queue, sleep_time=self.module.params.get('sleep_time'))
                self.change_detected = True
            except vmodl.RuntimeFault as e:
                self.module.fail_json(msg="Failed to send key %s to virtual machine due to %s" % (key_event, to_native(e.msg)))

        sendkey_facts = self.get_sendkey_facts(vm_obj, num_keys_returned)
        if num_keys_returned != self.num_keys_send:
            results = {'changed': self.change_detected, 'failed': True, 'sendkey_info': sendkey_facts}
        else:
            results = {'changed': self.change_detected, 'failed': False, 'sendkey_info': sendkey_facts}

        return results


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        name=dict(type='str'),
        uuid=dict(type='str'),
        moid=dict(type='str'),
        folder=dict(type='str'),
        datacenter=dict(type='str'),
        esxi_hostname=dict(type='str'),
        cluster=dict(type='str'),
        keys_send=dict(type='list', default=[], elements='str', no_log=False),
        string_send=dict(type='str'),
        strings_send=dict(type='list', default=[], elements='str', no_log=False),
        sleep_time=dict(type='float', default=0),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=[
            ['name', 'uuid', 'moid']
        ]
    )

    pyv = PyVmomiHelper(module)
    vm = pyv.get_vm()
    if not vm:
        vm_id = (module.params.get('uuid') or module.params.get('name') or module.params.get('moid'))
        module.fail_json(msg='Unable to find the specified virtual machine : %s ' % vm_id)

    result = pyv.send_key_to_vm(vm)
    if result['failed']:
        module.fail_json(**result)
    module.exit_json(**result)


if __name__ == '__main__':
    main()

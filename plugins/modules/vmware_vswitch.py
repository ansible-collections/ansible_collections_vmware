#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2015, Joseph Callen <jcallen () csc.com>
# Copyright: (c) 2018, Ansible Project
# Copyright: (c) 2018, Abhijeet Kasurde <akasurde@redhat.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: vmware_vswitch
short_description: Manage a VMware Standard Switch to an ESXi host.
description:
- This module can be used to add, remove and update a VMware Standard Switch to an ESXi host.
author:
- Joseph Callen (@jcpowermac)
- Russell Teague (@mtnbikenc)
- Abhijeet Kasurde (@Akasurde) <akasurde@redhat.com>
options:
  switch:
    description:
    - vSwitch name to add.
    required: true
    aliases: [ switch_name ]
    type: str
  nics:
    description:
    - A list of vmnic names or vmnic name to attach to vSwitch.
    aliases: [ nic_name ]
    default: []
    type: list
    elements: str
  number_of_ports:
    description:
    - Number of port to configure on vSwitch.
    default: 128
    type: int
  mtu:
    description:
    - MTU to configure on vSwitch.
    default: 1500
    type: int
  state:
    description:
    - Add or remove the switch.
    default: present
    choices: [ absent, present ]
    type: str
  esxi_hostname:
    description:
    - Manage the vSwitch using this ESXi host system.
    aliases: [ 'host' ]
    type: str
  security:
    description:
    - Network policy specifies layer 2 security settings for a
      portgroup such as promiscuous mode, where guest adapter listens
      to all the packets, MAC address changes and forged transmits.
    - Dict which configures the different security values for portgroup.
    suboptions:
      promiscuous_mode:
        type: bool
        description: Indicates whether promiscuous mode is allowed.
      forged_transmits:
        type: bool
        description: Indicates whether forged transmits are allowed.
      mac_changes:
        type: bool
        description: Indicates whether mac changes are allowed.
    required: false
    aliases: [ 'security_policy', 'network_policy' ]
    type: dict
  teaming:
    description:
      - Dictionary which configures the different teaming values for portgroup.
    suboptions:
      load_balancing:
        type: str
        description:
        - Network adapter teaming policy.
        choices: [ loadbalance_ip, loadbalance_srcmac, loadbalance_srcid, failover_explicit ]
        aliases: [ 'load_balance_policy' ]
      network_failure_detection:
        type: str
        description: Network failure detection.
        choices: [ link_status_only, beacon_probing ]
      notify_switches:
        type: bool
        description: Indicate whether or not to notify the physical switch if a link fails.
      failback:
        type: bool
        description: Indicate whether or not to use a failback when restoring links.
      active_adapters:
        type: list
        description:
        - List of active adapters used for load balancing.
        - All vmnics are used as active adapters if O(teaming.active_adapters) and O(teaming.standby_adapters) are not defined.
        elements: str
      standby_adapters:
        type: list
        description:
        - List of standby adapters used for failover.
        - All vmnics are used as active adapters if O(teaming.active_adapters) and O(teaming.standby_adapters) are not defined.
        elements: str
    required: false
    aliases: [ 'teaming_policy' ]
    type: dict
  traffic_shaping:
    description:
      - Dictionary which configures traffic shaping for the switch.
    suboptions:
      enabled:
        type: bool
        description: Status of Traffic Shaping Policy.
      average_bandwidth:
        type: int
        description: Average bandwidth (kbit/s).
      peak_bandwidth:
        type: int
        description: Peak bandwidth (kbit/s).
      burst_size:
        type: int
        description: Burst size (KB).
    required: false
    type: dict
extends_documentation_fragment:
- community.vmware.vmware.documentation

'''

EXAMPLES = r'''
- name: Add a VMware vSwitch
  community.vmware.vmware_vswitch:
    hostname: '{{ esxi_hostname }}'
    username: '{{ esxi_username }}'
    password: '{{ esxi_password }}'
    switch: vswitch_name
    nics: vmnic_name
    mtu: 9000
  delegate_to: localhost

- name: Add a VMware vSwitch without any physical NIC attached
  community.vmware.vmware_vswitch:
    hostname: '{{ esxi_hostname }}'
    username: '{{ esxi_username }}'
    password: '{{ esxi_password }}'
    switch: vswitch_0001
    mtu: 9000
  delegate_to: localhost

- name: Add a VMware vSwitch with multiple NICs
  community.vmware.vmware_vswitch:
    hostname: '{{ esxi_hostname }}'
    username: '{{ esxi_username }}'
    password: '{{ esxi_password }}'
    switch: vmware_vswitch_0004
    nics:
    - vmnic1
    - vmnic2
    mtu: 9000
  delegate_to: localhost

- name: Add a VMware vSwitch to a specific host system
  community.vmware.vmware_vswitch:
    hostname: '{{ esxi_hostname }}'
    username: '{{ esxi_username }}'
    password: '{{ esxi_password }}'
    esxi_hostname: DC0_H0
    switch_name: vswitch_001
    nic_name: vmnic0
    mtu: 9000
  delegate_to: localhost

- name: Add a VMware vSwitch to a specific host system with Promiscuous Mode Enabled
  community.vmware.vmware_vswitch:
    hostname: '{{ esxi_hostname }}'
    username: '{{ esxi_username }}'
    password: '{{ esxi_password }}'
    esxi_hostname: DC0_H0
    switch_name: vswitch_001
    nic_name: vmnic0
    mtu: 9000
    security:
        promiscuous_mode: true
  delegate_to: localhost

- name: Add a VMware vSwitch to a specific host system with active/standby teaming
  community.vmware.vmware_vswitch:
    hostname: '{{ esxi_hostname }}'
    username: '{{ esxi_username }}'
    password: '{{ esxi_password }}'
    esxi_hostname: DC0_H0
    switch_name: vswitch_001
    nic_name:
      - vmnic0
      - vmnic1
    teaming:
      active_adapters:
        - vmnic0
      standby_adapters:
        - vmnic1
  delegate_to: localhost

- name: Add a VMware vSwitch to a specific host system with traffic shaping
  community.vmware.vmware_vswitch:
    hostname: '{{ esxi_hostname }}'
    username: '{{ esxi_username }}'
    password: '{{ esxi_password }}'
    esxi_hostname: DC0_H0
    switch_name: vswitch_001
    nic_name:
      - vmnic0
      - vmnic1
    traffic_shaping:
        enabled: true
        average_bandwidth: 100000
        peak_bandwidth: 100000
        burst_size: 102400
  delegate_to: localhost

- name: Delete a VMware vSwitch in a specific host system
  community.vmware.vmware_vswitch:
    hostname: '{{ esxi_hostname }}'
    username: '{{ esxi_username }}'
    password: '{{ esxi_password }}'
    esxi_hostname: DC0_H0
    switch_name: vswitch_001
    state: absent
  delegate_to: localhost
'''

RETURN = r'''
result:
    description: information about performed operation
    returned: always
    type: str
    sample: "vSwitch 'vSwitch_1002' is created successfully"
'''

try:
    from pyVmomi import vim, vmodl
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.community.vmware.plugins.module_utils.vmware import PyVmomi, vmware_argument_spec
from ansible.module_utils._text import to_native


# Meaningless diff with no code changes to trigger CI

class VMwareHostVirtualSwitch(PyVmomi):
    def __init__(self, module):
        super(VMwareHostVirtualSwitch, self).__init__(module)
        self.host_system = None
        self.vss = None
        self.switch = module.params['switch']
        self.number_of_ports = module.params['number_of_ports']
        self.nics = module.params['nics']
        self.mtu = module.params['mtu']
        self.state = module.params['state']
        esxi_hostname = module.params['esxi_hostname']

        hosts = self.get_all_host_objs(esxi_host_name=esxi_hostname)
        if hosts:
            self.host_system = hosts[0]
        else:
            self.module.fail_json(msg="Failed to get details of ESXi server."
                                      " Please specify esxi_hostname.")

        self.network_mgr = self.host_system.configManager.networkSystem
        if not self.network_mgr:
            self.module.fail_json(msg="Failed to find network manager for ESXi system.")

        if self.params.get('state') == 'present':
            # Gather information about all vSwitches and Physical NICs
            available_pnic = [pnic.device for pnic in self.network_mgr.networkInfo.pnic]
            self.available_vswitches = dict()
            for available_vswitch in self.network_mgr.networkInfo.vswitch:
                used_pnic = []
                for pnic in available_vswitch.pnic:
                    # vSwitch contains all PNICs as string in format of 'key-vim.host.PhysicalNic-vmnic0'
                    m_pnic = pnic.split("-", 3)[-1]
                    used_pnic.append(m_pnic)
                self.available_vswitches[available_vswitch.name] = dict(pnic=used_pnic,
                                                                        mtu=available_vswitch.mtu,
                                                                        num_ports=available_vswitch.spec.numPorts,
                                                                        )
            for desired_pnic in self.nics:
                if desired_pnic not in available_pnic:
                    # Check if pnic does not exists
                    self.module.fail_json(msg="Specified Physical NIC '%s' does not"
                                              " exists on given ESXi '%s'." % (desired_pnic,
                                                                               self.host_system.name))
                for vswitch in self.available_vswitches:
                    if desired_pnic in self.available_vswitches[vswitch]['pnic'] and vswitch != self.switch:
                        # Check if pnic is already part of some other vSwitch
                        self.module.fail_json(msg="Specified Physical NIC '%s' is already used"
                                                  " by vSwitch '%s'." % (desired_pnic, vswitch))

    def process_state(self):
        """
        Manage internal state of vSwitch
        """
        vswitch_states = {
            'absent': {
                'present': self.state_destroy_vswitch,
                'absent': self.state_exit_unchanged,
            },
            'present': {
                'present': self.state_update_vswitch,
                'absent': self.state_create_vswitch,
            }
        }

        try:
            vswitch_states[self.state][self.check_vswitch_configuration()]()
        except vmodl.RuntimeFault as runtime_fault:
            self.module.fail_json(msg=to_native(runtime_fault.msg))
        except vmodl.MethodFault as method_fault:
            self.module.fail_json(msg=to_native(method_fault.msg))
        except Exception as e:
            self.module.fail_json(msg=to_native(e))

    def state_create_vswitch(self):
        """
        Create a virtual switch

        Source from
        https://github.com/rreubenur/pyvmomi-community-samples/blob/patch-1/samples/create_vswitch.py

        """

        results = dict(changed=False, result="")
        vss_spec = vim.host.VirtualSwitch.Specification()
        vss_spec.numPorts = self.number_of_ports
        vss_spec.mtu = self.mtu
        if self.nics:
            vss_spec.bridge = vim.host.VirtualSwitch.BondBridge(nicDevice=self.nics)

        if self.module.check_mode:
            results['msg'] = "vSwitch '%s' would be created" % self.switch
        else:
            try:
                self.network_mgr.AddVirtualSwitch(vswitchName=self.switch,
                                                  spec=vss_spec)

                changed = False
                spec = self.find_vswitch_by_name(self.host_system, self.switch).spec

                # Check Security Policy
                if self.update_security_policy(spec, results):
                    changed = True

                # Check Teaming Policy
                if self.update_teaming_policy(spec, results):
                    changed = True

                # Check Traffic Shaping Policy
                if self.update_traffic_shaping_policy(spec, results):
                    changed = True

                if changed:
                    self.network_mgr.UpdateVirtualSwitch(vswitchName=self.switch,
                                                         spec=spec)

                results['result'] = "vSwitch '%s' is created successfully" % self.switch
            except vim.fault.AlreadyExists as already_exists:
                results['result'] = "vSwitch with name %s already exists: %s" % (self.switch,
                                                                                 to_native(already_exists.msg))
            except vim.fault.ResourceInUse as resource_used:
                self.module.fail_json(msg="Failed to add vSwitch '%s' as physical network adapter"
                                          " being bridged is already in use: %s" % (self.switch,
                                                                                    to_native(resource_used.msg)))
            except vim.fault.HostConfigFault as host_config_fault:
                self.module.fail_json(msg="Failed to add vSwitch '%s' due to host"
                                          " configuration fault : %s" % (self.switch,
                                                                         to_native(host_config_fault.msg)))
            except vmodl.fault.InvalidArgument as invalid_argument:
                self.module.fail_json(msg="Failed to add vSwitch '%s', this can be due to either of following :"
                                          " 1. vSwitch Name exceeds the maximum allowed length,"
                                          " 2. Number of ports specified falls out of valid range,"
                                          " 3. Network policy is invalid,"
                                          " 4. Beacon configuration is invalid : %s" % (self.switch,
                                                                                        to_native(invalid_argument.msg)))
            except vmodl.fault.SystemError as system_error:
                self.module.fail_json(msg="Failed to add vSwitch '%s' due to : %s" % (self.switch,
                                                                                      to_native(system_error.msg)))
            except Exception as generic_exc:
                self.module.fail_json(msg="Failed to add vSwitch '%s' due to"
                                          " generic exception : %s" % (self.switch,
                                                                       to_native(generic_exc)))

        results['changed'] = True

        self.module.exit_json(**results)

    def state_exit_unchanged(self):
        """
        Declare exit without unchanged
        """
        self.module.exit_json(changed=False)

    def state_destroy_vswitch(self):
        """
        Remove vSwitch from configuration

        """
        results = dict(changed=False, result="")

        if self.module.check_mode:
            results['msg'] = "vSwitch '%s' would be removed" % self.vss.name
        else:
            try:
                self.host_system.configManager.networkSystem.RemoveVirtualSwitch(self.vss.name)
                results['result'] = "vSwitch '%s' removed successfully." % self.vss.name
            except vim.fault.NotFound as vswitch_not_found:
                results['result'] = "vSwitch '%s' not available. %s" % (self.switch,
                                                                        to_native(vswitch_not_found.msg))
            except vim.fault.ResourceInUse as vswitch_in_use:
                self.module.fail_json(msg="Failed to remove vSwitch '%s' as vSwitch"
                                          " is used by several virtual"
                                          " network adapters: %s" % (self.switch,
                                                                     to_native(vswitch_in_use.msg)))
            except vim.fault.HostConfigFault as host_config_fault:
                self.module.fail_json(msg="Failed to remove vSwitch '%s' due to host"
                                          " configuration fault : %s" % (self.switch,
                                                                         to_native(host_config_fault.msg)))
            except Exception as generic_exc:
                self.module.fail_json(msg="Failed to remove vSwitch '%s' due to generic"
                                          " exception : %s" % (self.switch,
                                                               to_native(generic_exc)))

        results['changed'] = True

        self.module.exit_json(**results)

    def state_update_vswitch(self):
        """
        Update vSwitch

        """
        changed = False
        results = dict(changed=False, result="No change in vSwitch '%s'" % self.switch)
        spec = self.vss.spec

        # Check MTU
        if self.vss.mtu != self.mtu:
            spec.mtu = self.mtu
            changed = True

        # Check Number of Ports
        if spec.numPorts != self.number_of_ports:
            spec.numPorts = self.number_of_ports
            changed = True

        # Check nics
        nics_current = set(map(lambda n: n.rsplit('-', 1)[1], self.vss.pnic))
        if nics_current != set(self.nics):
            if self.nics:
                spec.bridge = vim.host.VirtualSwitch.BondBridge(nicDevice=self.nics)
            else:
                spec.bridge = None
            changed = True

            # Update teaming if not configured specifigaly
            if not self.params['teaming']:
                nicOrder = spec.policy.nicTeaming.nicOrder
                # Remove missing nics from policy
                if nicOrder.activeNic != [i for i in nicOrder.activeNic if i in self.nics]:
                    nicOrder.activeNic = [i for i in nicOrder.activeNic if i in self.nics]
                if nicOrder.standbyNic != [i for i in nicOrder.standbyNic if i in self.nics]:
                    nicOrder.standbyNic = [i for i in nicOrder.standbyNic if i in self.nics]
                # Set new nics as active
                if set(self.nics) - nics_current:
                    nicOrder.activeNic += set(self.nics) - nics_current

        # Check Security Policy
        if self.update_security_policy(spec, results):
            changed = True

        # Check Teaming Policy
        if self.update_teaming_policy(spec, results):
            changed = True

        # Check Traffic Shaping Policy
        if self.update_traffic_shaping_policy(spec, results):
            changed = True

        if changed:
            if self.module.check_mode:
                results['msg'] = "vSwitch '%s' would be updated" % self.switch
            else:
                try:
                    self.network_mgr.UpdateVirtualSwitch(vswitchName=self.switch,
                                                         spec=spec)
                    results['result'] = "vSwitch '%s' is updated successfully" % self.switch
                except vim.fault.ResourceInUse as resource_used:
                    self.module.fail_json(msg="Failed to update vSwitch '%s' as physical network adapter"
                                              " being bridged is already in use: %s" % (self.switch,
                                                                                        to_native(resource_used.msg)))
                except vim.fault.NotFound as not_found:
                    self.module.fail_json(msg="Failed to update vSwitch with name '%s'"
                                              " as it does not exists: %s" % (self.switch,
                                                                              to_native(not_found.msg)))

                except vim.fault.HostConfigFault as host_config_fault:
                    self.module.fail_json(msg="Failed to update vSwitch '%s' due to host"
                                              " configuration fault : %s" % (self.switch,
                                                                             to_native(host_config_fault.msg)))
                except vmodl.fault.InvalidArgument as invalid_argument:
                    self.module.fail_json(msg="Failed to update vSwitch '%s', this can be due to either of following :"
                                              " 1. vSwitch Name exceeds the maximum allowed length,"
                                              " 2. Number of ports specified falls out of valid range,"
                                              " 3. Network policy is invalid,"
                                              " 4. Beacon configuration is invalid : %s" % (self.switch,
                                                                                            to_native(invalid_argument.msg)))
                except vmodl.fault.SystemError as system_error:
                    self.module.fail_json(msg="Failed to update vSwitch '%s' due to : %s" % (self.switch,
                                                                                             to_native(system_error.msg)))
                except vmodl.fault.NotSupported as not_supported:
                    self.module.fail_json(msg="Failed to update vSwitch '%s' as network adapter teaming policy"
                                              " is set but is not supported : %s" % (self.switch,
                                                                                     to_native(not_supported.msg)))
                except Exception as generic_exc:
                    self.module.fail_json(msg="Failed to update vSwitch '%s' due to"
                                              " generic exception : %s" % (self.switch,
                                                                           to_native(generic_exc)))

            results['changed'] = True

        self.module.exit_json(**results)

    def check_vswitch_configuration(self):
        """
        Check if vSwitch exists
        Returns: 'present' if vSwitch exists or 'absent' if not

        """
        self.vss = self.find_vswitch_by_name(self.host_system, self.switch)
        if self.vss is None:
            return 'absent'
        else:
            return 'present'

    @staticmethod
    def find_vswitch_by_name(host, vswitch_name):
        """
        Find and return vSwitch managed object
        Args:
            host: Host system managed object
            vswitch_name: Name of vSwitch to find

        Returns: vSwitch managed object if found, else None

        """
        for vss in host.configManager.networkSystem.networkInfo.vswitch:
            if vss.name == vswitch_name:
                return vss
        return None

    def update_security_policy(self, spec, results):
        """
        Update the security policy according to the parameters
        Args:
            spec: The vSwitch spec
            results: The results dict

        Returns: True if changes have been made, else false
        """
        if not self.params['security'] or not spec.policy.security:
            return False

        security_policy = spec.policy.security
        changed = False
        sec_promiscuous_mode = self.params['security'].get('promiscuous_mode')
        sec_forged_transmits = self.params['security'].get('forged_transmits')
        sec_mac_changes = self.params['security'].get('mac_changes')

        if sec_promiscuous_mode is not None:
            results['sec_promiscuous_mode'] = sec_promiscuous_mode
            if security_policy.allowPromiscuous is not sec_promiscuous_mode:
                results['sec_promiscuous_mode_previous'] = security_policy.allowPromiscuous
                security_policy.allowPromiscuous = sec_promiscuous_mode
                changed = True

        if sec_mac_changes is not None:
            results['sec_mac_changes'] = sec_mac_changes
            if security_policy.macChanges is not sec_mac_changes:
                results['sec_mac_changes_previous'] = security_policy.macChanges
                security_policy.macChanges = sec_mac_changes
                changed = True

        if sec_forged_transmits is not None:
            results['sec_forged_transmits'] = sec_forged_transmits
            if security_policy.forgedTransmits is not sec_forged_transmits:
                results['sec_forged_transmits_previous'] = security_policy.forgedTransmits
                security_policy.forgedTransmits = sec_forged_transmits
                changed = True

        return changed

    def update_teaming_policy(self, spec, results):
        """
        Update the teaming policy according to the parameters
        Args:
            spec: The vSwitch spec
            results: The results dict

        Returns: True if changes have been made, else false
        """
        if not self.params['teaming'] or not spec.policy.nicTeaming:
            return False

        teaming_policy = spec.policy.nicTeaming
        changed = False
        teaming_load_balancing = self.params['teaming'].get('load_balancing')
        teaming_failure_detection = self.params['teaming'].get('network_failure_detection')
        teaming_notify_switches = self.params['teaming'].get('notify_switches')
        teaming_failback = self.params['teaming'].get('failback')
        teaming_failover_order_active = self.params['teaming'].get('active_adapters')
        teaming_failover_order_standby = self.params['teaming'].get('standby_adapters')

        # Check teaming policy
        if teaming_load_balancing is not None:
            results['load_balancing'] = teaming_load_balancing
            if teaming_policy.policy != teaming_load_balancing:
                results['load_balancing_previous'] = teaming_policy.policy
                teaming_policy.policy = teaming_load_balancing
                changed = True

        # Check teaming notify switches
        if teaming_notify_switches is not None:
            results['notify_switches'] = teaming_notify_switches
            if teaming_policy.notifySwitches is not teaming_notify_switches:
                results['notify_switches_previous'] = teaming_policy.notifySwitches
                teaming_policy.notifySwitches = teaming_notify_switches
                changed = True

        # Check failback
        if teaming_failback is not None:
            results['failback'] = teaming_failback
            current_failback = not teaming_policy.rollingOrder
            if current_failback != teaming_failback:
                results['failback_previous'] = current_failback
                teaming_policy.rollingOrder = not teaming_failback
                changed = True

        # Check teaming failover order
        if teaming_failover_order_active is not None:
            results['failover_active'] = teaming_failover_order_active
            if teaming_policy.nicOrder.activeNic != teaming_failover_order_active:
                results['failover_active_previous'] = teaming_policy.nicOrder.activeNic
                teaming_policy.nicOrder.activeNic = teaming_failover_order_active
                changed = True
        if teaming_failover_order_standby is not None:
            results['failover_standby'] = teaming_failover_order_standby
            if teaming_policy.nicOrder.standbyNic != teaming_failover_order_standby:
                results['failover_standby_previous'] = teaming_policy.nicOrder.standbyNic
                teaming_policy.nicOrder.standbyNic = teaming_failover_order_standby
                changed = True

        # Check teaming failure detection
        if teaming_failure_detection is not None:
            results['failure_detection'] = teaming_failure_detection
            if teaming_failure_detection == "link_status_only":
                if teaming_policy.failureCriteria.checkBeacon is True:
                    results['failure_detection_previous'] = "beacon_probing"
                    teaming_policy.failureCriteria.checkBeacon = False
                    changed = True
            elif teaming_failure_detection == "beacon_probing":
                if teaming_policy.failureCriteria.checkBeacon is False:
                    results['failure_detection_previous'] = "link_status_only"
                    teaming_policy.failureCriteria.checkBeacon = True
                    changed = True

        return changed

    def update_traffic_shaping_policy(self, spec, results):
        """
        Update the traffic shaping policy according to the parameters
        Args:
            spec: The vSwitch spec
            results: The results dict

        Returns: True if changes have been made, else false
        """
        if not self.params['traffic_shaping'] or not spec.policy.nicTeaming:
            return False

        ts_policy = spec.policy.shapingPolicy
        changed = False
        ts_enabled = self.params['traffic_shaping'].get('enabled')

        # Check if traffic shaping needs to be disabled
        if not ts_enabled:
            if ts_policy.enabled:
                ts_policy.enabled = False
                changed = True
            return changed

        for value in ['average_bandwidth', 'peak_bandwidth', 'burst_size']:
            if not self.params['traffic_shaping'].get(value):
                self.module.fail_json(msg="traffic_shaping.%s is a required parameter if traffic_shaping is enabled." % value)
        ts_average_bandwidth = self.params['traffic_shaping'].get('average_bandwidth') * 1000
        ts_peak_bandwidth = self.params['traffic_shaping'].get('peak_bandwidth') * 1000
        ts_burst_size = self.params['traffic_shaping'].get('burst_size') * 1024

        if not ts_policy.enabled:
            ts_policy.enabled = True
            changed = True

        if ts_policy.averageBandwidth != ts_average_bandwidth:
            results['traffic_shaping_avg_bandw'] = ts_average_bandwidth
            results['traffic_shaping_avg_bandw_previous'] = ts_policy.averageBandwidth
            ts_policy.averageBandwidth = ts_average_bandwidth
            changed = True

        if ts_policy.peakBandwidth != ts_peak_bandwidth:
            results['traffic_shaping_peak_bandw'] = ts_peak_bandwidth
            results['traffic_shaping_peak_bandw_previous'] = ts_policy.peakBandwidth
            ts_policy.peakBandwidth = ts_peak_bandwidth
            changed = True

        if ts_policy.burstSize != ts_burst_size:
            results['traffic_shaping_burst'] = ts_burst_size
            results['traffic_shaping_burst_previous'] = ts_policy.burstSize
            ts_policy.burstSize = ts_burst_size
            changed = True

        return changed


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(dict(
        switch=dict(type='str', required=True, aliases=['switch_name']),
        nics=dict(type='list', aliases=['nic_name'], default=[], elements='str'),
        number_of_ports=dict(type='int', default=128),
        mtu=dict(type='int', default=1500),
        state=dict(type='str', default='present', choices=['absent', 'present']),
        esxi_hostname=dict(type='str', aliases=['host']),
        security=dict(
            type='dict',
            options=dict(
                promiscuous_mode=dict(type='bool'),
                forged_transmits=dict(type='bool'),
                mac_changes=dict(type='bool'),
            ),
            aliases=['security_policy', 'network_policy']
        ),
        teaming=dict(
            type='dict',
            options=dict(
                load_balancing=dict(
                    type='str',
                    choices=[
                        'loadbalance_ip',
                        'loadbalance_srcmac',
                        'loadbalance_srcid',
                        'failover_explicit',
                    ],
                    aliases=['load_balance_policy'],
                ),
                network_failure_detection=dict(
                    type='str',
                    choices=['link_status_only', 'beacon_probing']
                ),
                notify_switches=dict(type='bool'),
                failback=dict(type='bool'),
                active_adapters=dict(type='list', elements='str'),
                standby_adapters=dict(type='list', elements='str'),
            ),
            aliases=['teaming_policy']
        ),
        traffic_shaping=dict(
            type='dict',
            options=dict(
                enabled=dict(type='bool'),
                average_bandwidth=dict(type='int'),
                peak_bandwidth=dict(type='int'),
                burst_size=dict(type='int'),
            ),
        ),
    ))

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    host_virtual_switch = VMwareHostVirtualSwitch(module)
    host_virtual_switch.process_state()


if __name__ == '__main__':
    main()

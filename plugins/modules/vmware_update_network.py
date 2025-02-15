#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2015, Joseph Callen <jcallen () csc.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: vmware_migrate_vmk
short_description: Migrate a VMK interface from VSS to VDS
description:
    - Migrate a VMK interface from VSS to VDS
author:
- Joseph Callen (@jcpowermac)
- Russell Teague (@mtnbikenc)
notes:
    - Tested on vSphere 6.7
requirements:
    - "python >= 2.6"
    - PyVmomi
options:
    esxi_hostname:
        description:
            - ESXi hostname to be managed
        required: True
        type: str
    device:
        description:
            - VMK interface name
        required: True
        type: str
    current_switch_name:
        description:
            - Switch VMK interface is currently on
        required: True
        type: str
    current_portgroup_name:
        description:
            - Portgroup name VMK interface is currently on
        required: True
        type: str
    migrate_switch_name:
        description:
            - Switch name to migrate VMK interface to
        required: True
        type: str
    migrate_portgroup_name:
        description:
            - Portgroup name to migrate VMK interface to
        required: True
        type: str
extends_documentation_fragment:
- community.vmware.vmware.documentation

'''

EXAMPLES = r'''
- name: Migrate Management vmk
  community.vmware.vmware_migrate_vmk:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    esxi_hostname: "{{ esxi_hostname }}"
    device: vmk1
    current_switch_name: temp_vswitch
    current_portgroup_name: esx-mgmt
    migrate_switch_name: dvSwitch
    migrate_portgroup_name: Management
    lag_uplinks:
        - lag: lag1
          vmnics:
              - vmnic0
              - vmnic1
  delegate_to: localhost
'''
try:
    from pyVmomi import vim, vmodl
    HAS_PYVMOMI = True
except ImportError:
    HAS_PYVMOMI = False

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.community.vmware.plugins.module_utils.vmware import (
    vmware_argument_spec, find_dvs_by_name, find_hostsystem_by_name,
    connect_to_api, find_dvspg_by_name)


class VMwareMigrateVmk(object):

    def __init__(self, module):
        self.module = module
        self.host_system = None
        self.uplink_portgroup = None
        self.migrate_switch_name = self.module.params['migrate_switch_name']
        self.migrate_portgroup_name = self.module.params['migrate_portgroup_name']
        self.device = self.module.params['device']
        self.esxi_hostname = self.module.params['esxi_hostname']
        self.current_portgroup_name = self.module.params['current_portgroup_name']
        self.current_switch_name = self.module.params['current_switch_name']
        self.content = connect_to_api(module)
        self.vmnics = self.module.params['vmnics']
        self.lag_uplinks = self.module.params['lag_uplinks']

        self.desired_state = {}
        self.dv_switch = None
        self.lags = {}
        self.host = self.esxi_hostname

        self.dv_switch = find_dvs_by_name(self.content, self.migrate_switch_name)
        for lag in self.dv_switch.config.lacpGroupConfig:
            self.lags[lag.name] = lag

        for lag_uplink in self.lag_uplinks:
            if lag_uplink['lag'] not in self.lags:
                self.module.fail_json(msg="LAG %s not found" % lag_uplink['lag'])
    def find_dvs_uplink_pg(self):
        # There should only always be a single uplink port group on
        # a distributed virtual switch
        dvs_uplink_pg = self.dv_switch.config.uplinkPortgroup[0] if len(self.dv_switch.config.uplinkPortgroup) else None
        return dvs_uplink_pg

    def set_desired_state_lag(self):
        lag_uplinks = []
        switch_uplink_ports = {'non_lag': []}
        self.uplink_portgroup = self.find_dvs_uplink_pg()
        portCriteria = vim.dvs.PortCriteria()
        portCriteria.host = [self.host]
        portCriteria.portgroupKey = self.uplink_portgroup.key
        portCriteria.uplinkPort = True
        ports = self.dv_switch.FetchDVPorts(portCriteria)

        for name, lag in self.lags.items():
            switch_uplink_ports[name] = []
            for uplinkName in lag.uplinkName:
                for port in ports:
                    if port.config.name == uplinkName:
                        switch_uplink_ports[name].append(port.key)
                        lag_uplinks.append(port.key)

        for port in sorted(ports, key=lambda port: port.config.name):
            if port.key in self.uplink_portgroup.portKeys and port.key not in lag_uplinks:
                switch_uplink_ports['non_lag'].append(port.key)

        count = 0
        for vmnic in self.vmnics:
            self.desired_state[vmnic] = switch_uplink_ports['non_lag'][count]
            count += 1

        for lag in self.lag_uplinks:
            count = 0
            for vmnic in lag['vmnics']:
                self.desired_state[vmnic] = switch_uplink_ports[lag['lag']][count]
                count += 1


    def find_host_attached_dvs(self):
        for dvs_host_member in self.dv_switch.Fphost:
            if dvs_host_member.config.host.name == self.esxi_hostname:
                return dvs_host_member.config.host

        return None

    def modify_dvs_host(self, operation):
        changed, result = False, None
        spec = vim.DistributedVirtualSwitch.ConfigSpec()


        spec.configVersion = self.dv_switch.config.configVersion

        spec.host = [vim.dvs.HostMember.ConfigSpec()]
        spec.host[0].operation = operation
        spec.host[0].host = self.host
        # if self.vendor_specific_config:
        #     config = list()
        #     for item in self.vendor_specific_config:
        #         config.append(vim.dvs.KeyedOpaqueBlob(key=item['key'], opaqueData=item['value']))
        #     spec.host[0].vendorSpecificConfig = config

        if operation == "edit":
            spec.host[0].backing = vim.dvs.HostMember.PnicBacking()

            for nic, uplinkPortKey in self.desired_state.items():
                pnicSpec = vim.dvs.HostMember.PnicSpec()
                pnicSpec.pnicDevice = nic
                pnicSpec.uplinkPortgroupKey = self.uplink_portgroup.key
                pnicSpec.uplinkPortKey = uplinkPortKey
                spec.host[0].backing.pnicSpec.append(pnicSpec)

        try:
            task = self.dv_switch.ReconfigureDvs_Task(spec)
  #          changed, result = wait_for_task(task)
        except vmodl.fault.NotSupported as not_supported:
            self.module.fail_json(msg="Failed to configure DVS host %s as it is not"
                                      " compatible with the VDS version." % self.esxi_hostname,
                                  details=to_native(not_supported.msg))
 #       return changed, result
        return spec
    def process_state(self):
        try:
            vmk_migration_states = {
                'migrate_vss_vds': self.state_migrate_vss_vds,
                'migrate_vds_vss': self.state_migrate_vds_vss,
                'migrated': self.state_exit_unchanged
            }

            vmk_migration_states[self.check_vmk_current_state()]()

        except vmodl.RuntimeFault as runtime_fault:
            self.module.fail_json(msg=runtime_fault.msg)
        except vmodl.MethodFault as method_fault:
            self.module.fail_json(msg=method_fault.msg)
        except Exception as e:
            self.module.fail_json(msg=str(e))

    def state_exit_unchanged(self):
        self.module.exit_json(changed=False)

    def create_host_vnic_config_vds_vss(self):
        host_vnic_config = vim.host.VirtualNic.Config()
        host_vnic_config.spec = vim.host.VirtualNic.Specification()
        host_vnic_config.changeOperation = "edit"
        host_vnic_config.device = self.device
        host_vnic_config.spec.portgroup = self.migrate_portgroup_name
        return host_vnic_config

    def create_port_group_config_vds_vss(self):
        port_group_config = vim.host.PortGroup.Config()
        port_group_config.spec = vim.host.PortGroup.Specification()
        port_group_config.changeOperation = "add"
        port_group_config.spec.name = self.migrate_portgroup_name
        port_group_config.spec.vlanId = 0
        port_group_config.spec.vswitchName = self.migrate_switch_name
        port_group_config.spec.policy = vim.host.NetworkPolicy()
        return port_group_config

    def state_migrate_vds_vss(self):
        host_network_system = self.host_system.configManager.networkSystem
        config = vim.host.NetworkConfig()
        config.portgroup = [self.create_port_group_config_vds_vss()]
        host_network_system.UpdateNetworkConfig(config, "modify")
        config = vim.host.NetworkConfig()
        config.vnic = [self.create_host_vnic_config_vds_vss()]
        host_network_system.UpdateNetworkConfig(config, "modify")
        self.module.exit_json(changed=True)

    def create_host_vnic_config(self, dv_switch_uuid, portgroup_key):
        host_vnic_config = vim.host.VirtualNic.Config()
        host_vnic_config.spec = vim.host.VirtualNic.Specification()

        host_vnic_config.changeOperation = "edit"
        host_vnic_config.device = self.device
        host_vnic_config.portgroup = ""
        host_vnic_config.spec.distributedVirtualPort = vim.dvs.PortConnection()
        host_vnic_config.spec.distributedVirtualPort.switchUuid = dv_switch_uuid
        host_vnic_config.spec.distributedVirtualPort.portgroupKey = portgroup_key

        return host_vnic_config

    def create_port_group_config(self):
        port_group_config = vim.host.PortGroup.Config()
        port_group_config.spec = vim.host.PortGroup.Specification()

        port_group_config.changeOperation = "remove"
        port_group_config.spec.name = self.current_portgroup_name
        port_group_config.spec.vlanId = -1
        port_group_config.spec.vswitchName = self.current_switch_name
        port_group_config.spec.policy = vim.host.NetworkPolicy()

        return port_group_config

    def state_migrate_vss_vds(self):
        host_network_system = self.host_system.configManager.networkSystem

        dv_switch = find_dvs_by_name(self.content, self.migrate_switch_name)
        pg = find_dvspg_by_name(dv_switch, self.migrate_portgroup_name)
        self.host = find_hostsystem_by_name(self.content, self.esxi_hostname)
        self.set_desired_state_lag()
        s = self.modify_dvs_host("edit")

        config = vim.host.NetworkConfig()

        # current_switch_name

        config_vswitch_0 = vim.host.VirtualSwitch.Config()
        config_vswitch_0.name = self.current_switch_name
        config_vswitch_0.changeOperation = 'edit'
        config_vswitch_0.spec = vim.host.VirtualSwitch.Specification()
        config_vswitch_0.spec.numPorts = 128
        config_vswitch_0.spec.policy = vim.host.NetworkPolicy()
        config_vswitch_0.spec.policy.security = vim.host.NetworkPolicy.SecurityPolicy()
        config_vswitch_0.spec.policy.security.allowPromiscuous = False
        config_vswitch_0.spec.policy.security.forgedTransmits = True
        config_vswitch_0.spec.policy.security.macChanges = True
        config_vswitch_0.spec.policy.offloadPolicy = vim.host.NetOffloadCapabilities()
        config_vswitch_0.spec.policy.offloadPolicy.tcpSegmentation = True
        config_vswitch_0.spec.policy.offloadPolicy.zeroCopyXmit = True
        config_vswitch_0.spec.policy.offloadPolicy.csumOffload = True
        config_vswitch_0.spec.policy.shapingPolicy = vim.host.NetworkPolicy.TrafficShapingPolicy()
        config_vswitch_0.spec.policy.shapingPolicy.enabled = False
        config_vswitch_0.spec.policy.nicTeaming = vim.host.NetworkPolicy.NicTeamingPolicy()
        config_vswitch_0.spec.policy.nicTeaming.notifySwitches = True
        config_vswitch_0.spec.policy.nicTeaming.rollingOrder = False
        config_vswitch_0.spec.policy.nicTeaming.failureCriteria = vim.host.NetworkPolicy.NicFailureCriteria()
        config_vswitch_0.spec.policy.nicTeaming.failureCriteria.fullDuplex = False
        config_vswitch_0.spec.policy.nicTeaming.failureCriteria.percentage = 0
        config_vswitch_0.spec.policy.nicTeaming.failureCriteria.checkErrorPercent = False
        config_vswitch_0.spec.policy.nicTeaming.failureCriteria.checkDuplex = False
        config_vswitch_0.spec.policy.nicTeaming.failureCriteria.checkBeacon = False
        config_vswitch_0.spec.policy.nicTeaming.failureCriteria.speed = 10
        config_vswitch_0.spec.policy.nicTeaming.failureCriteria.checkSpeed = 'minimum'
        config_vswitch_0.spec.policy.nicTeaming.policy = 'loadbalance_srcid'
        config_vswitch_0.spec.policy.nicTeaming.reversePolicy = True
        config.vswitch = [config_vswitch_0]

        config.portgroup = [self.create_port_group_config()]
        config.vnic = [self.create_host_vnic_config(dv_switch.uuid, pg.key)]
        hpConfig = vim.host.HostProxySwitch.Config()
        config.proxySwitch = [hpConfig]
        config.proxySwitch[0].uuid = dv_switch.uuid
        config.proxySwitch[0].changeOperation = 'edit'
        config.proxySwitch[0].spec = vim.host.HostProxySwitch.Specification()
        config.proxySwitch[0].spec.backing = vim.dvs.HostMember.PnicBacking()

        config_proxySwitch_0_spec_backing_pnicSpec_0 = vim.dvs.HostMember.PnicSpec()
        config_proxySwitch_0_spec_backing_pnicSpec_0.pnicDevice = s.host[0].backing.pnicSpec[0].pnicDevice
        config_proxySwitch_0_spec_backing_pnicSpec_0.uplinkPortKey = s.host[0].backing.pnicSpec[0].uplinkPortKey
        config_proxySwitch_0_spec_backing_pnicSpec_0.uplinkPortgroupKey = s.host[0].backing.pnicSpec[0].uplinkPortgroupKey
        config_proxySwitch_0_spec_backing_pnicSpec_1 = vim.dvs.HostMember.PnicSpec()
        config_proxySwitch_0_spec_backing_pnicSpec_1.pnicDevice = s.host[0].backing.pnicSpec[1].pnicDevice
        config_proxySwitch_0_spec_backing_pnicSpec_1.uplinkPortKey = s.host[0].backing.pnicSpec[1].uplinkPortKey
        config_proxySwitch_0_spec_backing_pnicSpec_1.uplinkPortgroupKey = s.host[0].backing.pnicSpec[0].uplinkPortgroupKey


        config.proxySwitch[0].spec.backing.pnicSpec = [config_proxySwitch_0_spec_backing_pnicSpec_0,config_proxySwitch_0_spec_backing_pnicSpec_1]

        host_network_system.UpdateNetworkConfig(config, "modify")
        self.module.exit_json(changed=True)

    def check_vmk_current_state(self):
        self.host_system = find_hostsystem_by_name(self.content, self.esxi_hostname)

        for vnic in self.host_system.configManager.networkSystem.networkInfo.vnic:
            if vnic.device == self.device:
                if vnic.spec.distributedVirtualPort is None:
                    std_vswitches = [vswitch.name for vswitch in self.host_system.configManager.networkSystem.networkInfo.vswitch]
                    if self.current_switch_name not in std_vswitches:
                        return "migrated"
                    if vnic.portgroup == self.current_portgroup_name:
                        return "migrate_vss_vds"
                else:
                    dvs = find_dvs_by_name(self.content, self.current_switch_name)
                    if dvs is None:
                        return "migrated"
                    if vnic.spec.distributedVirtualPort.switchUuid == dvs.uuid:
                        return "migrate_vds_vss"


def main():

    argument_spec = vmware_argument_spec()
    argument_spec.update(dict(esxi_hostname=dict(required=True, type='str'),
                              device=dict(required=True, type='str'),
                              current_switch_name=dict(required=True, type='str'),
                              current_portgroup_name=dict(required=True, type='str'),
                              migrate_switch_name=dict(required=True, type='str'),
                              migrate_portgroup_name=dict(required=True, type='str'),
                              vmnics=dict(required=False, type='list', default=[], elements='str'),
                              lag_uplinks=dict(
                                  type='list',
                                  default=[],
                                  required=False,
                                  elements='dict',
                                  options=dict(
                                      lag=dict(
                                          type='str',
                                          required=True,
                                      ),
                                      vmnics=dict(
                                          type='list',
                                          required=False,
                                          elements='str',
                                          default=[],
                                      ),
                                  ),
                              ),

                              ))

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False)

    if not HAS_PYVMOMI:
        module.fail_json(msg='pyvmomi required for this module')
    vmware_migrate_vmk = VMwareMigrateVmk(module)
    vmware_migrate_vmk.process_state()


if __name__ == '__main__':
    main()

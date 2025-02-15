#!/usr/bin/python
#
# (c) 2015, Joseph Callen <jcallen () csc.com>
# Portions Copyright (c) 2015 VMware, Inc. All rights reserved.
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.



DOCUMENTATION = '''
module: vcenter_config_host_vds
short_description: Configure hosts vmnic on specified uplink port
description:
    Add host to vds and specified vmnic to specified uplink port
notes:
    - Tested on vcenter 6.0.0 Build 2594327 with ansible 2.1.0.0

requirements:
    - pyVmomi
    - ansible 2.x

options:
    hostname:
        description:
            - The hostname or IP address of the vSphere vCenter API server
        required: True
    username:
        description:
            - The username of the vSphere vCenter
        required: True
        aliases: ['user', 'admin']
    password:
        description:
            - The password of the vSphere vCenter
        required: True
        aliases: ['pass', 'pwd']
    datacenter_name:
        description:
            - The name of the datacenter the host will be configured in.
        required: True
    esxi_hostname:
        description:
            - The name/ip of the esx host to configure.
        required: True
    vds_name:
        description:
            - The name of the vds.
        required: True
    vmnic:
        description:
            - Specify vmnic to add to specified uplink
        required: True
    uplink_name:
        description:
            - Name of the uplink to add the specified vmnic to
        required: True
    state:
        description:
            - Currently only supported is present option
        choices: ['present']
        required: True
'''

EXAMPLES = '''
- name: config host on vds
  vcenter_config_host_vds:
    hostname: '172.16.0.100'
    username: 'administrator@corp.local'
    password: 'VMware1!'
    validate_certs: False
    datacenter: 'dc-01'
    esxi_hostname: "{{ item.name }}"
    vds_name: 'vds001'
    vmnic: "{{ item.nic }}"
    uplink_name: "{{ item.uplink }}"
    state: 'present'
  with_items:
    - { name: '172.16.0.205', uplink: 'vds001_Uplink_2', nic: 'vmnic1' }
    - { name: '172.16.0.205', uplink: 'vds001_Uplink_3', nic: 'vmnic2' }
    - { name: '172.16.0.205', uplink: 'vds001_Uplink_4', nic: 'vmnic3' }
  tags:
    - testing
'''

try:
    from pyVmomi import vim, vmodl
    import collections
    HAS_PYVMOMI = True
except ImportError:
    HAS_PYVMOMI = False


vc = {}


def host_current_pnic_spec(host, vdsuuid, vmnic):

    current_spec = None

    proxy_switches = host.config.network.proxySwitch

    for proxy_switch in proxy_switches:
        if proxy_switch.dvsUuid == vdsuuid:
            current_spec = proxy_switch.spec.backing.pnicSpec

    for i in current_spec:
        if i.pnicDevice == vmnic:
            current_spec.remove(i)

    return current_spec


def check_uplink_name(module):

    name_present = False

    uplink_name = module.params['uplink_name']
    vds = vc['vds']

    if uplink_name in vds.config.uplinkPortPolicy.uplinkPortName:
        name_present = True

    lag_pgs = [l for i in vds.config.lacpGroupConfig for l in i.uplinkName]

    if uplink_name in lag_pgs:
        name_present = True

    return name_present


def assign_specified_uplink(module, spec):

    reconfig_task = None
    host = vc['host']

    try:
       reconfig_task = host.configManager.networkSystem.UpdateNetworkConfig(spec, "modify")
    except Exception as e:
       module.fail_json(msg="Failed assigning uplink: {}".format(str(e)))

    return reconfig_task


def check_host_uplink(host):

    uplink_port_key = None
    vdsuuid = vc['vds_uuid']
    vmnic = vc['vmnic']

    proxy_switches = host.config.network.proxySwitch

    for proxy_switch in proxy_switches:
        if proxy_switch.dvsUuid == vdsuuid:
            for pnic in proxy_switch.spec.backing.pnicSpec:
                if pnic.pnicDevice == vmnic:
                    uplink_port_key = pnic.uplinkPortKey

    return uplink_port_key


def check_vmnic_available(module):

    host = vc['host']
    vmnic = module.params['vmnic']

    pnic = [p for p in host.config.network.pnic if p.device == vmnic]

    if not pnic:
        module.fail_json(msg="Specified vmnic: {} not in host specification".format(vmnic))

    pnic = pnic[0]
    pnic_key = pnic.key
    pnic_devcie = pnic.device

    vss = host.config.network.vswitch[0]

    if pnic_key in vss.pnic:
        fail_msg = "The specified vmnic: {} is in use by vswitch: {}".format(vmnic, vss.name)
        module.fail_json(msg=fail_msg)

    return pnic_devcie


def reconfig_host_net_config_spec(uplink_port_key, pnic_device):

    uplink_portgroup_key = vc['uplink_portgroup_key']
    vdsuuid = vc['vds_uuid']

    host_pnic_spec = vim.dvs.HostMember.PnicSpec(
        pnicDevice=pnic_device,
        uplinkPortgroupKey=uplink_portgroup_key,
        uplinkPortKey=uplink_port_key
    )

    host_backing = vim.dvs.HostMember.PnicBacking(pnicSpec=[host_pnic_spec])

    proxy_spec = vim.host.HostProxySwitch.Specification(backing=host_backing)

    proxy_config = vim.host.HostProxySwitch.Config(
        changeOperation="edit",
        uuid=vdsuuid,
        spec=proxy_spec
    )

    host_net_spec = vim.host.NetworkConfig()
    host_net_spec.proxySwitch = [proxy_config]

    return host_net_spec


def update_host_net_config_spec(uplink_port_key, pnic_device, current_spec):

    uplink_portgroup_key = vc['uplink_portgroup_key']
    vdsuuid = vc['vds_uuid']

    host_pnic_spec = vim.dvs.HostMember.PnicSpec(
        pnicDevice=pnic_device,
        uplinkPortgroupKey=uplink_portgroup_key,
        uplinkPortKey=uplink_port_key
    )

    host_backing = vim.dvs.HostMember.PnicBacking()

    if len(current_spec):

        for i in range(len(current_spec)):
            host_backing.pnicSpec.append(current_spec[i])

    host_backing.pnicSpec.append(host_pnic_spec)

    proxy_spec = vim.host.HostProxySwitch.Specification(backing=host_backing)

    proxy_config = vim.host.HostProxySwitch.Config(
        changeOperation="edit",
        uuid=vdsuuid,
        spec=proxy_spec
    )

    host_net_spec = vim.host.NetworkConfig()
    host_net_spec.proxySwitch = [proxy_config]

    return host_net_spec


def host_uplinkport_key(module, host):

    uplink_key = None
    uplink_name = module.params['uplink_name']
    vdsuuid = vc['vds_uuid']

    proxy_switches = host.config.network.proxySwitch

    for proxy_switch in proxy_switches:
        if proxy_switch.dvsUuid == vdsuuid:
            for uplink_port in proxy_switch.uplinkPort:
                if uplink_port.value == uplink_name:
                    uplink_key = uplink_port.key

    return uplink_key


def vds_add_host_spec():

    host = vc['host']
    operation = 'add'
    vmnic = vc['vmnic']
    uplink_portgroup_key = vc['uplink_portgroup_key']
    vds_config_version = vc['vds_config_version']

    host_mem_backing_pnicspec = vim.dvs.HostMember.PnicSpec(
        pnicDevice = vmnic,
        uplinkPortgroupKey = uplink_portgroup_key
    )

    host_mem_spec_backing = vim.dvs.HostMember.PnicBacking(
        pnicSpec=[host_mem_backing_pnicspec]
    )

    host_mem_spec = vim.dvs.HostMember.ConfigSpec(
        operation = operation,
        host = host,
        backing = host_mem_spec_backing
    )

    dvs_config_spec = vim.DistributedVirtualSwitch.ConfigSpec(
        configVersion = vds_config_version,
        host = [host_mem_spec]
    )

    return dvs_config_spec


def add_host_vds(module, spec):

    vds = vc['vds']
    changed = False
    result = None

    try:
        reconfig_vds_task = vds.ReconfigureDvs_Task(spec)
        changed, result = wait_for_task(reconfig_vds_task)
    except vmodl.RuntimeFault as runtime_fault:
        module.fail_json(msg=runtime_fault.msg)
    except vmodl.MethodFault as method_fault:
        module.fail_json(msg=method_fault.msg)
    except Exception as e:
        module.fail_json(msg=str(e))

    return changed, result


def host_dvs_compatibility_check(module):

    host_compatible = False
    content = vc['si']
    dc = vc['datacenter']
    vds = vc['vds']
    host = vc['host']
    vds_manager = content.dvSwitchManager

    try:

        compatible_hosts = vds_manager.QueryCompatibleHostForExistingDvs(dc, True, vds)

        if host in compatible_hosts:
            host_compatible = True

    except vmodl.fault.InvalidArgument as invalid_argument:
        module.fail_json(msg="The vds is not valid or recognized: {}".format(invalid_argument))
    except Exception as e:
        module.fail_json(msg="Error checking host compatibiliy: {}".format(e))

    return host_compatible


def host_migration_dependencies(module):

    allowed = False

    pnic_device = vc['vmnic']
    host = vc['host']
    iscsi_manager = host.configManager.iscsiManager

    try:

        migration_dependency = iscsi_manager.QueryMigrationDependencies(pnic_device)
        allowed = migration_dependency.migrationAllowed

    except vmodl.RuntimeFault as runtime_fault:
        module.fail_json(msg=runtime_fault.msg)
    except vmodl.MethodFault as method_fault:
        module.fail_json(msg=method_fault.msg)
    except Exception as e:
        module.fail_json(msg=str(e))

    if not allowed:
        disallow_reason = migration_dependency.disallowReason
        return allowed, disallow_reason

    return allowed, None


def find_host_attached_vds(esxi_hostname, vds):

    for vds_host_member in vds.config.host:
        if vds_host_member.config.host.name == esxi_hostname:
            return vds_host_member.config.host

    return None


def find_dvs_uplink_pg(vds):

    if len(vds.config.uplinkPortgroup):
        return vds.config.uplinkPortgroup[0]
    else:
        return None


def state_create_vds_host(module):

    esx_hostname = module.params['esxi_hostname']
    vds_name = module.params['vds_name']
    host = vc['host']

    host_compatible = host_dvs_compatibility_check(module)

    if not host_compatible:
        fail_msg = "Host: {} is not compatible with vds: {}".format(esx_hostname, vds_name)
        module.fail_json(msg=fail_msg)

    migration_dependencies, disallow_reason = host_migration_dependencies(module)

    if not migration_dependencies:
        fail_msg = "Host: {} has following migration dependencies issues {}".format(esx_hostname, disallow_reason)
        module.fail_json(msg=fail_msg)

    add_spec = vds_add_host_spec()
    changed, result = add_host_vds(module, add_spec)

    if not changed:
        fail_msg = "Failed to add host: {} to vds: {}".format(esx_hostname, vds_name)
        module.fail_json(msg=fail_msg)

    uplink_port_key = host_uplinkport_key(module, host)
    pnic_device = vc['vmnic']

    if not uplink_port_key:
        module.fail_json(msg="Failed to get uplink port group key")

    update_spec = reconfig_host_net_config_spec(uplink_port_key, pnic_device)

    assign_uplink = assign_specified_uplink(module, update_spec)

    if not assign_uplink:
        module.fail_json(msg="Failed to assign uplink")

    module.exit_json(changed=True, result=str(assign_uplink))


def state_update_vds_host(module):

    host = vc['host']
    vds_uuid = vc['vds_uuid']
    uplink_port_key = host_uplinkport_key(module, host)
    pnic_device = vc['vmnic']

    current_spec = host_current_pnic_spec(host, vds_uuid, pnic_device)

    spec = update_host_net_config_spec(uplink_port_key, pnic_device, current_spec)

    assign_uplink = assign_specified_uplink(module, spec)

    if not assign_uplink:
        module.fail_json(msg="Failed to assign uplink")

    module.exit_json(changed=True, result=str(assign_uplink))


def state_destroy_vds_host(module):
    module.exit_json(changed=False, msg="DELETE")


def state_exit_unchanged(module):
    module.exit_json(changed=False, msg="EXIT UNCHANGED")


def check_vds_host_state(module):

    datacenter_name = module.params['datacenter']
    vds_name = module.params['vds_name']
    esxi_hostname = module.params['esxi_hostname']

    si = connect_to_api(module)
    vc['si'] = si

    datacenter = find_datacenter_by_name(si, datacenter_name)

    if not datacenter:
        module.fail_json(msg="Could not find Datacenter: {}".format(datacenter_name))

    vds = find_dvs_by_name(si, vds_name)

    if not vds:
        module.fail_json(msg="Virtual distributed switch: {} does not exist".format(vds_name))

    uplink_portgroup = find_dvs_uplink_pg(vds)

    if not uplink_portgroup:
        module.fail_json(msg="An uplink portgroup does not exist on the distributed virtual switch {}".format(vds_name))

    vc['datacenter'] = datacenter
    vc['vds'] = vds
    vc['vds_uuid'] = vds.uuid
    vc['vds_config_version'] = vds.config.configVersion
    vc['uplink_portgroup'] = uplink_portgroup
    vc['uplink_portgroup_key'] = uplink_portgroup.key

    uplink_check = check_uplink_name(module)

    if not uplink_check:
        module.fail_json(msg="Specified uplink name:{} not found".format(module.params['uplink_name']))

    host = find_host_attached_vds(esxi_hostname, vds)

    if not host:
        host = find_hostsystem_by_name(si, esxi_hostname)

        if not host:
            module.fail_json(msg="Esxi host: %s not in vcenter" % esxi_hostname)

        vc['host'] = host

        vmnic = check_vmnic_available(module)

        vc['vmnic'] = vmnic

        return 'absent'

    else:
        vc['host'] = host

        vmnic = check_vmnic_available(module)
        vc['vmnic'] = vmnic

        if not host_uplinkport_key(module, host):
            module.fail_json(msg="uplink name not found in available uplinks")

        if check_host_uplink(host) == host_uplinkport_key(module, host):
            return 'present'
        else:
            return 'update'



def main():
    argument_spec = vmware_argument_spec()

    argument_spec.update(
        dict(
            datacenter=dict(required=True, type='str'),
            esxi_hostname=dict(required=True, type='str'),
            vds_name=dict(required=True, type='str'),
            vmnic=dict(required=True, type='str'),
            uplink_name=dict(required=True, type='str'),
            state=dict(default='present', choices=['present', 'absent'], type='str'),
        )
    )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    if not HAS_PYVMOMI:
        module.fail_json(msg='pyvmomi is required for this module')

    try:

        dvs_host_states = {
            'absent': {
                'present': state_destroy_vds_host,
                'absent': state_exit_unchanged,
            },
            'present': {
                'update': state_update_vds_host,
                'present': state_exit_unchanged,
                'absent': state_create_vds_host,
            }
        }

        dvs_host_states[module.params['state']][check_vds_host_state(module)](module)

    except vmodl.RuntimeFault as runtime_fault:
        module.fail_json(msg=runtime_fault.msg)
    except vmodl.MethodFault as method_fault:
        module.fail_json(msg=method_fault.msg)
    except Exception as e:
        module.fail_json(msg=str(e))


from ansible.module_utils.basic import *
from ansible.module_utils.vmware import *

if __name__ == '__main__':
    main()

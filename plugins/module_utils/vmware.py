# -*- coding: utf-8 -*-

# Copyright: (c) 2015, Joseph Callen <jcallen () csc.com>
# Copyright: (c) 2018, Ansible Project
# Copyright: (c) 2018, James E. King III (@jeking3) <jking@apache.org>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import atexit
import ansible.module_utils.common._collections_compat as collections_compat
import json
import os
import re
import socket
import ssl
import hashlib
import time
import traceback
import datetime
from collections import OrderedDict
from ansible.module_utils.compat.version import StrictVersion
from random import randint


REQUESTS_IMP_ERR = None
try:
    # requests is required for exception handling of the ConnectionError
    import requests
    HAS_REQUESTS = True
except ImportError:
    REQUESTS_IMP_ERR = traceback.format_exc()
    HAS_REQUESTS = False

PYVMOMI_IMP_ERR = None
try:
    from pyVim import connect
    from pyVmomi import vim, vmodl, VmomiSupport
    HAS_PYVMOMI = True
except ImportError:
    PYVMOMI_IMP_ERR = traceback.format_exc()
    HAS_PYVMOMI = False

from ansible.module_utils._text import to_text, to_native
from ansible.module_utils.six import integer_types, iteritems, string_types, raise_from
from ansible.module_utils.basic import env_fallback, missing_required_lib
from ansible.module_utils.six.moves.urllib.parse import unquote


class TaskError(Exception):
    def __init__(self, *args, **kwargs):
        super(TaskError, self).__init__(*args, **kwargs)


class ApiAccessError(Exception):
    def __init__(self, *args, **kwargs):
        super(ApiAccessError, self).__init__(*args, **kwargs)


def check_answer_question_status(vm):
    """Check whether locked a virtual machine.

    Args:
        vm: Virtual machine management object

    Returns: bool
    """
    if hasattr(vm, "runtime") and vm.runtime.question:
        return True

    return False


def make_answer_response(vm, answers):
    """Make the response contents to answer against locked a virtual machine.

    Args:
        vm: Virtual machine management object
        answers: Answer contents

    Returns: Dict with answer id and number
    Raises: TaskError on failure
    """
    response_list = {}
    for message in vm.runtime.question.message:
        response_list[message.id] = {}
        for choice in vm.runtime.question.choice.choiceInfo:
            response_list[message.id].update({
                choice.label: choice.key
            })

    responses = []
    try:
        for answer in answers:
            responses.append({
                "id": vm.runtime.question.id,
                "response_num": response_list[answer["question"]][answer["response"]]
            })
    except Exception:
        raise TaskError("not found %s or %s or both in the response list" % (answer["question"], answer["response"]))

    return responses


def answer_question(vm, responses):
    """Answer against the question for unlocking a virtual machine.

    Args:
        vm: Virtual machine management object
        responses: Answer contents to unlock a virtual machine
    """
    for response in responses:
        try:
            vm.AnswerVM(response["id"], response["response_num"])
        except Exception as e:
            raise TaskError("answer failed: %s" % to_text(e))


def wait_for_task(task, max_backoff=64, timeout=3600, vm=None, answers=None):
    """Wait for given task using exponential back-off algorithm.

    Args:
        task: VMware task object
        max_backoff: Maximum amount of sleep time in seconds
        timeout: Timeout for the given task in seconds

    Returns: Tuple with True and result for successful task
    Raises: TaskError on failure
    """
    failure_counter = 0
    start_time = time.time()

    while True:
        if check_answer_question_status(vm):
            if answers:
                responses = make_answer_response(vm, answers)
                answer_question(vm, responses)
            else:
                raise TaskError("%s" % to_text(vm.runtime.question.text))
        if time.time() - start_time >= timeout:
            raise TaskError("Timeout")
        if task.info.state == vim.TaskInfo.State.success:
            return True, task.info.result
        if task.info.state == vim.TaskInfo.State.error:
            error_msg = task.info.error
            host_thumbprint = None
            try:
                error_msg = error_msg.msg
                if hasattr(task.info.error, 'thumbprint'):
                    host_thumbprint = task.info.error.thumbprint
            except AttributeError:
                pass
            finally:
                raise_from(TaskError(error_msg, host_thumbprint), task.info.error)
        if task.info.state in [vim.TaskInfo.State.running, vim.TaskInfo.State.queued]:
            sleep_time = min(2 ** failure_counter + randint(1, 1000) / 1000, max_backoff)
            time.sleep(sleep_time)
            failure_counter += 1


def wait_for_vm_ip(content, vm, timeout=300):
    facts = dict()
    interval = 15
    while timeout > 0:
        _facts = gather_vm_facts(content, vm)
        if _facts['ipv4'] or _facts['ipv6']:
            facts = _facts
            break
        time.sleep(interval)
        timeout -= interval

    return facts


def find_obj(content, vimtype, name, first=True, folder=None):
    container = content.viewManager.CreateContainerView(folder or content.rootFolder, recursive=True, type=vimtype)
    # Get all objects matching type (and name if given)
    obj_list = [obj for obj in container.view if not name or to_text(unquote(obj.name)) == to_text(unquote(name))]
    container.Destroy()

    # Return first match or None
    if first:
        if obj_list:
            return obj_list[0]
        return None

    # Return all matching objects or empty list
    return obj_list


def find_dvspg_by_name(dv_switch, portgroup_name):
    portgroup_name = quote_obj_name(portgroup_name)
    portgroups = dv_switch.portgroup

    for pg in portgroups:
        if pg.name == portgroup_name:
            return pg

    return None


def find_object_by_name(content, name, obj_type, folder=None, recurse=True):
    if not isinstance(obj_type, list):
        obj_type = [obj_type]

    name = name.strip()

    objects = get_all_objs(content, obj_type, folder=folder, recurse=recurse)
    for obj in objects:
        try:
            if unquote(obj.name) == name:
                return obj
        except vmodl.fault.ManagedObjectNotFound:
            pass

    return None


def find_all_objects_by_name(content, name, obj_type, folder=None, recurse=True):
    if not isinstance(obj_type, list):
        obj_type = [obj_type]

    name = name.strip()
    result = []

    objects = get_all_objs(content, obj_type, folder=folder, recurse=recurse)
    for obj in objects:
        try:
            if unquote(obj.name) == name:
                result.append(obj)
        except vmodl.fault.ManagedObjectNotFound:
            pass
    return result


def find_cluster_by_name(content, cluster_name, datacenter=None):
    if datacenter and hasattr(datacenter, 'hostFolder'):
        folder = datacenter.hostFolder
    else:
        folder = content.rootFolder

    return find_object_by_name(content, cluster_name, [vim.ClusterComputeResource], folder=folder)


def find_datacenter_by_name(content, datacenter_name):
    return find_object_by_name(content, datacenter_name, [vim.Datacenter])


def get_parent_datacenter(obj):
    """ Walk the parent tree to find the objects datacenter """
    if isinstance(obj, vim.Datacenter):
        return obj
    datacenter = None
    while True:
        if not hasattr(obj, 'parent'):
            break
        obj = obj.parent or obj.parentVApp
        if isinstance(obj, vim.Datacenter):
            datacenter = obj
            break
    return datacenter


def find_datastore_by_name(content, datastore_name, datacenter_name=None):
    return find_object_by_name(content, datastore_name, [vim.Datastore], datacenter_name)


def find_folder_by_name(content, folder_name):
    return find_object_by_name(content, folder_name, [vim.Folder])


def find_folder_by_fqpn(content, folder_name, datacenter_name=None, folder_type=None):
    """
    Find the folder by its given fully qualified path name.
    The Fully Qualified Path Name is I(datacenter)/I(folder type)/folder name/
    for example - Lab/vm/someparent/myfolder is a vm folder in the Lab datacenter.
    """
    # Remove leading/trailing slashes and create list of subfolders
    folder = folder_name.strip('/')
    folder_parts = folder.strip('/').split('/')

    # Process datacenter
    if len(folder_parts) > 0:
        if not datacenter_name:
            datacenter_name = folder_parts[0]
        if datacenter_name == folder_parts[0]:
            folder_parts.pop(0)
    datacenter = find_datacenter_by_name(content, datacenter_name)
    if not datacenter:
        return None

    # Process folder type
    if len(folder_parts) > 0:
        if not folder_type:
            folder_type = folder_parts[0]
        if folder_type == folder_parts[0]:
            folder_parts.pop(0)
    if folder_type in ['vm', 'host', 'datastore', 'network']:
        parent_obj = getattr(datacenter, "%sFolder" % folder_type.lower())
    else:
        return None

    # Process remaining subfolders
    if len(folder_parts) > 0:
        for part in folder_parts:
            folder_obj = None
            for part_obj in parent_obj.childEntity:
                if part_obj.name == part and ('Folder' in part_obj.childType or vim.Folder in part_obj.childType):
                    folder_obj = part_obj
                    parent_obj = part_obj
                    break
            if not folder_obj:
                return None
    else:
        folder_obj = parent_obj
    return folder_obj


def find_dvs_by_name(content, switch_name, folder=None):
    return find_object_by_name(content, switch_name, [vim.DistributedVirtualSwitch], folder=folder)


def find_hostsystem_by_name(content, hostname, datacenter=None):
    if datacenter and hasattr(datacenter, 'hostFolder'):
        folder = datacenter.hostFolder
    else:
        folder = content.rootFolder
    return find_object_by_name(content, hostname, [vim.HostSystem], folder=folder)


def find_resource_pool_by_name(content, resource_pool_name):
    return find_object_by_name(content, resource_pool_name, [vim.ResourcePool])


def find_resource_pool_by_cluster(content, resource_pool_name='Resources', cluster=None):
    return find_object_by_name(content, resource_pool_name, [vim.ResourcePool], folder=cluster)


def find_network_by_name(content, network_name, datacenter_name=None):
    return find_object_by_name(content, network_name, [vim.Network], datacenter_name)


def find_all_networks_by_name(content, network_name, datacenter_name=None):
    return find_all_objects_by_name(content, network_name, [vim.Network], datacenter_name)


def find_vm_by_id(content, vm_id, vm_id_type="vm_name", datacenter=None,
                  cluster=None, folder=None, match_first=False):
    """ UUID is unique to a VM, every other id returns the first match. """
    si = content.searchIndex
    vm = None

    if vm_id_type == 'dns_name':
        vm = si.FindByDnsName(datacenter=datacenter, dnsName=vm_id, vmSearch=True)
    elif vm_id_type == 'uuid':
        # Search By BIOS UUID rather than instance UUID
        vm = si.FindByUuid(datacenter=datacenter, instanceUuid=False, uuid=vm_id, vmSearch=True)
    elif vm_id_type == 'instance_uuid':
        vm = si.FindByUuid(datacenter=datacenter, instanceUuid=True, uuid=vm_id, vmSearch=True)
    elif vm_id_type == 'ip':
        vm = si.FindByIp(datacenter=datacenter, ip=vm_id, vmSearch=True)
    elif vm_id_type == 'vm_name':
        folder = None
        if cluster:
            folder = cluster
        elif datacenter:
            folder = datacenter.hostFolder
        vm = find_vm_by_name(content, vm_id, folder)
    elif vm_id_type == 'inventory_path':
        searchpath = folder
        # get all objects for this path
        f_obj = si.FindByInventoryPath(searchpath)
        if f_obj:
            if isinstance(f_obj, vim.Datacenter):
                f_obj = f_obj.vmFolder
            for c_obj in f_obj.childEntity:
                if not isinstance(c_obj, vim.VirtualMachine):
                    continue
                if c_obj.name == vm_id:
                    vm = c_obj
                    if match_first:
                        break
    return vm


def find_vm_by_name(content, vm_name, folder=None, recurse=True):
    return find_object_by_name(content, vm_name, [vim.VirtualMachine], folder=folder, recurse=recurse)


def find_host_portgroup_by_name(host, portgroup_name):

    for portgroup in host.config.network.portgroup:
        if portgroup.spec.name == portgroup_name:
            return portgroup
    return None


def compile_folder_path_for_object(vobj):
    """ make a /vm/foo/bar/baz like folder path for an object """

    paths = []
    if isinstance(vobj, vim.Folder):
        paths.append(vobj.name)

    thisobj = vobj
    while hasattr(thisobj, 'parent'):
        thisobj = thisobj.parent
        try:
            moid = thisobj._moId
        except AttributeError:
            moid = None
        if moid in ['group-d1', 'ha-folder-root']:
            break
        if isinstance(thisobj, vim.Folder):
            paths.append(thisobj.name)
    paths.reverse()
    return '/' + '/'.join(paths)


def _get_vm_prop(vm, attributes):
    """Safely get a property or return None"""
    result = vm
    for attribute in attributes:
        try:
            result = getattr(result, attribute)
        except (AttributeError, IndexError):
            return None
    return result


def gather_vm_facts(content, vm):
    """ Gather facts from vim.VirtualMachine object. """
    facts = {
        'module_hw': True,
        'hw_name': vm.config.name,
        'hw_power_status': vm.summary.runtime.powerState,
        'hw_guest_full_name': vm.summary.guest.guestFullName,
        'hw_guest_id': vm.summary.guest.guestId,
        'hw_product_uuid': vm.config.uuid,
        'hw_processor_count': vm.config.hardware.numCPU,
        'hw_cores_per_socket': vm.config.hardware.numCoresPerSocket,
        'hw_memtotal_mb': vm.config.hardware.memoryMB,
        'hw_interfaces': [],
        'hw_datastores': [],
        'hw_files': [],
        'hw_esxi_host': None,
        'hw_guest_ha_state': None,
        'hw_is_template': vm.config.template,
        'hw_folder': None,
        'hw_version': vm.config.version,
        'instance_uuid': vm.config.instanceUuid,
        'guest_tools_status': _get_vm_prop(vm, ('guest', 'toolsRunningStatus')),
        'guest_tools_version': _get_vm_prop(vm, ('guest', 'toolsVersion')),
        'guest_question': json.loads(json.dumps(vm.summary.runtime.question, cls=VmomiSupport.VmomiJSONEncoder,
                                                sort_keys=True, strip_dynamic=True)),
        'guest_consolidation_needed': vm.summary.runtime.consolidationNeeded,
        'ipv4': None,
        'ipv6': None,
        'annotation': vm.config.annotation,
        'customvalues': {},
        'snapshots': [],
        'current_snapshot': None,
        'vnc': {},
        'moid': vm._moId,
        'vimref': "vim.VirtualMachine:%s" % vm._moId,
        'advanced_settings': {},
    }

    # facts that may or may not exist
    if vm.summary.runtime.host:
        try:
            host = vm.summary.runtime.host
            facts['hw_esxi_host'] = host.summary.config.name
            facts['hw_cluster'] = host.parent.name if host.parent and isinstance(host.parent, vim.ClusterComputeResource) else None

        except vim.fault.NoPermission:
            # User does not have read permission for the host system,
            # proceed without this value. This value does not contribute or hamper
            # provisioning or power management operations.
            pass
    if vm.summary.runtime.dasVmProtection:
        facts['hw_guest_ha_state'] = vm.summary.runtime.dasVmProtection.dasProtected

    datastores = vm.datastore
    for ds in datastores:
        facts['hw_datastores'].append(ds.info.name)

    try:
        files = vm.config.files
        layout = vm.layout
        if files:
            facts['hw_files'] = [files.vmPathName]
            for item in layout.snapshot:
                for snap in item.snapshotFile:
                    if 'vmsn' in snap:
                        facts['hw_files'].append(snap)
            for item in layout.configFile:
                facts['hw_files'].append(os.path.join(os.path.dirname(files.vmPathName), item))
            for item in vm.layout.logFile:
                facts['hw_files'].append(os.path.join(files.logDirectory, item))
            for item in vm.layout.disk:
                for disk in item.diskFile:
                    facts['hw_files'].append(disk)
    except Exception:
        pass

    facts['hw_folder'] = PyVmomi.get_vm_path(content, vm)

    cfm = content.customFieldsManager
    # Resolve custom values
    for value_obj in vm.summary.customValue:
        kn = value_obj.key
        if cfm is not None and cfm.field:
            for f in cfm.field:
                if f.key == value_obj.key:
                    kn = f.name
                    # Exit the loop immediately, we found it
                    break

        facts['customvalues'][kn] = value_obj.value

    # Resolve advanced settings
    for advanced_setting in vm.config.extraConfig:
        facts['advanced_settings'][advanced_setting.key] = advanced_setting.value

    net_dict = {}
    vmnet = _get_vm_prop(vm, ('guest', 'net'))
    if vmnet:
        for device in vmnet:
            if device.deviceConfigId > 0:
                net_dict[device.macAddress] = list(device.ipAddress)

    if vm.guest.ipAddress:
        if ':' in vm.guest.ipAddress:
            facts['ipv6'] = vm.guest.ipAddress
        else:
            facts['ipv4'] = vm.guest.ipAddress

    ethernet_idx = 0
    for entry in vm.config.hardware.device:
        if not hasattr(entry, 'macAddress'):
            continue

        if entry.macAddress:
            mac_addr = entry.macAddress
            mac_addr_dash = mac_addr.replace(':', '-')
        else:
            mac_addr = mac_addr_dash = None

        if (
            hasattr(entry, "backing")
            and hasattr(entry.backing, "port")
            and hasattr(entry.backing.port, "portKey")
            and hasattr(entry.backing.port, "portgroupKey")
        ):
            port_group_key = entry.backing.port.portgroupKey
            port_key = entry.backing.port.portKey
        else:
            port_group_key = None
            port_key = None

        factname = 'hw_eth' + str(ethernet_idx)
        facts[factname] = {
            'addresstype': entry.addressType,
            'label': entry.deviceInfo.label,
            'macaddress': mac_addr,
            'ipaddresses': net_dict.get(entry.macAddress, None),
            'macaddress_dash': mac_addr_dash,
            'summary': entry.deviceInfo.summary,
            'portgroup_portkey': port_key,
            'portgroup_key': port_group_key,
        }
        facts['hw_interfaces'].append('eth' + str(ethernet_idx))
        ethernet_idx += 1

    snapshot_facts = list_snapshots(vm)
    if 'snapshots' in snapshot_facts:
        facts['snapshots'] = snapshot_facts['snapshots']
        facts['current_snapshot'] = snapshot_facts['current_snapshot']

    facts['vnc'] = get_vnc_extraconfig(vm)

    # Gather vTPM information
    facts['tpm_info'] = {
        'tpm_present': vm.summary.config.tpmPresent if hasattr(vm.summary.config, 'tpmPresent') else None,
        'provider_id': vm.config.keyId.providerId.id if vm.config.keyId else None
    }
    return facts


def ansible_date_time_facts(timestamp):
    # timestamp is a datetime.datetime object
    date_time_facts = {}
    if timestamp is None:
        return date_time_facts

    utctimestamp = timestamp.astimezone(datetime.timezone.utc)

    date_time_facts['year'] = timestamp.strftime('%Y')
    date_time_facts['month'] = timestamp.strftime('%m')
    date_time_facts['weekday'] = timestamp.strftime('%A')
    date_time_facts['weekday_number'] = timestamp.strftime('%w')
    date_time_facts['weeknumber'] = timestamp.strftime('%W')
    date_time_facts['day'] = timestamp.strftime('%d')
    date_time_facts['hour'] = timestamp.strftime('%H')
    date_time_facts['minute'] = timestamp.strftime('%M')
    date_time_facts['second'] = timestamp.strftime('%S')
    date_time_facts['epoch'] = timestamp.strftime('%s')
    date_time_facts['date'] = timestamp.strftime('%Y-%m-%d')
    date_time_facts['time'] = timestamp.strftime('%H:%M:%S')
    date_time_facts['iso8601_micro'] = utctimestamp.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    date_time_facts['iso8601'] = utctimestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
    date_time_facts['iso8601_basic'] = timestamp.strftime("%Y%m%dT%H%M%S%f")
    date_time_facts['iso8601_basic_short'] = timestamp.strftime("%Y%m%dT%H%M%S")
    date_time_facts['tz'] = timestamp.strftime("%Z")
    date_time_facts['tz_offset'] = timestamp.strftime("%z")

    return date_time_facts


def deserialize_snapshot_obj(obj):
    return {'id': obj.id,
            'name': obj.name,
            'description': obj.description,
            'creation_time': obj.createTime,
            'state': obj.state,
            'quiesced': obj.quiesced}


def list_snapshots_recursively(snapshots):
    snapshot_data = []
    for snapshot in snapshots:
        snapshot_data.append(deserialize_snapshot_obj(snapshot))
        snapshot_data = snapshot_data + list_snapshots_recursively(snapshot.childSnapshotList)
    return snapshot_data


def get_current_snap_obj(snapshots, snapob):
    snap_obj = []
    for snapshot in snapshots:
        if snapshot.snapshot == snapob:
            snap_obj.append(snapshot)
        snap_obj = snap_obj + get_current_snap_obj(snapshot.childSnapshotList, snapob)
    return snap_obj


def list_snapshots(vm):
    result = {}
    snapshot = _get_vm_prop(vm, ('snapshot',))
    if not snapshot:
        return result
    if vm.snapshot is None:
        return result

    result['snapshots'] = list_snapshots_recursively(vm.snapshot.rootSnapshotList)
    current_snapref = vm.snapshot.currentSnapshot
    current_snap_obj = get_current_snap_obj(vm.snapshot.rootSnapshotList, current_snapref)
    if current_snap_obj:
        result['current_snapshot'] = deserialize_snapshot_obj(current_snap_obj[0])
    else:
        result['current_snapshot'] = dict()
    return result


def get_vnc_extraconfig(vm):
    result = {}
    for opts in vm.config.extraConfig:
        for optkeyname in ['enabled', 'ip', 'port', 'password']:
            if opts.key.lower() == "remotedisplay.vnc." + optkeyname:
                result[optkeyname] = opts.value
    return result


def vmware_argument_spec():
    return dict(
        hostname=dict(type='str',
                      required=False,
                      fallback=(env_fallback, ['VMWARE_HOST']),
                      ),
        username=dict(type='str',
                      aliases=['user', 'admin'],
                      required=False,
                      fallback=(env_fallback, ['VMWARE_USER'])),
        password=dict(type='str',
                      aliases=['pass', 'pwd'],
                      required=False,
                      no_log=True,
                      fallback=(env_fallback, ['VMWARE_PASSWORD'])),
        port=dict(type='int',
                  default=443,
                  fallback=(env_fallback, ['VMWARE_PORT'])),
        validate_certs=dict(type='bool',
                            required=False,
                            default=True,
                            fallback=(env_fallback, ['VMWARE_VALIDATE_CERTS'])
                            ),
        proxy_host=dict(type='str',
                        required=False,
                        default=None,
                        fallback=(env_fallback, ['VMWARE_PROXY_HOST'])),
        proxy_port=dict(type='int',
                        required=False,
                        default=None,
                        fallback=(env_fallback, ['VMWARE_PROXY_PORT'])),
    )


def connect_to_api(module, disconnect_atexit=True, return_si=False, hostname=None, username=None, password=None, port=None, validate_certs=None,
                   httpProxyHost=None, httpProxyPort=None):
    if module:
        if not hostname:
            hostname = module.params['hostname']
        if not username:
            username = module.params['username']
        if not password:
            password = module.params['password']
        if not httpProxyHost:
            httpProxyHost = module.params.get('proxy_host')
        if not httpProxyPort:
            httpProxyPort = module.params.get('proxy_port')
        if not port:
            port = module.params.get('port', 443)
        if not validate_certs:
            validate_certs = module.params['validate_certs']

    def _raise_or_fail(msg):
        if module is not None:
            module.fail_json(msg=msg)
        raise ApiAccessError(msg)

    if not hostname:
        _raise_or_fail(msg="Hostname parameter is missing."
                       " Please specify this parameter in task or"
                       " export environment variable like 'export VMWARE_HOST=ESXI_HOSTNAME'")

    if not username:
        _raise_or_fail(msg="Username parameter is missing."
                       " Please specify this parameter in task or"
                       " export environment variable like 'export VMWARE_USER=ESXI_USERNAME'")

    if not password:
        _raise_or_fail(msg="Password parameter is missing."
                       " Please specify this parameter in task or"
                       " export environment variable like 'export VMWARE_PASSWORD=ESXI_PASSWORD'")

    if validate_certs and not hasattr(ssl, 'SSLContext'):
        _raise_or_fail(msg='pyVim does not support changing verification mode with python < 2.7.9. Either update '
                           'python or use validate_certs=false.')
    elif validate_certs:
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
        ssl_context.verify_mode = ssl.CERT_REQUIRED
        ssl_context.check_hostname = True
        ssl_context.load_default_certs()
    elif hasattr(ssl, 'SSLContext'):
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
        ssl_context.verify_mode = ssl.CERT_NONE
        ssl_context.check_hostname = False
    else:  # Python < 2.7.9 or RHEL/Centos < 7.4
        ssl_context = None

    service_instance = None

    connect_args = dict(
        host=hostname,
        port=port,
    )
    if ssl_context:
        connect_args.update(sslContext=ssl_context)

    msg_suffix = ''
    try:
        if httpProxyHost:
            msg_suffix = " [proxy: %s:%d]" % (httpProxyHost, httpProxyPort)
            connect_args.update(httpProxyHost=httpProxyHost, httpProxyPort=httpProxyPort)
            smart_stub = connect.SmartStubAdapter(**connect_args)
            session_stub = connect.VimSessionOrientedStub(smart_stub, connect.VimSessionOrientedStub.makeUserLoginMethod(username, password))
            service_instance = vim.ServiceInstance('ServiceInstance', session_stub)
        else:
            connect_args.update(user=username, pwd=password)
            service_instance = connect.SmartConnect(**connect_args)
    except vim.fault.InvalidLogin as invalid_login:
        msg = "Unable to log on to vCenter or ESXi API at %s:%s " % (hostname, port)
        _raise_or_fail(msg="%s as %s: %s" % (msg, username, invalid_login.msg) + msg_suffix)
    except vim.fault.NoPermission as no_permission:
        _raise_or_fail(msg="User %s does not have required permission"
                           " to log on to vCenter or ESXi API at %s:%s : %s" % (username, hostname, port, no_permission.msg))
    except (requests.ConnectionError, ssl.SSLError) as generic_req_exc:
        _raise_or_fail(msg="Unable to connect to vCenter or ESXi API at %s on TCP/%s: %s" % (hostname, port, generic_req_exc))
    except vmodl.fault.InvalidRequest as invalid_request:
        # Request is malformed
        msg = "Failed to get a response from server %s:%s " % (hostname, port)
        _raise_or_fail(msg="%s as request is malformed: %s" % (msg, invalid_request.msg) + msg_suffix)
    except Exception as generic_exc:
        msg = "Unknown error while connecting to vCenter or ESXi API at %s:%s" % (hostname, port) + msg_suffix
        _raise_or_fail(msg="%s : %s" % (msg, generic_exc))

    if service_instance is None:
        msg = "Unknown error while connecting to vCenter or ESXi API at %s:%s" % (hostname, port)
        _raise_or_fail(msg=msg + msg_suffix)

    # Disabling atexit should be used in special cases only.
    # Such as IP change of the ESXi host which removes the connection anyway.
    # Also removal significantly speeds up the return of the module
    if disconnect_atexit:
        atexit.register(connect.Disconnect, service_instance)
    if return_si:
        return service_instance, service_instance.RetrieveContent()
    return service_instance.RetrieveContent()


def get_all_objs(content, vimtype, folder=None, recurse=True):
    if not folder:
        folder = content.rootFolder

    obj = {}
    container = content.viewManager.CreateContainerView(folder, vimtype, recurse)
    for managed_object_ref in container.view:
        try:
            obj.update({managed_object_ref: managed_object_ref.name})
        except vmodl.fault.ManagedObjectNotFound:
            pass
    return obj


def serialize_spec(clonespec):
    """Serialize a clonespec or a relocation spec"""
    data = {}
    attrs = dir(clonespec)
    attrs = [x for x in attrs if not x.startswith('_')]
    for x in attrs:
        xo = getattr(clonespec, x)
        if callable(xo):
            continue
        xt = type(xo)
        if xo is None:
            data[x] = None
        elif isinstance(xo, vim.vm.ConfigSpec):
            data[x] = serialize_spec(xo)
        elif isinstance(xo, vim.vm.RelocateSpec):
            data[x] = serialize_spec(xo)
        elif isinstance(xo, vim.vm.device.VirtualDisk):
            data[x] = serialize_spec(xo)
        elif isinstance(xo, vim.vm.device.VirtualDeviceSpec.FileOperation):
            data[x] = to_text(xo)
        elif isinstance(xo, vim.Description):
            data[x] = {
                'dynamicProperty': serialize_spec(xo.dynamicProperty),
                'dynamicType': serialize_spec(xo.dynamicType),
                'label': serialize_spec(xo.label),
                'summary': serialize_spec(xo.summary),
            }
        elif hasattr(xo, 'name'):
            data[x] = to_text(xo) + ':' + to_text(xo.name)
        elif isinstance(xo, vim.vm.ProfileSpec):
            pass
        elif issubclass(xt, list):
            data[x] = []
            for xe in xo:
                data[x].append(serialize_spec(xe))
        elif issubclass(xt, string_types + integer_types + (float, bool)):
            if issubclass(xt, integer_types):
                data[x] = int(xo)
            else:
                data[x] = to_text(xo)
        elif issubclass(xt, bool):
            data[x] = xo
        elif issubclass(xt, dict):
            data[to_text(x)] = {}
            for k, v in xo.items():
                k = to_text(k)
                data[x][k] = serialize_spec(v)
        else:
            data[x] = str(xt)

    return data


def find_host_by_cluster_datacenter(module, content, datacenter_name, cluster_name, host_name):
    dc = find_datacenter_by_name(content, datacenter_name)
    if dc is None:
        module.fail_json(msg="Unable to find datacenter with name %s" % datacenter_name)
    cluster = find_cluster_by_name(content, cluster_name, datacenter=dc)
    if cluster is None:
        module.fail_json(msg="Unable to find cluster with name %s" % cluster_name)

    for host in cluster.host:
        if host.name == host_name:
            return host, cluster

    return None, cluster


def set_vm_power_state(content, vm, state, force, timeout=0, answers=None):
    """
    Set the power status for a VM determined by the current and
    requested states. force is forceful
    """
    facts = gather_vm_facts(content, vm)
    if state == 'present':
        state = 'poweredon'
    expected_state = state.replace('_', '').replace('-', '').lower()
    current_state = facts['hw_power_status'].lower()
    result = dict(
        changed=False,
        failed=False,
    )

    # Need Force
    if not force and current_state not in ['poweredon', 'poweredoff']:
        result['failed'] = True
        result['msg'] = "Virtual Machine is in %s power state. Force is required!" % current_state
        result['instance'] = gather_vm_facts(content, vm)
        return result

    # State is not already true
    if current_state != expected_state:
        task = None
        try:
            if expected_state == 'poweredoff':
                task = vm.PowerOff()

            elif expected_state == 'poweredon':
                task = vm.PowerOn()

            elif expected_state == 'restarted':
                if current_state in ('poweredon', 'poweringon', 'resetting', 'poweredoff'):
                    task = vm.Reset()
                else:
                    result['failed'] = True
                    result['msg'] = "Cannot restart virtual machine in the current state %s" % current_state

            elif expected_state == 'suspended':
                if current_state in ('poweredon', 'poweringon'):
                    task = vm.Suspend()
                else:
                    result['failed'] = True
                    result['msg'] = 'Cannot suspend virtual machine in the current state %s' % current_state

            elif expected_state in ['shutdownguest', 'rebootguest']:
                if current_state == 'poweredon':
                    if vm.guest.toolsRunningStatus == 'guestToolsRunning':
                        if expected_state == 'shutdownguest':
                            task = vm.ShutdownGuest()
                            if timeout > 0:
                                result.update(wait_for_poweroff(vm, timeout))
                        else:
                            task = vm.RebootGuest()
                        # Set result['changed'] immediately because
                        # shutdown and reboot return None.
                        result['changed'] = True
                    else:
                        result['failed'] = True
                        result['msg'] = "VMware tools should be installed for guest shutdown/reboot"
                elif current_state == 'poweredoff':
                    result['changed'] = False
                else:
                    result['failed'] = True
                    result['msg'] = "Virtual machine %s must be in poweredon state for guest reboot" % vm.name

            else:
                result['failed'] = True
                result['msg'] = "Unsupported expected state provided: %s" % expected_state

        except Exception as e:
            result['failed'] = True
            result['msg'] = to_text(e)

        if task:
            try:
                wait_for_task(task, vm=vm, answers=answers)
            except TaskError as e:
                result['failed'] = True
                result['msg'] = to_text(e)
            finally:
                if task.info.state == 'error':
                    result['failed'] = True
                    result['msg'] = task.info.error.msg
                else:
                    result['changed'] = True

    # need to get new metadata if changed
    result['instance'] = gather_vm_facts(content, vm)

    return result


def wait_for_poweroff(vm, timeout=300):
    result = dict()
    interval = 15
    while timeout > 0:
        if vm.runtime.powerState.lower() == 'poweredoff':
            break
        time.sleep(interval)
        timeout -= interval
    else:
        result['failed'] = True
        result['msg'] = 'Timeout while waiting for VM power off.'
    return result


def is_integer(value, type_of='int'):
    try:
        VmomiSupport.vmodlTypes[type_of](value)
        return True
    except (TypeError, ValueError):
        return False


def is_boolean(value):
    if str(value).lower() in ['true', 'on', 'yes', 'false', 'off', 'no']:
        return True
    return False


def is_truthy(value):
    if str(value).lower() in ['true', 'on', 'yes']:
        return True
    return False


# options is the dict as defined in the module parameters, current_options is
# the list of the currently set options as returned by the vSphere API.
# When truthy_strings_as_bool is True, strings like 'true', 'off' or 'yes'
# are converted to booleans.
def option_diff(options, current_options, truthy_strings_as_bool=True):
    current_options_dict = {}
    for option in current_options:
        current_options_dict[option.key] = option.value

    change_option_list = []
    for option_key, option_value in options.items():
        if truthy_strings_as_bool and is_boolean(option_value):
            option_value = VmomiSupport.vmodlTypes['bool'](is_truthy(option_value))
        elif isinstance(option_value, int):
            option_value = VmomiSupport.vmodlTypes['int'](option_value)
        elif isinstance(option_value, float):
            option_value = VmomiSupport.vmodlTypes['float'](option_value)
        elif isinstance(option_value, str):
            option_value = VmomiSupport.vmodlTypes['string'](option_value)

        if option_key not in current_options_dict or current_options_dict[option_key] != option_value:
            change_option_list.append(vim.option.OptionValue(key=option_key, value=option_value))

    return change_option_list


def quote_obj_name(object_name=None):
    """
    Replace special characters in object name
    with urllib quote equivalent

    """
    if not object_name:
        return None

    SPECIAL_CHARS = OrderedDict({
        '%': '%25',
        '/': '%2f',
        '\\': '%5c'
    })
    for key in SPECIAL_CHARS.keys():
        if key in object_name:
            object_name = object_name.replace(key, SPECIAL_CHARS[key])

    return object_name


class PyVmomi(object):
    def __init__(self, module):
        """
        Constructor
        """
        if not HAS_REQUESTS:
            module.fail_json(msg=missing_required_lib('requests'),
                             exception=REQUESTS_IMP_ERR)

        if not HAS_PYVMOMI:
            module.fail_json(msg=missing_required_lib('PyVmomi'),
                             exception=PYVMOMI_IMP_ERR)

        self.module = module
        self.params = module.params
        self.current_vm_obj = None
        self.si, self.content = connect_to_api(self.module, return_si=True)
        self.custom_field_mgr = []
        if self.content.customFieldsManager:  # not an ESXi
            self.custom_field_mgr = self.content.customFieldsManager.field

    def is_vcenter(self):
        """
        Check if given hostname is vCenter or ESXi host
        Returns: True if given connection is with vCenter server
                 False if given connection is with ESXi server

        """
        api_type = None
        try:
            api_type = self.content.about.apiType
        except (vmodl.RuntimeFault, vim.fault.VimFault) as exc:
            self.module.fail_json(msg="Failed to get status of vCenter server : %s" % exc.msg)

        if api_type == 'VirtualCenter':
            return True
        elif api_type == 'HostAgent':
            return False

    def vcenter_version_at_least(self, version=None):
        """
        Check that the vCenter server is at least a specific version number
        Args:
            version (tuple): a version tuple, for example (6, 7, 0)
        Returns: bool
        """
        if version:
            vc_version = self.content.about.version
            return StrictVersion(vc_version) >= StrictVersion('.'.join(map(str, version)))
        self.module.fail_json(msg='The passed vCenter version: %s is None.' % version)

    def get_cert_fingerprint(self, fqdn, port, proxy_host=None, proxy_port=None):
        if proxy_host:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            sock.connect((
                proxy_host,
                proxy_port))
            command = "CONNECT %s:%d HTTP/1.0\r\n\r\n" % (fqdn, port)
            sock.send(command.encode())
            buf = sock.recv(8192).decode()
            if buf.split()[1] != '200':
                self.module.fail_json(msg="Failed to connect to the proxy")
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            der_cert_bin = ctx.wrap_socket(sock, server_hostname=fqdn).getpeercert(True)
            sock.close()
        else:
            try:
                pem = ssl.get_server_certificate((fqdn, port))
            except Exception:
                self.module.fail_json(msg=f"Cannot connect to host: {fqdn}")
            der_cert_bin = ssl.PEM_cert_to_DER_cert(pem)
        if der_cert_bin:
            string = str(hashlib.sha1(der_cert_bin).hexdigest())
            return ':'.join(a + b for a, b in zip(string[::2], string[1::2]))
        else:
            self.module.fail_json(msg=f"Unable to obtain certificate fingerprint for host: {fqdn}")

    def find_obj(self, vimtype, name, first=True, folder=None):
        container = self.content.viewManager.CreateContainerView(folder or self.content.rootFolder, recursive=True, type=vimtype)
        # Get all objects matching type (and name if given)
        obj_list = [obj for obj in container.view if not name or to_text(unquote(obj.name)) == to_text(unquote(name))]
        container.Destroy()

        # Return first match or None
        if first:
            if obj_list:
                return obj_list[0]
            return None

        # Return all matching objects or empty list
        return obj_list

    def get_managed_objects_properties(self, vim_type, properties=None):
        """
        Look up a Managed Object Reference in vCenter / ESXi Environment
        :param vim_type: Type of vim object e.g, for datacenter - vim.Datacenter
        :param properties: List of properties related to vim object e.g. Name
        :return: local content object
        """
        # Get Root Folder
        root_folder = self.content.rootFolder

        if properties is None:
            properties = ['name']

        # Create Container View with default root folder
        mor = self.content.viewManager.CreateContainerView(root_folder, [vim_type], True)

        # Create Traversal spec
        traversal_spec = vmodl.query.PropertyCollector.TraversalSpec(
            name="traversal_spec",
            path='view',
            skip=False,
            type=vim.view.ContainerView
        )

        # Create Property Spec
        property_spec = vmodl.query.PropertyCollector.PropertySpec(
            type=vim_type,  # Type of object to retrieved
            all=False,
            pathSet=properties
        )

        # Create Object Spec
        object_spec = vmodl.query.PropertyCollector.ObjectSpec(
            obj=mor,
            skip=True,
            selectSet=[traversal_spec]
        )

        # Create Filter Spec
        filter_spec = vmodl.query.PropertyCollector.FilterSpec(
            objectSet=[object_spec],
            propSet=[property_spec],
            reportMissingObjectsInResults=False
        )

        return self.content.propertyCollector.RetrieveContents([filter_spec])

    # Virtual Machine related functions
    def get_vm(self):
        """
        Find unique virtual machine either by UUID, MoID or Name.
        Returns: virtual machine object if found, else None.

        """
        vm_obj = None
        user_desired_path = None
        use_instance_uuid = self.params.get('use_instance_uuid') or False
        if 'uuid' in self.params and self.params['uuid']:
            if not use_instance_uuid:
                vm_obj = find_vm_by_id(self.content, vm_id=self.params['uuid'], vm_id_type="uuid")
            elif use_instance_uuid:
                vm_obj = find_vm_by_id(self.content,
                                       vm_id=self.params['uuid'],
                                       vm_id_type="instance_uuid")
        elif 'name' in self.params and self.params['name']:
            objects = self.get_managed_objects_properties(vim_type=vim.VirtualMachine, properties=['name'])
            vms = []

            for temp_vm_object in objects:
                if (
                    len(temp_vm_object.propSet) == 1
                    and unquote(temp_vm_object.propSet[0].val) == self.params["name"]
                ):
                    vms.append(temp_vm_object.obj)

            # get_managed_objects_properties may return multiple virtual machine,
            # following code tries to find user desired one depending upon the folder specified.
            if len(vms) > 1:
                # We have found multiple virtual machines, decide depending upon folder value
                if self.params['folder'] is None or self.params['datacenter'] is None:
                    self.module.fail_json(msg="Multiple virtual machines with same name [%s] found, "
                                          "try to specify folder and / or datacenter to ensure uniqueness "
                                          "of the virtual machine" % self.params['name'],
                                          details="Please see documentation of the vmware_guest module "
                                          "for folder parameter.")

                # Get folder path where virtual machine is located
                # User provided folder where user thinks virtual machine is present
                user_folder = self.params['folder']
                # User defined datacenter
                user_defined_dc = self.params['datacenter']
                # User defined datacenter's object
                datacenter_obj = find_datacenter_by_name(self.content, self.params['datacenter'])
                # Get Path for Datacenter
                dcpath = compile_folder_path_for_object(vobj=datacenter_obj)

                # Nested folder does not return trailing /
                if not dcpath.endswith('/'):
                    dcpath += '/'

                if user_folder in [None, '', '/']:
                    # User provided blank value or
                    # User provided only root value, we fail
                    self.module.fail_json(msg="vmware_guest found multiple virtual machines with same "
                                          "name [%s], please specify folder path other than blank "
                                          "or '/'" % self.params['name'])
                elif user_folder.startswith('/vm/'):
                    # User provided nested folder under VMware default vm folder i.e. folder = /vm/india/finance
                    user_desired_path = "%s%s%s" % (dcpath, user_defined_dc, user_folder)
                else:
                    # User defined datacenter is not nested i.e. dcpath = '/' , or
                    # User defined datacenter is nested i.e. dcpath = '/F0/DC0' or
                    # User provided folder starts with / and datacenter i.e. folder = /ha-datacenter/ or
                    # User defined folder starts with datacenter without '/' i.e.
                    # folder = DC0/vm/india/finance or
                    # folder = DC0/vm
                    user_desired_path = user_folder

                for vm in vms:
                    # Check if user has provided same path as virtual machine
                    actual_vm_folder_path = self.get_vm_path(content=self.content, vm_name=vm)
                    if not actual_vm_folder_path.startswith("%s%s" % (dcpath, user_defined_dc)):
                        continue
                    if user_desired_path in actual_vm_folder_path:
                        vm_obj = vm
                        break
            elif vms:
                # Unique virtual machine found.
                actual_vm_folder_path = self.get_vm_path(content=self.content, vm_name=vms[0])
                if self.params.get('folder') is None:
                    vm_obj = vms[0]
                elif self.params['folder'] in actual_vm_folder_path:
                    vm_obj = vms[0]
        elif 'moid' in self.params and self.params['moid']:
            vm_obj = VmomiSupport.templateOf('VirtualMachine')(self.params['moid'], self.si._stub)
            try:
                getattr(vm_obj, 'name')
            except vmodl.fault.ManagedObjectNotFound:
                vm_obj = None

        if vm_obj:
            self.current_vm_obj = vm_obj

        return vm_obj

    def gather_facts(self, vm):
        """
        Gather facts of virtual machine.
        Args:
            vm: Name of virtual machine.

        Returns: Facts dictionary of the given virtual machine.

        """
        return gather_vm_facts(self.content, vm)

    @staticmethod
    def get_vm_path(content, vm_name):
        """
        Find the path of virtual machine.
        Args:
            content: VMware content object
            vm_name: virtual machine managed object

        Returns: Folder of virtual machine if exists, else None

        """
        folder_name = None
        folder = vm_name.parent
        if folder:
            folder_name = folder.name
            fp = folder.parent
            # climb back up the tree to find our path, stop before the root folder
            while fp is not None and fp.name is not None and fp != content.rootFolder:
                folder_name = fp.name + '/' + folder_name
                try:
                    fp = fp.parent
                except Exception:
                    break
            folder_name = '/' + folder_name
        return folder_name

    def get_vm_or_template(self, template_name=None):
        """
        Find the virtual machine or virtual machine template using name
        used for cloning purpose.
        Args:
            template_name: Name of virtual machine or virtual machine template

        Returns: virtual machine or virtual machine template object

        """
        template_obj = None
        if not template_name:
            return template_obj

        if "/" in template_name:
            vm_obj_path = os.path.dirname(template_name)
            vm_obj_name = os.path.basename(template_name)
            template_obj = find_vm_by_id(self.content, vm_obj_name, vm_id_type="inventory_path", folder=vm_obj_path)
            if template_obj:
                return template_obj
        else:
            template_obj = find_vm_by_id(self.content, vm_id=template_name, vm_id_type="uuid")
            if template_obj:
                return template_obj

            objects = self.get_managed_objects_properties(vim_type=vim.VirtualMachine, properties=['name'])
            templates = []

            for temp_vm_object in objects:
                if len(temp_vm_object.propSet) != 1:
                    continue
                for temp_vm_object_property in temp_vm_object.propSet:
                    if temp_vm_object_property.val == template_name:
                        templates.append(temp_vm_object.obj)
                        break

            if len(templates) > 1:
                # We have found multiple virtual machine templates
                self.module.fail_json(msg="Multiple virtual machines or templates with same name [%s] found." % template_name)
            elif templates:
                template_obj = templates[0]

        return template_obj

    # Cluster related functions
    def find_cluster_by_name(self, cluster_name, datacenter_name=None):
        """
        Find Cluster by name in given datacenter
        Args:
            cluster_name: Name of cluster name to find
            datacenter_name: (optional) Name of datacenter

        Returns: True if found

        """
        return find_cluster_by_name(self.content, cluster_name, datacenter=datacenter_name)

    def get_all_hosts_by_cluster(self, cluster_name):
        """
        Get all hosts from cluster by cluster name
        Args:
            cluster_name: Name of cluster

        Returns: List of hosts

        """
        cluster_obj = self.find_cluster_by_name(cluster_name=cluster_name)
        if cluster_obj:
            return list(cluster_obj.host)
        else:
            return []

    # Hosts related functions
    def find_hostsystem_by_name(self, host_name, datacenter=None):
        """
        Find Host by name
        Args:
            host_name: Name of ESXi host
            datacenter: (optional) Datacenter of ESXi resides

        Returns: True if found

        """
        return find_hostsystem_by_name(self.content, hostname=host_name, datacenter=datacenter)

    def get_all_host_objs(self, cluster_name=None, esxi_host_name=None):
        """
        Get all host system managed object

        Args:
            cluster_name: Name of Cluster
            esxi_host_name: Name of ESXi server

        Returns: A list of all host system managed objects, else empty list

        """
        host_obj_list = []
        if not self.is_vcenter():
            hosts = get_all_objs(self.content, [vim.HostSystem]).keys()
            if hosts:
                host_obj_list.append(list(hosts)[0])
        else:
            if cluster_name:
                cluster_obj = self.find_cluster_by_name(cluster_name=cluster_name)
                if cluster_obj:
                    host_obj_list = list(cluster_obj.host)
                else:
                    self.module.fail_json(changed=False, msg="Cluster '%s' not found" % cluster_name)
            elif esxi_host_name:
                if isinstance(esxi_host_name, str):
                    esxi_host_name = [esxi_host_name]

                for host in esxi_host_name:
                    esxi_host_obj = self.find_hostsystem_by_name(host_name=host)
                    if esxi_host_obj:
                        host_obj_list.append(esxi_host_obj)
                    else:
                        self.module.fail_json(changed=False, msg="ESXi '%s' not found" % host)

        return host_obj_list

    def host_version_at_least(self, version=None, vm_obj=None, host_name=None):
        """
        Check that the ESXi Host is at least a specific version number
        Args:
            vm_obj: virtual machine object, required one of vm_obj, host_name
            host_name (string): ESXi host name
            version (tuple): a version tuple, for example (6, 7, 0)
        Returns: bool
        """
        if vm_obj:
            host_system = vm_obj.summary.runtime.host
        elif host_name:
            host_system = self.find_hostsystem_by_name(host_name=host_name)
        else:
            self.module.fail_json(msg='VM object or ESXi host name must be set one.')
        if host_system and version:
            host_version = host_system.summary.config.product.version
            return StrictVersion(host_version) >= StrictVersion('.'.join(map(str, version)))
        else:
            self.module.fail_json(msg='Unable to get the ESXi host from vm: %s, or hostname %s,'
                                      'or the passed ESXi version: %s is None.' % (vm_obj, host_name, version))

    # Network related functions
    @staticmethod
    def find_host_portgroup_by_name(host, portgroup_name):
        """
        Find Portgroup on given host
        Args:
            host: Host config object
            portgroup_name: Name of portgroup

        Returns: True if found else False

        """
        for portgroup in host.config.network.portgroup:
            if portgroup.spec.name == portgroup_name:
                return portgroup
        return False

    def get_all_port_groups_by_host(self, host_system):
        """
        Get all Port Group by host
        Args:
            host_system: Name of Host System

        Returns: List of Port Group Spec
        """
        pgs_list = []
        for pg in host_system.config.network.portgroup:
            pgs_list.append(pg)
        return pgs_list

    def find_network_by_name(self, network_name=None):
        """
        Get network specified by name
        Args:
            network_name: Name of network

        Returns: List of network managed objects
        """
        networks = []

        if not network_name:
            return networks

        objects = self.get_managed_objects_properties(vim_type=vim.Network, properties=['name'])

        for temp_vm_object in objects:
            if len(temp_vm_object.propSet) != 1:
                continue
            for temp_vm_object_property in temp_vm_object.propSet:
                if temp_vm_object_property.val == network_name:
                    networks.append(temp_vm_object.obj)
                    break
        return networks

    def network_exists_by_name(self, network_name=None):
        """
        Check if network with a specified name exists or not
        Args:
            network_name: Name of network

        Returns: True if network exists else False
        """
        ret = False
        if not network_name:
            return ret
        ret = True if self.find_network_by_name(network_name=network_name) else False
        return ret

    # Datacenter
    def find_datacenter_by_name(self, datacenter_name):
        """
        Get datacenter managed object by name

        Args:
            datacenter_name: Name of datacenter

        Returns: datacenter managed object if found else None

        """
        return find_datacenter_by_name(self.content, datacenter_name=datacenter_name)

    def is_datastore_valid(self, datastore_obj=None):
        """
        Check if datastore selected is valid or not
        Args:
            datastore_obj: datastore managed object

        Returns: True if datastore is valid, False if not
        """
        if not datastore_obj \
           or datastore_obj.summary.maintenanceMode != 'normal' \
           or not datastore_obj.summary.accessible:
            return False
        return True

    def find_datastore_by_name(self, datastore_name, datacenter_name=None):
        """
        Get datastore managed object by name
        Args:
            datastore_name: Name of datastore
            datacenter_name: Name of datacenter where the datastore resides.  This is needed because Datastores can be
            shared across Datacenters, so we need to specify the datacenter to assure we get the correct Managed Object Reference

        Returns: datastore managed object if found else None

        """
        return find_datastore_by_name(self.content, datastore_name=datastore_name, datacenter_name=datacenter_name)

    def find_folder_by_name(self, folder_name):
        """
        Get vm folder managed object by name
        Args:
            folder_name: Name of the vm folder

        Returns: vm folder managed object if found else None

        """
        return find_folder_by_name(self.content, folder_name=folder_name)

    def find_folder_by_fqpn(self, folder_name, datacenter_name=None, folder_type=None):
        """
        Get a unique folder managed object by specifying its Fully Qualified Path Name
        as datacenter/folder_type/sub1/sub2
        Args:
            folder_name: Fully Qualified Path Name folder name
            datacenter_name: Name of the datacenter, taken from Fully Qualified Path Name if not defined
            folder_type: Type of folder, vm, host, datastore or network,
                         taken from Fully Qualified Path Name if not defined

        Returns: folder managed object if found, else None

        """
        return find_folder_by_fqpn(self.content, folder_name=folder_name, datacenter_name=datacenter_name, folder_type=folder_type)

    # Datastore cluster
    def find_datastore_cluster_by_name(self, datastore_cluster_name, datacenter=None, folder=None):
        """
        Get datastore cluster managed object by name
        Args:
            datastore_cluster_name: Name of datastore cluster
            datacenter: Managed object of the datacenter
            folder: Managed object of the folder which holds datastore

        Returns: Datastore cluster managed object if found else None

        """
        if datacenter and hasattr(datacenter, 'datastoreFolder'):
            folder = datacenter.datastoreFolder
        if not folder:
            folder = self.content.rootFolder

        data_store_clusters = get_all_objs(self.content, [vim.StoragePod], folder=folder)
        for dsc in data_store_clusters:
            if dsc.name == datastore_cluster_name:
                return dsc
        return None

    def get_recommended_datastore(self, datastore_cluster_obj=None):
        """
        Return Storage DRS recommended datastore from datastore cluster
        Args:
            datastore_cluster_obj: datastore cluster managed object

        Returns: Name of recommended datastore from the given datastore cluster

        """
        if datastore_cluster_obj is None:
            return None
        # Check if Datastore Cluster provided by user is SDRS ready
        sdrs_status = datastore_cluster_obj.podStorageDrsEntry.storageDrsConfig.podConfig.enabled
        if sdrs_status:
            # We can get storage recommendation only if SDRS is enabled on given datastorage cluster
            pod_sel_spec = vim.storageDrs.PodSelectionSpec()
            pod_sel_spec.storagePod = datastore_cluster_obj
            storage_spec = vim.storageDrs.StoragePlacementSpec()
            storage_spec.podSelectionSpec = pod_sel_spec
            storage_spec.type = 'create'

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
            if isinstance(ds, vim.Datastore) and ds.summary.freeSpace > datastore_freespace:
                # If datastore field is provided, filter destination datastores
                if not self.is_datastore_valid(datastore_obj=ds):
                    continue

                datastore = ds
                datastore_freespace = ds.summary.freeSpace
        if datastore:
            return datastore.name
        return None

    # Resource pool
    def find_resource_pool_by_name(self, resource_pool_name='Resources', folder=None):
        """
        Get resource pool managed object by name
        Args:
            resource_pool_name: Name of resource pool

        Returns: Resource pool managed object if found else None

        """
        if not folder:
            folder = self.content.rootFolder

        resource_pools = get_all_objs(self.content, [vim.ResourcePool], folder=folder)
        for rp in resource_pools:
            if rp.name == resource_pool_name:
                return rp
        return None

    def find_resource_pool_by_cluster(self, resource_pool_name='Resources', cluster=None):
        """
        Get resource pool managed object by cluster object
        Args:
            resource_pool_name: Name of resource pool
            cluster: Managed object of cluster

        Returns: Resource pool managed object if found else None

        """
        desired_rp = None
        if not cluster:
            return desired_rp

        if resource_pool_name != 'Resources':
            # Resource pool name is different than default 'Resources'
            resource_pools = cluster.resourcePool.resourcePool
            if resource_pools:
                for rp in resource_pools:
                    if rp.name == resource_pool_name:
                        desired_rp = rp
                        break
        else:
            desired_rp = cluster.resourcePool

        return desired_rp

    # VMDK stuff
    def vmdk_disk_path_split(self, vmdk_path):
        """
        Takes a string in the format

            [datastore_name] path/to/vm_name.vmdk

        Returns a tuple with multiple strings:

        1. datastore_name: The name of the datastore (without brackets)
        2. vmdk_fullpath: The "path/to/vm_name.vmdk" portion
        3. vmdk_filename: The "vm_name.vmdk" portion of the string (os.path.basename equivalent)
        4. vmdk_folder: The "path/to/" portion of the string (os.path.dirname equivalent)
        """
        try:
            datastore_name = re.match(r'^\[(.*?)\]', vmdk_path, re.DOTALL).groups()[0]
            vmdk_fullpath = re.match(r'\[.*?\] (.*)$', vmdk_path).groups()[0]
            vmdk_filename = os.path.basename(vmdk_fullpath)
            vmdk_folder = os.path.dirname(vmdk_fullpath)
            return datastore_name, vmdk_fullpath, vmdk_filename, vmdk_folder
        except (IndexError, AttributeError) as e:
            self.module.fail_json(msg="Bad path '%s' for filename disk vmdk image: %s" % (vmdk_path, to_native(e)))

    def find_vmdk_file(self, datastore_obj, vmdk_fullpath, vmdk_filename, vmdk_folder):
        """
        Return vSphere file object or fail_json
        Args:
            datastore_obj: Managed object of datastore
            vmdk_fullpath: Path of VMDK file e.g., path/to/vm/vmdk_filename.vmdk
            vmdk_filename: Name of vmdk e.g., VM0001_1.vmdk
            vmdk_folder: Base dir of VMDK e.g, path/to/vm

        """

        browser = datastore_obj.browser
        datastore_name = datastore_obj.name
        datastore_name_sq = "[" + datastore_name + "]"
        if browser is None:
            self.module.fail_json(msg="Unable to access browser for datastore %s" % datastore_name)

        detail_query = vim.host.DatastoreBrowser.FileInfo.Details(
            fileOwner=True,
            fileSize=True,
            fileType=True,
            modification=True
        )
        search_spec = vim.host.DatastoreBrowser.SearchSpec(
            details=detail_query,
            matchPattern=[vmdk_filename],
            searchCaseInsensitive=True,
        )
        search_res = browser.SearchSubFolders(
            datastorePath=datastore_name_sq,
            searchSpec=search_spec
        )

        changed = False
        vmdk_path = datastore_name_sq + " " + vmdk_fullpath
        try:
            changed, result = wait_for_task(search_res)
        except TaskError as task_e:
            self.module.fail_json(msg=to_native(task_e))

        if not changed:
            self.module.fail_json(msg="No valid disk vmdk image found for path %s" % vmdk_path)

        target_folder_paths = [
            datastore_name_sq + " " + vmdk_folder + '/',
            datastore_name_sq + " " + vmdk_folder,
        ]

        for file_result in search_res.info.result:
            for f in getattr(file_result, 'file'):
                if f.path == vmdk_filename and file_result.folderPath in target_folder_paths:
                    return f

        self.module.fail_json(msg="No vmdk file found for path specified [%s]" % vmdk_path)

    def find_first_class_disk_by_name(self, disk_name, datastore_obj):
        """
        Get first-class disk managed object by name
        Args:
            disk_name: Name of the first-class disk
            datastore_obj: Managed object of datastore

        Returns: First-class disk managed object if found else None

        """

        if self.is_vcenter():
            for id in self.content.vStorageObjectManager.ListVStorageObject(datastore_obj):
                disk = self.content.vStorageObjectManager.RetrieveVStorageObject(id, datastore_obj)
                if disk.config.name == disk_name:
                    return disk
        else:
            for id in self.content.vStorageObjectManager.HostListVStorageObject(datastore_obj):
                disk = self.content.vStorageObjectManager.HostRetrieveVStorageObject(id, datastore_obj)
                if disk.config.name == disk_name:
                    return disk

        return None

    def find_first_class_disks(self, datastore_obj):
        """
        Get first-class disks managed object
        Args:
            datastore_obj: Managed object of datastore

        Returns: First-class disks managed object if found else None

        """

        disks = []

        if self.is_vcenter():
            for id in self.content.vStorageObjectManager.ListVStorageObject(datastore_obj):
                disks.append(self.content.vStorageObjectManager.RetrieveVStorageObject(id, datastore_obj))

        else:
            for id in self.content.vStorageObjectManager.HostListVStorageObject(datastore_obj):
                disks.append(self.content.vStorageObjectManager.HostRetrieveVStorageObject(id, datastore_obj))

        if disks == []:
            return None
        else:
            return disks
    #
    # Conversion to JSON
    #

    def _deepmerge(self, d, u):
        """
        Deep merges u into d.

        Credit:
          https://bit.ly/2EDOs1B (stackoverflow question 3232943)
        License:
          cc-by-sa 3.0 (https://creativecommons.org/licenses/by-sa/3.0/)
        Changes:
          using collections_compat for compatibility

        Args:
          - d (dict): dict to merge into
          - u (dict): dict to merge into d

        Returns:
          dict, with u merged into d
        """
        for k, v in iteritems(u):
            if isinstance(v, collections_compat.Mapping):
                d[k] = self._deepmerge(d.get(k, {}), v)
            else:
                d[k] = v
        return d

    def _extract(self, data, remainder):
        """
        This is used to break down dotted properties for extraction.

        Args:
          - data (dict): result of _jsonify on a property
          - remainder: the remainder of the dotted property to select

        Return:
          dict
        """
        result = dict()
        if '.' not in remainder:
            result[remainder] = data[remainder]
            return result
        key, remainder = remainder.split('.', 1)
        if isinstance(data, list):
            temp_ds = []
            for i in range(len(data)):
                temp_ds.append(self._extract(data[i][key], remainder))
            result[key] = temp_ds
        else:
            result[key] = self._extract(data[key], remainder)
        return result

    def _jsonify(self, obj):
        """
        Convert an object from pyVmomi into JSON.

        Args:
          - obj (object): vim object

        Return:
          dict
        """
        return json.loads(json.dumps(obj, cls=VmomiSupport.VmomiJSONEncoder,
                                     sort_keys=True, strip_dynamic=True))

    def to_json(self, obj, properties=None):
        """
        Convert a vSphere (pyVmomi) Object into JSON.  This is a deep
        transformation.  The list of properties is optional - if not
        provided then all properties are deeply converted.  The resulting
        JSON is sorted to improve human readability.

        Args:
          - obj (object): vim object
          - properties (list, optional): list of properties following
                the property collector specification, for example:
                ["config.hardware.memoryMB", "name", "overallStatus"]
                default is a complete object dump, which can be large

        Return:
          dict
        """
        result = dict()
        if properties:
            for prop in properties:
                try:
                    if '.' in prop:
                        key, remainder = prop.split('.', 1)
                        tmp = dict()
                        tmp[key] = self._extract(self._jsonify(getattr(obj, key)), remainder)
                        self._deepmerge(result, tmp)
                    else:
                        result[prop] = self._jsonify(getattr(obj, prop))
                        # To match gather_vm_facts output
                        prop_name = prop
                        if prop.lower() == '_moid':
                            prop_name = 'moid'
                        elif prop.lower() == '_vimref':
                            prop_name = 'vimref'
                        result[prop_name] = result[prop]
                except (AttributeError, KeyError):
                    self.module.fail_json(msg="Property '{0}' not found.".format(prop))
        else:
            result = self._jsonify(obj)
        return result

    def get_folder_path(self, cur):
        full_path = '/' + cur.name
        while hasattr(cur, 'parent') and cur.parent:
            if cur.parent == self.content.rootFolder:
                break
            cur = cur.parent
            full_path = '/' + cur.name + full_path
        return full_path

    def find_obj_by_moid(self, object_type, moid):
        """
        Get Managed Object based on an object type and moid.
        If you'd like to search for a virtual machine, recommended you use get_vm method.

        Args:
          - object_type: Managed Object type
                It is possible to specify types the following.
                ["Datacenter", "ClusterComputeResource", "ResourcePool", "Folder", "HostSystem",
                 "VirtualMachine", "DistributedVirtualSwitch", "DistributedVirtualPortgroup", "Datastore"]
          - moid: moid of Managed Object
        :return: Managed Object if it exists else None
        """

        obj = VmomiSupport.templateOf(object_type)(moid, self.si._stub)
        try:
            getattr(obj, 'name')
        except vmodl.fault.ManagedObjectNotFound:
            obj = None

        return obj

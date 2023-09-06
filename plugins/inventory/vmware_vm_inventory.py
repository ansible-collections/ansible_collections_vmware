# Copyright: (c) 2018, Ansible Project
# Copyright: (c) 2018, Abhijeet Kasurde <akasurde@redhat.com>
# Copyright: (c) 2020, dacrystal
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
    name: vmware_vm_inventory
    short_description: VMware Guest inventory source
    author:
      - Abhijeet Kasurde (@Akasurde)
    description:
        - Get virtual machines as inventory hosts from VMware environment.
        - Uses any file which ends with vmware.yml, vmware.yaml, vmware_vm_inventory.yml, or vmware_vm_inventory.yaml as a YAML configuration file.
    extends_documentation_fragment:
      - inventory_cache
      - constructed
    requirements:
      - "requests >= 2.3"
      - "vSphere Automation SDK - For tag feature"
    options:
        hostname:
            description:
            - Name or IP of vCenter or ESXi server.
            - Accepts vault encrypted variable.
            required: true
            env:
              - name: VMWARE_HOST
              - name: VMWARE_SERVER
        username:
            description:
            - Name of vSphere user.
            - Accepts vault encrypted variable.
            required: true
            env:
              - name: VMWARE_USER
              - name: VMWARE_USERNAME
        password:
            description:
            - Password of vSphere user.
            - Accepts vault encrypted variable.
            required: true
            env:
              - name: VMWARE_PASSWORD
        port:
            description: Port number used to connect to vCenter or ESXi Server.
            default: 443
            type: int
            env:
              - name: VMWARE_PORT
        validate_certs:
            description:
            - Allows connection when SSL certificates are not valid.
            - Set to C(false) when certificates are not trusted.
            default: true
            type: bool
            env:
              - name: VMWARE_VALIDATE_CERTS
        with_tags:
            description:
            - Include tags and associated virtual machines.
            - Requires 'vSphere Automation SDK' library to be installed on the given controller machine.
            - Please refer following URLs for installation steps
            - U(https://code.vmware.com/web/sdk/7.0/vsphere-automation-python)
            default: false
            type: bool
        hostnames:
            description:
            - A list of templates in order of precedence to compose inventory_hostname.
            - Ignores template if resulted in an empty string or None value.
            - You can use property specified in I(properties) as variables in the template.
            type: list
            elements: string
            default: ['config.name + "_" + config.uuid']
        properties:
            description:
            - Specify the list of VMware schema properties associated with the VM.
            - These properties will be populated in hostvars of the given VM.
            - Each value in the list can be a path to a specific property in VM object or a path to a collection of VM objects.
            - C(config.name), C(config.uuid) are required properties if C(hostnames) is set to default.
            - C(config.guestId), C(summary.runtime.powerState) are required if C(keyed_groups) is set to default.
            - Please make sure that all the properties that are used in other parameters are included in this options.
            - In addition to VM properties, the following are special values
            - Use C(customValue) to populate virtual machine's custom attributes. C(customValue) is only supported by vCenter and not by ESXi.
            - Use C(all) to populate all the properties of the virtual machine.
              The value C(all) is time consuming operation, do not use unless required absolutely.
            - Please refer more VMware guest attributes which can be used as properties
              U(https://docs.ansible.com/ansible/latest/collections/community/vmware/docsite/vmware_scenarios/vmware_inventory_vm_attributes.html)
            type: list
            elements: string
            default: [ 'name', 'config.cpuHotAddEnabled', 'config.cpuHotRemoveEnabled',
                       'config.instanceUuid', 'config.hardware.numCPU', 'config.template',
                       'config.name', 'config.uuid', 'guest.hostName', 'guest.ipAddress',
                       'guest.guestId', 'guest.guestState', 'runtime.maxMemoryUsage',
                       'customValue', 'summary.runtime.powerState', 'config.guestId',
                       ]
        with_nested_properties:
            description:
            - This option transform flatten properties name to nested dictionary.
            - From 1.10.0 and onwards, default value is set to C(true).
            type: bool
            default: true
        keyed_groups:
            description:
            - Add hosts to group based on the values of a variable.
            type: list
            default: [
                {key: 'config.guestId', separator: ''},
                {key: 'summary.runtime.powerState', separator: ''},
            ]
        filters:
            description:
            - This option allows client-side filtering hosts with jinja templating.
            - When server-side filtering is introduced, it should be preferred over this.
            type: list
            elements: str
            default: []
        resources:
            description:
            - A list of resources to limit search scope.
            - Each resource item is represented by exactly one C('vim_type_snake_case):C(list of resource names) pair and optional nested I(resources)
            - Key name is based on snake case of a vim type name; e.g C(host_system) correspond to C(vim.HostSystem)
            - See  L(VIM Types,https://pubs.vmware.com/vi-sdk/visdk250/ReferenceGuide/index-mo_types.html)
            required: false
            type: list
            elements: dict
            default: []
        with_path:
            description:
            - Include virtual machines path.
            - Set this option to a string value to replace root name from I('Datacenters').
            default: false
            type: bool
        with_sanitized_property_name:
            description:
                - This option allows property name sanitization to create safe property names for use in Ansible.
                - Also, transforms property name to snake case.
            type: bool
            default: false
        proxy_host:
          description:
          - Address of a proxy that will receive all HTTPS requests and relay them.
          - The format is a hostname or a IP.
          - This feature depends on a version of pyvmomi>=v6.7.1.2018.12.
          type: str
          required: false
          env:
            - name: VMWARE_PROXY_HOST
        proxy_port:
          description:
          - Port of the HTTP proxy that will receive all HTTPS requests and relay them.
          type: int
          required: false
          env:
            - name: VMWARE_PROXY_PORT
'''

EXAMPLES = r'''
# Sample configuration file for VMware Guest dynamic inventory
    plugin: community.vmware.vmware_vm_inventory
    strict: false
    hostname: 10.65.223.31
    username: administrator@vsphere.local
    password: Esxi@123$%
    validate_certs: false
    with_tags: true

# Gather minimum set of properties for VMware guest
    plugin: community.vmware.vmware_vm_inventory
    strict: false
    hostname: 10.65.223.31
    username: administrator@vsphere.local
    password: Esxi@123$%
    validate_certs: false
    properties:
    - 'name'
    - 'guest.ipAddress'
    - 'config.name'
    - 'config.uuid'

# Create Groups based upon VMware Tools status
    plugin: community.vmware.vmware_vm_inventory
    strict: false
    hostname: 10.65.223.31
    username: administrator@vsphere.local
    password: Esxi@123$%
    validate_certs: false
    properties:
    - 'name'
    - 'config.name'
    - 'guest.toolsStatus'
    - 'guest.toolsRunningStatus'
    hostnames:
    - config.name
    keyed_groups:
    - key: guest.toolsStatus
      separator: ''
    - key: guest.toolsRunningStatus
      separator: ''

# Filter VMs based upon condition
    plugin: community.vmware.vmware_vm_inventory
    strict: false
    hostname: 10.65.223.31
    username: administrator@vsphere.local
    password: Esxi@123$%
    validate_certs: false
    properties:
    - 'runtime.powerState'
    - 'config.name'
    filters:
    - runtime.powerState == "poweredOn"
    hostnames:
    - config.name

# Filter VM's based on OR conditions
    plugin: community.vmware.vmware_vm_inventory
    strict: false
    hostname: 10.65.223.31
    username: administrator@vsphere.local
    password: Esxi@123$%
    validate_certs: false
    properties:
    - 'name'
    - 'config.name'
    - 'guest.ipAddress'
    - 'guest.toolsStatus'
    - 'guest.toolsRunningStatus'
    - 'config.guestFullName'
    - 'config.guestId'
    hostnames:
    - 'config.name'
    filters:
    - config.guestId == "rhel7_64Guest" or config.name == "rhel_20_04_empty"

# Filter VM's based on regex conditions
    plugin: community.vmware.vmware_vm_inventory
    strict: false
    hostname: 10.65.223.31
    username: administrator@vsphere.local
    password: Esxi@123$%
    validate_certs: false
    properties:
    - 'config.name'
    - 'config.guestId'
    - 'guest.ipAddress'
    - 'summary.runtime.powerState'
    filters:
    - guest.ipAddress is defined and (guest.ipAddress is match('192.168.*') or guest.ipAddress is match('192.169.*'))

# Using compose and groups
    plugin: community.vmware.vmware_vm_inventory
    strict: false
    hostname: 10.65.223.31
    username: administrator@vsphere.local
    password: Esxi@123$%
    validate_certs: false
    properties:
    - 'name'
    - 'config.name'
    - 'guest.ipAddress'
    compose:
      # This will populate the IP address of virtual machine if available
      # and will be used while communicating to the given virtual machine
      ansible_host: 'guest.ipAddress'
      composed_var: 'config.name'
      # This will populate a host variable with a string value
      ansible_user: "'admin'"
      ansible_connection: "'ssh'"
    groups:
      VMs: true
    hostnames:
    - config.name

# Use Datacenter, Cluster and Folder value to list VMs
    plugin: community.vmware.vmware_vm_inventory
    strict: false
    hostname: 10.65.200.241
    username: administrator@vsphere.local
    password: Esxi@123$%
    validate_certs: false
    with_tags: true
    resources:
      - datacenter:
        - Asia-Datacenter1
        - Asia-Datacenter2
        resources:
        - compute_resource:
          - Asia-Cluster1
          resources:
          - host_system:
            - Asia-ESXI4
        - folder:
          - dev
          - prod

# Use Category and it's relation with Tag
    plugin: community.vmware.vmware_vm_inventory
    strict: false
    hostname: 10.65.201.128
    username: administrator@vsphere.local
    password: Esxi@123$%
    validate_certs: false
    hostnames:
    - 'config.name'
    properties:
    - 'config.name'
    - 'config.guestId'
    - 'guest.ipAddress'
    - 'summary.runtime.powerState'
    with_tags: true
    keyed_groups:
    - key: tag_category.OS
      prefix: "vmware_tag_os_category_"
      separator: ""
    with_nested_properties: true
    filters:
    - "tag_category.OS is defined and 'Linux' in tag_category.OS"

# customizing hostnames based on VM's FQDN. The second hostnames template acts as a fallback mechanism.
    plugin: community.vmware.vmware_vm_inventory
    strict: false
    hostname: 10.65.223.31
    username: administrator@vsphere.local
    password: Esxi@123$%
    validate_certs: false
    hostnames:
     - 'config.name+"."+guest.ipStack.0.dnsConfig.domainName'
     - 'config.name'
    properties:
      - 'config.name'
      - 'config.guestId'
      - 'guest.hostName'
      - 'guest.ipAddress'
      - 'guest.guestFamily'
      - 'guest.ipStack'

# Select a specific IP address for use by ansible when multiple NICs are present on the VM
    plugin: community.vmware.vmware_vm_inventory
    strict: false
    hostname: 10.65.223.31
    username: administrator@vsphere.local
    password: Esxi@123$%
    validate_certs: false
    compose:
      # Set the IP address used by ansible to one that starts by 10.42. or 10.43.
      ansible_host: >-
        guest.net
        | selectattr('ipAddress')
        | map(attribute='ipAddress')
        | flatten
        | select('match', '^10.42.*|^10.43.*')
        | list
        | first
    properties:
      - guest.net

# Group hosts using Jinja2 conditionals
    plugin: community.vmware.vmware_vm_inventory
    strict: false
    hostname: 10.65.13.37
    username: administrator@vsphere.local
    password: Esxi@123$%
    validate_certs: false
    hostnames:
    - config.name
    properties:
    - 'name'
    - 'config.name'
    - 'config.datastoreUrl'
    groups:
      slow_storage: "'Nas01' in config.datastoreUrl[0].name"
      fast_storage: "'SSD' in config.datastoreUrl[0].name"
'''

from ansible.errors import AnsibleError, AnsibleParserError
from ansible.module_utils._text import to_text, to_native
from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible.module_utils.common.dict_transformations import _snake_to_camel
from ansible.utils.display import Display
from ansible.module_utils.six import text_type
from ansible_collections.community.vmware.plugins.plugin_utils.inventory import (
    to_nested_dict,
    to_flatten_dict,
)

display = Display()

try:
    # requests is required for exception handling of the ConnectionError
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    from pyVmomi import vim, vmodl
    HAS_PYVMOMI = True
except ImportError:
    HAS_PYVMOMI = False

try:
    from com.vmware.vapi.std_client import DynamicID
    from vmware.vapi.vsphere.client import create_vsphere_client
    HAS_VSPHERE = True
except ImportError:
    HAS_VSPHERE = False


from ansible.plugins.inventory import BaseInventoryPlugin, Constructable, Cacheable
from ansible.parsing.yaml.objects import AnsibleVaultEncryptedUnicode
from ansible_collections.community.vmware.plugins.module_utils.vmware import connect_to_api


class BaseVMwareInventory:
    def __init__(self, hostname, username, password, port, validate_certs, with_tags, http_proxy_host, http_proxy_port):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.port = port
        self.with_tags = with_tags
        self.validate_certs = validate_certs
        self.content = None
        self.rest_content = None
        self.proxy_host = http_proxy_host
        self.proxy_port = http_proxy_port

    def do_login(self):
        """
        Check requirements and do login
        """
        self.check_requirements()
        self.si, self.content = self._login()
        if self.with_tags:
            self.rest_content = self._login_vapi()

    def _login_vapi(self):
        """
        Login to vCenter API using REST call
        Returns: connection object

        """
        session = requests.Session()
        session.verify = self.validate_certs
        if not self.validate_certs:
            # Disable warning shown at stdout
            requests.packages.urllib3.disable_warnings()

        server = self.hostname
        if self.port:
            server += ":" + str(self.port)

        client, err = None, None
        try:
            client = create_vsphere_client(server=server,
                                           username=self.username,
                                           password=self.password,
                                           session=session)
        except Exception as error:
            err = error

        if client is None:
            msg = "Failed to login to %s using %s" % (server, self.username)
            if err:
                msg += " due to : %s" % to_native(err)
            raise AnsibleError(msg)
        return client

    def _login(self):
        """
        Login to vCenter or ESXi server
        Returns: connection object

        """
        return connect_to_api(module=None, disconnect_atexit=True, return_si=True,
                              hostname=self.hostname, username=self.username, password=self.password,
                              port=self.port, validate_certs=self.validate_certs, httpProxyHost=self.proxy_host,
                              httpProxyPort=self.proxy_port)

    def check_requirements(self):
        """ Check all requirements for this inventory are satisfied"""
        if not HAS_REQUESTS:
            raise AnsibleParserError('Please install "requests" Python module as this is required'
                                     ' for VMware Guest dynamic inventory plugin.')
        elif not HAS_PYVMOMI:
            raise AnsibleParserError('Please install "PyVmomi" Python module as this is required'
                                     ' for VMware Guest dynamic inventory plugin.')
        if HAS_REQUESTS:
            # Pyvmomi 5.5 and onwards requires requests 2.3
            # https://github.com/vmware/pyvmomi/blob/master/requirements.txt
            required_version = (2, 3)
            requests_version = requests.__version__.split(".")[:2]
            try:
                requests_major_minor = tuple(map(int, requests_version))
            except ValueError:
                raise AnsibleParserError("Failed to parse 'requests' library version.")

            if requests_major_minor < required_version:
                raise AnsibleParserError("'requests' library version should"
                                         " be >= %s, found: %s." % (".".join([str(w) for w in required_version]),
                                                                    requests.__version__))

        if not HAS_VSPHERE and self.with_tags:
            raise AnsibleError("Unable to find 'vSphere Automation SDK' Python library which is required."
                               " Please refer this URL for installation steps"
                               " - https://code.vmware.com/web/sdk/7.0/vsphere-automation-python")

        if not all([self.hostname, self.username, self.password]):
            raise AnsibleError("Missing one of the following : hostname, username, password. Please read "
                               "the documentation for more information.")

    def get_managed_objects_properties(self, vim_type, properties=None, resources=None, strict=False):  # noqa  # pylint: disable=too-complex
        """
        Look up a Managed Object Reference in vCenter / ESXi Environment
        :param vim_type: Type of vim object e.g, for datacenter - vim.Datacenter
        :param properties: List of properties related to vim object e.g. Name
        :param resources: List of resources to limit search scope
        :param strict: Dictates if plugin raises error or just warns
        :return: local content object
        """
        TraversalSpec = vmodl.query.PropertyCollector.TraversalSpec
        FilterSpec = vmodl.query.PropertyCollector.FilterSpec
        ObjectSpec = vmodl.query.PropertyCollector.ObjectSpec
        PropertySpec = vmodl.query.PropertyCollector.PropertySpec

        resource_filters = resources or []
        type_to_name_map = {}

        def _handle_error(message):
            if strict:
                raise AnsibleError(message)
            else:
                display.warning(message)

        def get_contents(container, vim_types):
            return self.content.propertyCollector.RetrieveContents([
                FilterSpec(
                    objectSet=[
                        ObjectSpec(
                            obj=self.content.viewManager.CreateContainerView(
                                container, vim_types, True),
                            skip=False,
                            selectSet=[TraversalSpec(
                                type=vim.view.ContainerView, path='view', skip=False)]
                        )],
                    propSet=[PropertySpec(type=t, all=False, pathSet=['name']) for t in vim_types],
                )
            ])

        def filter_containers(containers, typ, filter_list):
            if len(filter_list) > 0:
                objs = []
                results = []
                found_filters = {}

                for container in containers:
                    results.extend(get_contents(container, [typ]))

                for res in results:
                    if res.propSet[0].val in filter_list:
                        objs.append(res.obj)
                        found_filters[res.propSet[0].val] = True

                for fil in filter_list:
                    if fil not in found_filters:
                        _handle_error("Unable to find %s %s" % (type_to_name_map[typ], fil))

                return objs
            return containers

        def build_containers(containers, vim_type, names, filters):
            filters = filters or []
            if vim_type:
                containers = filter_containers(containers, vim_type, names)

            new_containers = []
            for fil in filters:
                new_filters = None
                for k, v in fil.items():
                    if k == "resources":
                        new_filters = v
                    else:
                        vim_type = getattr(vim, _snake_to_camel(k, True))
                        names = v
                        type_to_name_map[vim_type] = k.replace("_", " ")

                new_containers.extend(build_containers(containers, vim_type, names, new_filters))

            if len(filters) > 0:
                return new_containers
            return containers

        containers = build_containers([self.content.rootFolder], None, None, resource_filters)
        if len(containers) == 0:
            return []

        objs_list = [ObjectSpec(
            obj=self.content.viewManager.CreateContainerView(r, [vim_type], True),
            selectSet=[TraversalSpec(path='view', skip=False, type=vim.view.ContainerView)]) for r in containers]

        is_all = False if properties else True

        # Create Property Spec
        property_spec = PropertySpec(
            type=vim_type,  # Type of object to retrieved
            all=is_all,
            pathSet=properties
        )

        # Create Filter Spec
        filter_spec = FilterSpec(
            objectSet=objs_list,
            propSet=[property_spec],
            reportMissingObjectsInResults=False
        )

        try:
            return self.content.propertyCollector.RetrieveContents([filter_spec])
        except vmodl.query.InvalidProperty as err:
            _handle_error("Invalid property name: %s" % err.name)
        except Exception as err:  # pylint: disable=broad-except
            _handle_error("Couldn't retrieve contents from host: %s" % to_native(err))
        return []


class InventoryModule(BaseInventoryPlugin, Constructable, Cacheable):

    NAME = 'community.vmware.vmware_vm_inventory'

    def verify_file(self, path):
        """
        Verify plugin configuration file and mark this plugin active
        Args:
            path: Path of configuration YAML file
        Returns: True if everything is correct, else False
        """
        valid = False
        if super(InventoryModule, self).verify_file(path):
            if path.endswith(('vmware.yaml', 'vmware.yml', 'vmware_vm_inventory.yaml', 'vmware_vm_inventory.yml')):
                valid = True

        return valid

    def parse(self, inventory, loader, path, cache=True):
        """
        Parses the inventory file
        """
        super(InventoryModule, self).parse(inventory, loader, path, cache=cache)

        cache_key = self.get_cache_key(path)

        config_data = self._read_config_data(path)

        # set _options from config data
        self._consume_options(config_data)

        hostname = self.get_option('hostname')
        username = self.get_option('username')
        password = self.get_option('password')

        if isinstance(hostname, AnsibleVaultEncryptedUnicode):
            hostname = hostname.data

        if isinstance(username, AnsibleVaultEncryptedUnicode):
            username = username.data

        if isinstance(password, AnsibleVaultEncryptedUnicode):
            password = password.data

        self.pyv = BaseVMwareInventory(
            hostname=hostname,
            username=username,
            password=password,
            port=self.get_option('port'),
            with_tags=self.get_option('with_tags'),
            validate_certs=self.get_option('validate_certs'),
            http_proxy_host=self.get_option('proxy_host'),
            http_proxy_port=self.get_option('proxy_port')
        )
        self.pyv.do_login()

        if cache:
            cache = self.get_option('cache')

        update_cache = False
        if cache:
            try:
                cacheable_results = self._cache[cache_key]
            except KeyError:
                update_cache = True

        if cache and not update_cache:
            self._populate_from_cache(cacheable_results)
        else:
            cacheable_results = self._populate_from_source()

        if update_cache or (not cache and self.get_option('cache')):
            self._cache[cache_key] = cacheable_results

    def _populate_from_cache(self, cache_data):
        """
        Populate cache using source data

        """
        for host, host_properties in cache_data.items():
            self._populate_host_properties(host_properties, host)

    def _populate_from_source(self):
        """
        Populate inventory data from direct source

        """
        hostvars = {}
        strict = self.get_option('strict')

        vm_properties = self.get_option('properties')
        if not isinstance(vm_properties, list):
            vm_properties = [vm_properties]

        if len(vm_properties) == 0:
            vm_properties = ['name']

        if 'all' in vm_properties:
            query_props = None
            vm_properties.remove('all')
        else:
            if 'runtime.connectionState' not in vm_properties:
                vm_properties.append('runtime.connectionState')
            query_props = [x for x in vm_properties if x != "customValue"]

        objects = self.pyv.get_managed_objects_properties(
            vim_type=vim.VirtualMachine,
            properties=query_props,
            resources=self.get_option('resources'),
            strict=strict,
        )

        tags_info = dict()
        if self.pyv.with_tags:
            tag_svc = self.pyv.rest_content.tagging.Tag
            cat_svc = self.pyv.rest_content.tagging.Category

            tags = tag_svc.list()
            for tag in tags:
                tag_obj = tag_svc.get(tag)
                tags_info[tag_obj.id] = (tag_obj.name, cat_svc.get(tag_obj.category_id).name)

        hostnames = self.get_option('hostnames')

        for vm_obj in objects:
            properties = dict()
            for vm_obj_property in vm_obj.propSet:
                properties[vm_obj_property.name] = vm_obj_property.val

            if (properties.get('runtime.connectionState') or properties['runtime'].connectionState) in ('orphaned', 'inaccessible', 'disconnected'):
                continue

            # Custom values
            if 'customValue' in vm_properties:
                field_mgr = []
                if self.pyv.content.customFieldsManager:  # not an ESXi
                    field_mgr = self.pyv.content.customFieldsManager.field
                for cust_value in vm_obj.obj.customValue:
                    properties[[y.name for y in field_mgr if y.key == cust_value.key][0]] = cust_value.value

            # Tags
            if tags_info:
                # Add virtual machine to appropriate tag group
                vm_mo_id = vm_obj.obj._GetMoId()  # pylint: disable=protected-access
                vm_dynamic_id = DynamicID(type='VirtualMachine', id=vm_mo_id)
                tag_association = self.pyv.rest_content.tagging.TagAssociation
                properties['tags'] = []
                properties['categories'] = []
                properties['tag_category'] = {}
                for tag_id in tag_association.list_attached_tags(vm_dynamic_id):
                    if tag_id not in tags_info:
                        # Ghost Tags - community.vmware#681
                        continue
                    # Add tags related to VM
                    properties['tags'].append(tags_info[tag_id][0])
                    # Add categories related to VM
                    properties['categories'].append(tags_info[tag_id][1])
                    # Add tag and categories related to VM
                    if tags_info[tag_id][1] not in properties['tag_category']:
                        properties['tag_category'][tags_info[tag_id][1]] = []
                    properties['tag_category'][tags_info[tag_id][1]].append(tags_info[tag_id][0])

            # Path
            with_path = self.get_option('with_path')
            if with_path:
                path = []
                parent = vm_obj.obj.parent
                while parent:
                    path.append(parent.name)
                    parent = parent.parent
                path.reverse()
                properties['path'] = "/".join(path)

            host_properties = to_nested_dict(properties)

            # Check if we can add host as per filters
            host_filters = self.get_option('filters')
            if not self._can_add_host(host_filters, host_properties, strict=strict):
                continue

            host = self._get_hostname(host_properties, hostnames, strict=strict)

            if host not in hostvars:
                hostvars[host] = host_properties
                self._populate_host_properties(host_properties, host)

        return hostvars

    def _get_hostname(self, properties, hostnames, strict=False):
        hostname = None
        errors = []

        for preference in hostnames:
            try:
                hostname = self._compose(preference, properties)
            except Exception as e:  # pylint: disable=broad-except
                if strict:
                    raise AnsibleError("Could not compose %s as hostnames - %s" % (preference, to_native(e)))
                else:
                    errors.append(
                        (preference, str(e))
                    )
            if hostname:
                return to_text(hostname)

        raise AnsibleError(
            'Could not template any hostname for host, errors for each preference: %s' % (
                ', '.join(['%s: %s' % (pref, err) for pref, err in errors])
            )
        )

    def _can_add_host(self, host_filters, host_properties, strict=False):
        can_add_host = True
        for host_filter in host_filters:
            try:
                can_add_host = self._compose(host_filter, host_properties)
            except Exception as e:  # pylint: disable=broad-except
                if strict:
                    raise AnsibleError("Could not evaluate %s as host filters - %s" % (host_filter, to_native(e)))

            if not can_add_host:
                return False
        return True

    def _populate_host_properties(self, host_properties, host):
        # Load VM properties in host_vars
        self.inventory.add_host(host)

        # Use constructed if applicable
        strict = self.get_option('strict')

        # Composed variables
        compose = self.get_option('compose')
        if not compose:
            compose['ansible_host'] = 'guest.ipAddress'

        self._set_composite_vars(compose, host_properties, host, strict=strict)
        # Complex groups based on jinja2 conditionals, hosts that meet the conditional are added to group
        self._add_host_to_composed_groups(self.get_option('groups'), host_properties, host, strict=strict)
        # Create groups based on variable values and add the corresponding hosts to it
        self._add_host_to_keyed_groups(self.get_option('keyed_groups'), host_properties, host, strict=strict)

        with_path = self.get_option('with_path')
        if with_path:
            parents = host_properties['path'].split('/')
            if parents:
                if isinstance(with_path, text_type):
                    parents = [with_path] + parents

                c_name = self._sanitize_group_name('/'.join(parents))
                c_group = self.inventory.add_group(c_name)
                self.inventory.add_host(host, c_group)
                parents.pop()

                while len(parents) > 0:
                    p_name = self._sanitize_group_name('/'.join(parents))
                    p_group = self.inventory.add_group(p_name)

                    self.inventory.add_child(p_group, c_group)
                    c_group = p_group
                    parents.pop()

        can_sanitize = self.get_option('with_sanitized_property_name')

        # Sanitize host properties: to snake case
        if can_sanitize:  # to snake case
            host_properties = camel_dict_to_snake_dict(host_properties)

        with_nested_properties = self.get_option('with_nested_properties')
        if with_nested_properties:
            for k, v in host_properties.items():
                k = self._sanitize_group_name(k) if can_sanitize else k
                self.inventory.set_variable(host, k, v)

        # For backward compatability
        host_properties = to_flatten_dict(host_properties)
        for k, v in host_properties.items():
            k = self._sanitize_group_name(k) if can_sanitize else k
            self.inventory.set_variable(host, k, v)

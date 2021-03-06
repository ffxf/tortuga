# Copyright 2008-2018 Univa Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# pylint: disable=logging-not-lazy,no-self-use,no-member,maybe-no-member

import sys
import socket
import traceback
import os.path
import configparser
import subprocess
import csv
import logging
import gevent
from tortuga.exceptions.unsupportedOperation import UnsupportedOperation
from tortuga.config.configManager import ConfigManager
from tortuga.os_utility.osUtility import getOsObjectFactory
from tortuga.exceptions.nicNotFound import NicNotFound
from tortuga.addhost.addHostManager import AddHostManager
from tortuga.db.dbManager import DbManager
from tortuga.db.resourceAdapterCredentialsDbHandler \
    import ResourceAdapterCredentialsDbHandler
from tortuga.exceptions.resourceNotFound import ResourceNotFound
from tortuga.parameter.parameterApi import ParameterApi


class ResourceAdapter(object): \
        # pylint: disable=too-many-public-methods
    '''
    This is the base class for all resource adapters to derive from.
    The default actions simply print a debug message to show that the
    subclass did not implement the action.
    '''

    def __init__(self, addHostSession=None):
        if '__adaptername__' not in self.__class__.__dict__:
            raise NotImplementedError(
                'Subclasses of ResourceAdapter must have __adaptername__'
                ' defined')

        self._logger = logging.getLogger(
            'tortuga.resourceAdapter.%s' % (self.__adaptername__))
        self._logger.addHandler(logging.NullHandler())

        self.__installer_public_hostname = None
        self.__installer_public_ipaddress = None
        self.__private_dns_zone = None

        # Initialize caches
        self.__addHostApi = None
        self.__nodeApi = None
        self.__osObject = None
        self.__sanApi = None

        # Initialize abort flag (to "not" aborting)
        self.__isAborted = False

        self._cm = ConfigManager()

        self._addHostSession = addHostSession

    @property
    def addHostSession(self):
        return self._addHostSession

    @property
    def cacheCfgFilePath(self):
        return os.path.join(
            self._cm.getRoot(), 'var', '%s-instance.conf' % (
                self.__adaptername__))

    @property
    def cfgFileName(self):
        return os.path.join(
            self._cm.getKitConfigBase(),
            'adapter-defaults-%s.conf' % (
                self.__adaptername__))

    def hookAction(self, action, nodes, args=None):
        # Only the 'default' resource adapter overrides the hookAction()
        # method.
        pass

    def start(self, addNodesRequest, dbSession, dbHardwareProfile,
              dbSoftwareProfile=None): \
            # pylint: disable=unused-argument
        self.__trace(
            addNodesRequest, dbSession, dbHardwareProfile,
            dbSoftwareProfile)

    def validate_start_arguments(self, addNodesRequest, dbHardwareProfile,
                                 dbSoftwareProfile):
        self.__trace(
            addNodesRequest, dbHardwareProfile, dbSoftwareProfile)

    def stop(self, hardwareProfileName, deviceName):
        self.__trace(hardwareProfileName, deviceName)

    def updateNode(self, session, node, updateNodeRequest): \
            # pylint: disable=unused-argument
        self.__trace(session, node, updateNodeRequest)

    def suspendActiveNode(self, nodeId):
        '''Change the given active node to an idle node'''
        self.__trace(nodeId)

    def idleActiveNode(self, nodeIds):
        '''Change the given active node to an idle node'''
        self.__trace(nodeIds)

    def activateIdleNode(self, node, softwareProfileName,
                         softwareProfileChanged):
        '''Change the given idle node to an active node'''
        self.__trace(node, softwareProfileName, softwareProfileChanged)

    def deleteNode(self, nodeIds):
        '''Remove the given node (active or idle) from the system'''
        self.__trace(nodeIds)

    def _async_delete_nodes(self, nodes):
        """
        Asynchronously delete nodes; calls "ResourceAdapter._delete_node()"
        method for each deleted nodes

        :param dbNodes: list of Nodes objects
        :return: None
        """
        greenlets = []

        for node in nodes:
            greenlets.append(gevent.spawn(self._delete_node, node))

        # TODO: implement timeout
        gevent.joinall(greenlets)

    def _delete_node(self, node):
        """
        Abstract method called to delete node from
        "ResourceAdapter._async_delete_nodes()"

        :param node: Nodes object
        """

    def transferNode(self, nodeIdSoftwareProfileTuples,
                     newSoftwareProfileName):
        '''Transfer the given idle node'''
        self.__trace(nodeIdSoftwareProfileTuples, newSoftwareProfileName)

    def startupNode(self, nodeIds, remainingNodeList=None,
                    tmpBootMethod='n'): \
            # pylint: disable=unused-argument
        '''Start the given node'''
        # By default raise unsupported operation
        raise UnsupportedOperation('Node does not support starting')

    def shutdownNode(self, nodes, bSoftReset=False): \
            # pylint: disable=unused-argument
        '''Shutdown the given node'''
        # By default raise unsupported operation
        raise UnsupportedOperation('Node does not support shutdown')

    def rebootNode(self, nodes, bSoftReset=False): \
            # pylint: disable=unused-argument
        '''Reboot the given node'''
        # By default raise unsupported operation
        raise UnsupportedOperation('Node does not support rebooting')

    def checkpointNode(self, nodeId): \
            # pylint: disable=unused-argument
        '''Checkpoint the given node'''
        # By default raise unsupported operation
        raise UnsupportedOperation('Node does not support checkpointing')

    def revertNodeToCheckpoint(self, nodeId): \
            # pylint: disable=unused-argument
        '''Revert the given node to the checkpoint'''
        # By default raise unsupported operation
        raise UnsupportedOperation('Node does not support checkpointing')

    def migrateNode(self, nodeId, remainingNodeList, liveMigrate): \
            # pylint: disable=unused-argument
        '''Migrate the given node'''
        # By default raise unsupported operation
        raise UnsupportedOperation('Node does not support migrating')

    def addVolumeToNode(self, node, volume, isDirect): \
            # pylint: disable=unused-argument
        '''Add a disk to a node'''
        # By default raise unsupported operation
        raise UnsupportedOperation(
            'Node does not support dynamic disk addition')

    def removeVolumeFromNode(self, node, volume): \
            # pylint: disable=unused-argument
        '''Remove a disk from a node'''
        # By default raise unsupported operation
        raise UnsupportedOperation(
            'Node does not support dynamic disk deletion' % (node))

    def abort(self):
        '''abort node addition'''
        self._logger.debug('Setting abort flag')
        self.__isAborted = True

    def isAborted(self):
        '''Returns status of abort flag'''
        return self.__isAborted

    def __trace(self, *pargs, **kargs):
        stack = traceback.extract_stack()
        funcname = stack[-2][2]

        self._logger.debug(
            '-- (pass) %s::%s %s %s' % (
                self.__adaptername__, funcname, pargs, kargs))

    def getLogger(self):
        return self._logger

    def getResourceAdapterConfig(self, sectionName=None):
        """
        Raises:
            ResourceNotFound
        """

        self.getLogger().debug(
            'getResourceAdapterConfig(sectionName=[{0}])'.format(
                sectionName if sectionName else '(none)'))

        try:
            # Load default values
            defaultResourceAdapterConfigDict = self._loadConfigDict()

            if sectionName is None or sectionName == 'default':
                return defaultResourceAdapterConfigDict
        except ResourceNotFound:
            defaultResourceAdapterConfigDict = {}

        overrideConfigDict = self._loadConfigDict(sectionName)

        # Override defaults with hardware profile specific settings
        return dict(
            list(defaultResourceAdapterConfigDict.items()) +
            list(overrideConfigDict.items()))

    def _loadConfigDict(self, sectionName=None):
        """
        Raises:
            ResourceNotFound
        """

        if sectionName is None:
            sectionName = 'default'

        session = DbManager().openSession()

        try:
            self.getLogger().debug('_loadConfigDict()')

            result = ResourceAdapterCredentialsDbHandler().get(
                session, self.__adaptername__, sectionName)

            configDict = {}

            for entry in result['configuration']:
                configDict[entry['key']] = entry['value']
        finally:
            DbManager().closeSession()

        return configDict

    def getResourceAdapterConfigProfileByNodeName(self, name):
        """Get resource adapter configuration for existing node"""

        self.getLogger().debug(
            'getResourceAdapterConfigByNodeName(): name=[{0}]'.format(name))

        instance_cache = self.instanceCacheRefresh()

        return instance_cache.get(name, 'resource_adapter_configuration') \
            if instance_cache.has_section(name) and instance_cache.has_option(
                name, 'resource_adapter_configuration') else None

    def __getAddHostApi(self):
        '''Get and cache the Add Host API'''

        if self.__addHostApi is None:
            from tortuga.addhost.addHostServerLocal \
                import AddHostServerLocal

            self.__addHostApi = AddHostServerLocal()

        return self.__addHostApi

    def __getNodeApi(self):
        '''Get and cache the Node API'''

        if self.__nodeApi is None:
            from tortuga.node.nodeApi import NodeApi
            self.__nodeApi = NodeApi()
        return self.__nodeApi

    def __getOsObject(self):
        '''Get and cache the OS Object Factory'''

        if self.__osObject is None:
            from tortuga.os_utility import osUtility
            self.__osObject = osUtility.getOsObjectFactory()
        return self.__osObject

    def __getSanApi(self):
        '''Internal: Get and cache the SAN API'''

        if self.__sanApi is None:
            from tortuga.san import san
            self.__sanApi = san.San()
        return self.__sanApi

    # Properties for this object
    addHostApi = property(__getAddHostApi, None, None, None)
    nodeApi = property(__getNodeApi, None, None, None)
    osObject = property(__getOsObject, None, None, None)
    sanApi = property(__getSanApi, None, None, None)

    def statusMessage(self, msg):
        if self._addHostSession:
            AddHostManager().updateStatus(
                self._addHostSession, msg)
        else:
            # Just print out the message...this is a stop gap for resource
            # adapters running outside of the addHostManager framework
            sys.stdout.write(msg + '\n')
            sys.stdout.flush()

    def getOptions(self, dbSoftwareProfile, dbHardwareProfile): \
            # pylint: disable=unused-argument
        return {}

    def instanceCacheWrite(self, cfg):
        # Write the instance cache back to disk

        self.getLogger().debug('instanceCacheWrite()')

        with open(self.cacheCfgFilePath, 'w') as fp:
            cfg.write(fp)

    def instanceCacheRefresh(self):
        self.getLogger().debug('instanceCacheRefresh()')

        cfg = configparser.ConfigParser()

        cfg.read(self.cacheCfgFilePath)

        return cfg

    def instanceCacheSet(self, name, metadata=None):
        self.getLogger().debug(
            'instanceCacheSet(node=[%s], metadata=[%s])' % (name, metadata))

        cfg = self.instanceCacheRefresh()

        if not cfg.has_section(name):
            cfg.add_section(name)

        # Write metadata to node section
        if metadata:
            for key, value in metadata.items():
                cfg.set(name, key, value)

        self.instanceCacheWrite(cfg)

    def instanceCacheSetBulk(self, instance_ids, nodes=None):
        self.getLogger().debug(
            'instanceCacheSetBulk(instance_ids=[%s], nodes=[%s])' % (
                ' '.join(instance_ids),
                ' '.join([node.name for node in nodes or []])))

        cfg = self.instanceCacheRefresh()

        if not nodes:
            if not cfg.has_section('unassigned'):
                cfg.add_section('unassigned')

                instances = set()
            else:
                val = cfg.get('unassigned', 'instances')

                instances = set(val.split(' '))

            instances |= set(instance_ids)

            cfg.set('unassigned', 'instances', ' '.join(instances))

        self.instanceCacheWrite(cfg)

    def instanceCacheGet(self, nodeName):
        self.getLogger().debug(
            'instanceCacheGet(nodeName=[%s])' % (nodeName))

        cfg = self.instanceCacheRefresh()

        if not cfg.has_section(nodeName):
            raise ResourceNotFound(
                'No instance cache entry for [{0}]'.format(nodeName))

        # Read entire section into a dict
        result = {}

        for key, value in cfg.items(nodeName):
            result[key] = value

        return result

    def instanceCacheDelete(self, name):
        # Clear instance from configuration

        config = self.instanceCacheRefresh()

        if not config.has_section(name):
            self.getLogger().debug(
                'Cache clear: node [{0}] not found, no action'
                ' taken'.format(name))

            return

        self.getLogger().debug('Cache clear: node [{0}]'.format(name))

        config.remove_section(name)

        self.instanceCacheWrite(config)

    def instanceCacheUpdate(self, name, added=None, deleted=None):
        """
        'added' is a list of key-value tuples to be added
        'deleted' is a list of keys to be removed from the instance cache
        """

        self.getLogger().debug(
            'instanceCacheUpdate(): name=[{0}]'.format(name))

        config = self.instanceCacheRefresh()

        if not config.has_section(name):
            config.add_section(name)

        for key, value in added or []:
            config.set(name, key, value)

        for key in deleted or []:
            config.remove_option(name, key)

        self.instanceCacheWrite(config)

    def __findNicForProvisioningNetwork(self, nics, prov_network):
        """
        TODO: move this elsewhere

        Raises:
            NicNotFound
        """

        nics = [nic for nic in nics if nic.network == prov_network]

        if not nics:
            raise NicNotFound(
                'Unable to find NIC on provisioning network [%s]' % (
                    prov_network.address + '/' + prov_network.netmask))

        return nics[0]

    def writeLocalBootConfiguration(self, node, hardwareprofile,
                                    softwareprofile):
        """
        Raises:
            NicNotFound
        """

        if not hardwareprofile.nics:
            # Hardware profile has no provisioning NICs defined. This
            # shouldn't happen...

            self.getLogger().debug(
                'No provisioning nics defined in hardware profile %s' % (
                    hardwareprofile.name))

            return

        # Determine the provisioning nic for the hardware profile
        hwProfileProvisioningNic = hardwareprofile.nics[0]

        nic = None

        if hwProfileProvisioningNic.network:
            # Find the nic attached to the newly added node that is on
            # the same network as the provisioning nic.
            nic = self.__findNicForProvisioningNetwork(
                node.nics, hwProfileProvisioningNic.network)

        if not nic or not nic.mac:
            self.getLogger().warning(
                'MAC address not defined for nic (ip=[%s]) on node [%s]' % (
                    nic.ip, node.name))

            return

        # Set up DHCP/PXE for newly addded node
        bhm = getOsObjectFactory().getOsBootHostManager()

        # Write out the PXE file
        bhm.writePXEFile(
            node, hardwareprofile=hardwareprofile,
            softwareprofile=softwareprofile, localboot=False)

        # Add a DHCP lease
        bhm.addDhcpLease(node, nic)

    def removeLocalBootConfiguration(self, node):
        bhm = self.osObject.getOsBootHostManager()

        bhm.rmPXEFile(node)
        bhm.removeDhcpLease(node)

    def _pre_add_host(self, name, hwprofilename, swprofilename, ip): \
            # pylint: disable=unused-argument
        # Perform "pre-add-host" operation
        command = ('sudo %s/pre-add-host'
                   ' --hardware-profile %s'
                   ' --software-profile %s'
                   ' --host-name %s' % (
                       self._cm.getBinDir(),
                       hwprofilename,
                       swprofilename,
                       name))

        if ip:
            command += ' --ip %s' % (ip)

        self.getLogger().debug('calling command= [%s]' % (command))

        p = subprocess.Popen(
            command, shell=True, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, close_fds=True)

        p.communicate()

        p.wait()

    @property
    def installer_public_hostname(self):
        if self.__installer_public_hostname is None:

            cmd = '/opt/puppetlabs/bin/facter fqdn'

            with open(os.devnull, 'w') as devnull:
                p = subprocess.Popen(cmd,
                                     shell=True,
                                     stdout=subprocess.PIPE,
                                     stderr=devnull)

                stdout, _ = p.communicate()

                retval = p.wait()

            if retval == 0:
                self.__installer_public_hostname = stdout.decode().rstrip()

                self.getLogger().debug(
                    'using installerName [%s] from Facter' % (
                        self.__installer_public_hostname))
            else:
                self.__installer_public_hostname = self._cm.getHost()

                self.getLogger().debug(
                    'using installerName [%s] from system' % (
                        self.__installer_public_hostname))

        return self.__installer_public_hostname

    @property
    def installer_public_ipaddress(self):
        # Get installer IP
        if self.__installer_public_ipaddress is None:
            self.getLogger().debug('Looking up installer IP using DNS')

            aiInfo = socket.getaddrinfo(
                self.installer_public_hostname, None, socket.AF_INET,
                socket.SOCK_STREAM)

            self.__installer_public_ipaddress = aiInfo[0][4][0]

        return self.__installer_public_ipaddress

    @property
    def private_dns_zone(self):
        if self.__private_dns_zone is None:
            self.__private_dns_zone = \
                ParameterApi().getParameter('DNSZone').getValue()

        return self.__private_dns_zone

    def get_node_vcpus(self, name): \
            # pylint: disable=unused-argument
        return 1

    def get_instance_size_mapping(self, value):
        """
        Helper method for matching the first field (instance size) in
        the resource adapter specific CSV file

        :return: instance type/size to vcpus mapping
        :returntype int:
        """

        fn = os.path.join(
            self._cm.getKitConfigBase(),
            '{0}-instance-sizes.csv'.format(self.__adaptername__))

        if not os.path.exists(fn):
            return 1

        try:
            with open(fn) as fp:
                reader = csv.reader(fp)
                for row in reader:
                    if row[0] == value:
                        return int(row[1])

            return 1
        except Exception as exc:
            self.getLogger().error(
                'Error processing instance type mapping'
                ' [{0}] (exc=[{1}]). Using default value'.format(fn, exc))

            return 1

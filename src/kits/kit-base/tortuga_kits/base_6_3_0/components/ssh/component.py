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

from logging import getLogger
import os
import shutil

from tortuga.db.dbManager import DbManager
from tortuga.db.nics import Nics
from tortuga.kit.installer import ComponentInstallerBase
from tortuga.os_utility import tortugaSubprocess


logger = getLogger(__name__)


CONFIG_FILE = '/etc/ssh/ssh_config'


class ComponentInstaller(ComponentInstallerBase):
    name = 'ssh'
    version = '6.3.0'
    os_list = [
        {'family': 'rhel', 'version': '6', 'arch': 'x86_64'},
    ]

    def configure(self):
        fp = open(CONFIG_FILE, 'w')
        dbm = DbManager()
        session = dbm.openSession()

        try:
            print("# ", file=fp)
            print("# Dynamically generated by: genconfig (Do not edit!)",
                  file=fp)
            print("#", file=fp)
            print("", file=fp)

            dnszone = self.kit_installer.get_db_parameter_value('DNSZone')

            for db_nic in session.query(Nics).order_by(Nics.ip).all():
                if db_nic.node.state == 'Deleted':
                    continue

                if not db_nic.ip:
                    continue

                name = db_nic.node.name.split('.')[0]

                print('Host {}'.format(db_nic.ip), file=fp)
                print('\tStrictHostKeyChecking no', file=fp)

                print('Host {}.{}'.format(name, dnszone), file=fp)
                print('\tStrictHostKeyChecking no', file=fp)

                print('Host {}'.format(name), file=fp)
                print('\tStrictHostKeyChecking no', file=fp)

                print("", file=fp)

            print('Host *', file=fp)
            print('\t# ssh_config defaults', file=fp)
            print('\tGSSAPIAuthentication yes', file=fp)
            print('\tForwardX11Trusted yes', file=fp)
            print('\t# tortuga defaults', file=fp)
            print('\tNoHostAuthenticationForLocalhost yes', file=fp)
            print('\tStrictHostKeyChecking no', file=fp)

        finally:
            fp.close()
            dbm.closeSession()

    def action_add_host(self, hardware_profile_name, software_profile_name,
                        nodes, *args, **kwargs):
        self.configure()

    def action_configure(self, software_profile_name, *args, **kwargs):
        self.configure()

    def action_delete_host(self, hardware_profile_name, software_profile_name,
                           nodes, *args, **kwargs):
        for node in nodes:
            short_host_name = node.getName().split('.')[0]

            #
            # Remove ssh keymapping for node
            #
            logger.debug('Removing ssh public key for node {}'.format(node))

            #
            # Remove fullname
            #
            tortugaSubprocess.executeCommand(
                'ssh-keygen -R {} >/dev/null 2>&1 ||:'.format(node))

            # Remove short name
            tortugaSubprocess.executeCommand(
                'ssh-keygen -R {} >/dev/null 2>&1 ||:'.format(
                    short_host_name)
            )

            #
            # Remove nic entries
            #
            for nic in node.getNics():
                tortugaSubprocess.executeCommand(
                    'ssh-keygen -R {} >/dev/null 2>&1 ||:'.format(nic.getIp()))

        self.configure()

    def action_post_install(self, *args, **kwargs):
        self.configure()

        sshdir = '/root/.ssh'
        privkey = os.path.join(sshdir, 'id_rsa')
        pubkey = os.path.join(sshdir, 'id_rsa.pub')
        authkeys = os.path.join(sshdir, 'authorized_keys')

        if not os.path.exists(sshdir):
            os.makedirs(sshdir, 0o700)

        #
        # Create public key if key not found
        #
        if not os.path.exists(pubkey):
            #
            # RSA key, 2048 bits in size, /root/.ssh/id_rsa, no passphrase
            #
            tortugaSubprocess.executeCommand(
                'ssh-keygen -t rsa -b 2048 -f {} -N ""'.format(privkey))

        #
        # copy public key to authorized_keys
        #
        if not os.path.exists(authkeys):
            shutil.copy(pubkey, authkeys)

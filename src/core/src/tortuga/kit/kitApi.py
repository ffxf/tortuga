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

# pylint: disable=no-member

from .eula import CommandLineEulaValidator
from tortuga.kit.manager import KitManager
from tortuga.kit.kitApiInterface import KitApiInterface
from tortuga.utility.tortugaApi import TortugaApi
from tortuga.exceptions.tortugaException import TortugaException
from typing import List


class KitApi(TortugaApi, KitApiInterface):
    """
    Kit API class.
    """
    def __init__(self):
        super().__init__()
        self._kit_manager = KitManager(
            eula_validator=CommandLineEulaValidator()
        )

    def getKit(self, name, version, iteration=None):
        """
        Get kit info.

            Returns:
                kit
            Throws:
                KitNotFound
                TortugaException
        """
        try:
            kit = self._kit_manager.getKit(name, version, iteration)
            return kit
        except TortugaException as ex:
            raise
        except Exception as ex:
            self.getLogger().exception('%s' % ex)
            raise TortugaException(exception=ex)

    def getKitById(self, id_):
        """
        Get kit info by kitId.

            Returns:
                kit
            Throws:
                KitNotFound
                TortugaException
        """
        try:
            return self._kit_manager.getKitById(id_)
        except TortugaException as ex:
            raise
        except Exception as ex:
            self.getLogger().exception('%s' % ex)

    def getKitList(self):
        """
        Get kit list.

            Returns:
                [kits]
            Throws:
                TortugaException
        """
        try:
            kitList = self._kit_manager.getKitList()
            return kitList
        except TortugaException as ex:
            raise
        except Exception as ex:
            self.getLogger().exception('%s' % ex)
            raise TortugaException(exception=ex)

    def installKit(self, name, version, iteration=None, key=None):
        """
        Install kit using kit name/version/iteration.

            Returns:
                kitId
            Throws:
                UserNotAuthorized
                FileNotFound
                KitAlreadyExists
                TortugaException
        """
        try:
            kit = self._kit_manager.installKit(
                name, version, iteration, key)

            return kit
        except TortugaException as ex:
            raise
        except Exception as ex:
            self.getLogger().exception('%s' % ex)
            raise TortugaException(exception=ex)

    def installKitPackage(self, packageUrl, key=None):
        """
            Install kit package.

            Returns:
                kitId
            Throws:
                UserNotAuthorized
                FileNotFound
                KitAlreadyExists
                TortugaException
        """
        try:
            kit = self._kit_manager.installKitPackage(
                packageUrl, key)

            return kit
        except TortugaException as ex:
            raise
        except Exception as ex:
            self.getLogger().exception('%s' % ex)
            raise TortugaException(exception=ex)

    def getKitEula(self, name, version, iteration=None):
        """
            Fetch eula information for kit.

            Returns:
                eula tortuga object
            Throws:
                UserNotAuthorized
                FileNotFound
                NoKitEula
                TortugaException
        """
        try:
            return self._kit_manager.get_kit_eula(
                name, version, iteration)
        except TortugaException as ex:
            raise
        except Exception as ex:
            self.getLogger().exception('%s' % ex)
            raise TortugaException(exception=ex)

    def getKitPackageEula(self, packageUrl):
        """
            Fetch eula information for kit package.

            Returns:
                eula tortuga object
            Throws:
                UserNotAuthorized
                FileNotFound
                NoKitEula
                TortugaException
        """
        try:
            eula = self._kit_manager.get_kit_package_eula(packageUrl)
            return eula
        except TortugaException as ex:
            raise
        except Exception as ex:
            self.getLogger().exception('%s' % ex)
            raise TortugaException(exception=ex)

    def installOsKit(self, os_media_urls: List[str], **kwargs) -> None:
        """
            Install OS kit

            Returns:
                kitId
            Throws:
                UserNotAuthorized
                FileNotFound
                KitAlreadyExists
                TortugaException
        """
        try:
            return self._kit_manager.installOsKit(os_media_urls, **kwargs)
        except TortugaException:
            raise
        except Exception as ex:
            self.getLogger().exception(ex)
            raise TortugaException(exception=ex)

    def deleteKit(self, name, version=None, iteration=None, force=False) -> None:
        """
        Delete kit.

            Returns:
                None
            Throws:
                UserNotAuthorized
                KitNotFound
                KitInUse
                TortugaException
        """
        try:
            self._kit_manager.deleteKit(
                name, version, iteration, force=force)
        except TortugaException:
            raise
        except Exception as ex:
            self.getLogger().exception('%s' % ex)
            raise TortugaException(exception=ex)

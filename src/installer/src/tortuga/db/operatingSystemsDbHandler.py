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

# pylint: disable=not-callable,multiple-statements,no-self-use,no-name-in-module
# pylint: disable=no-member,maybe-no-member

from sqlalchemy import and_
from sqlalchemy.orm.exc import NoResultFound

from tortuga.db.tortugaDbObjectHandler import TortugaDbObjectHandler
from tortuga.db.operatingSystems import OperatingSystems
from tortuga.db.operatingSystemsFamilies import OperatingSystemsFamilies
from tortuga.exceptions.osNotFound import OsNotFound
from tortuga.exceptions.osAlreadyExists import OsAlreadyExists
from tortuga.helper import osHelper
from tortuga.objects.osFamilyInfo import OsFamilyInfo


class OperatingSystemsDbHandler(TortugaDbObjectHandler):
    """
    This class handles OS table.
    """

    def getOsInfo(self, session, name, vers=None, arch=None):
        """
        Return osInfo for specified name/version/arch
        """

        if name and vers and arch:
            osFilter = and_(OperatingSystems.name == name,
                            OperatingSystems.version == vers,
                            OperatingSystems.arch == arch)
        elif name and vers:
            osFilter = and_(OperatingSystems.name == name,
                            OperatingSystems.version == vers)
        else:
            osFilter = and_(OperatingSystems.name == name)

        try:
            return session.query(OperatingSystems).filter(osFilter).one()
        except NoResultFound:
            raise OsNotFound(
                'Operating system [%s-%s-%s] not found.' % (
                    name, vers, arch))

    def getOsId(self, session, name, version, arch):
        """
        Return id for the specified operating system.
        """
        return self.getOsInfo(session, name, version, arch).id

    def addOs(self, session, osInfo):
        """
        Insert operating system into the db.
        """

        try:
            self.getOsId(
                session, osInfo.getName(), osInfo.getVersion(),
                osInfo.getArch())

            raise OsAlreadyExists('OS %s already exists' % (osInfo))
        except OsNotFound:
            # OK.
            pass

        dbOs = OperatingSystems(
            name=osInfo.getName(), version=osInfo.getVersion(),
            arch=osInfo.getArch())

        session.add(dbOs)

        return dbOs

    def _getOsFamily(self, session, osFamilyInfo):
        if osFamilyInfo.getName() and osFamilyInfo.getVersion() and \
                osFamilyInfo.getArch():
            osFamilyFilter = and_(
                OperatingSystemsFamilies.name == osFamilyInfo.getName(),
                OperatingSystemsFamilies.version == osFamilyInfo.
                getVersion(),
                OperatingSystemsFamilies.arch == osFamilyInfo.getArch()
            )
        elif osFamilyInfo.getName() and osFamilyInfo.getVersion():
            osFamilyFilter = and_(
                OperatingSystemsFamilies.name == osFamilyInfo.getName(),
                OperatingSystemsFamilies.version ==
                osFamilyInfo.getVersion(),
                OperatingSystemsFamilies.arch == None  # noqa
            )
        else:
            osFamilyFilter = and_(
                OperatingSystemsFamilies.name == osFamilyInfo.getName(),
                OperatingSystemsFamilies.version == None,  # noqa
                OperatingSystemsFamilies.arch == None  # noqa
            )

        try:
            return session.query(OperatingSystemsFamilies).filter(
                osFamilyFilter).one()
        except NoResultFound:
            pass

        return None

    def __addOsFamilyRoot(self, session):
        dbOsFamily = OperatingSystemsFamilies(name='root')
        session.add(dbOsFamily)
        return dbOsFamily

    def addOsFamilyIfNotFound(self, session, osFamilyInfo):
        familyName = osFamilyInfo.getName()
        familyVers = osFamilyInfo.getVersion()
        familyArch = osFamilyInfo.getArch()

        dbOsFamily = self._getOsFamily(session, osFamilyInfo)

        if dbOsFamily:
            return dbOsFamily

        # The 'root' entry is an exception since it doesn't have a
        # parent.  Just add it...
        if familyName == 'root':
            dbOsFamily = self.__addOsFamilyRoot(session)
        else:
            # ... otherwise, check for the parent of the specified
            # and it's parent should be 'root'
            osFamilyInfoParent = OsFamilyInfo(familyName, familyVers)

            dbOsFamilyParent = self._getOsFamily(
                session, osFamilyInfoParent)

            if not dbOsFamilyParent:
                # Check for the root entry
                osFamilyInfoRoot = OsFamilyInfo('root')

                dbOsFamilyRoot = self._getOsFamily(
                    session, osFamilyInfoRoot)

                if not dbOsFamilyRoot:
                    dbOsFamilyRoot = self.__addOsFamilyRoot(session)

                dbOsFamilyParent = OperatingSystemsFamilies(
                    name=familyName, version=familyVers)

                session.add(dbOsFamilyParent)

                dbOsFamilyRoot.children.append(dbOsFamilyParent)

            dbOsFamily = OperatingSystemsFamilies(
                name=familyName,
                version=familyVers,
                arch=familyArch)

            session.add(dbOsFamily)

            dbOsFamilyParent.children.append(dbOsFamily)

        return dbOsFamily

    def addOsIfNotFound(self, session, osInfo):
        """
        Insert operating system into the db if it is not found.
        """
        try:
            return self.getOsInfo(
                session, osInfo.getName(), osInfo.getVersion(),
                osInfo.getArch())
        except OsNotFound:
            pass

        # Translate osInfo
        tmpOsInfo = osHelper.getOsInfo(osInfo.getName(),
                                       osInfo.getVersion(),
                                       osInfo.getArch())

        # Check for existence of OS family
        dbOsFamily = self.addOsFamilyIfNotFound(
            session, tmpOsInfo.getOsFamilyInfo())

        dbOs = OperatingSystems(name=osInfo.getName(),
                                version=osInfo.getVersion(),
                                arch=osInfo.getArch())

        dbOs.family = dbOsFamily

        session.add(dbOs)

        return dbOs

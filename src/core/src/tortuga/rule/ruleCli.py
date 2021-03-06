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

from tortuga.cli.tortugaCli import TortugaCli
from tortuga.exceptions.invalidCliRequest import InvalidCliRequest


class RuleCli(TortugaCli):
    """
    Base rule command line interface class.
    """

    def getApplicationNameAndRuleName(self):
        applicationName = self._options.applicationName
        ruleName = self._options.ruleName

        if not applicationName:
            raise InvalidCliRequest(_('Missing application name.'))

        if not ruleName:
            raise InvalidCliRequest(_('Missing rule name.'))

        return applicationName, ruleName

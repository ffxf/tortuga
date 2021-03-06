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

import json

from tortuga.exceptions.tortugaException import TortugaException
from .tortugaWsApi import TortugaWsApi


class SyncWsApi(TortugaWsApi):
    """Cluster sync WS API class"""

    def scheduleClusterUpdate(self, updateReason=None):
        """Schedule cluster update.

            Returns:
                None
            Throws:
                UserNotAuthorized
                TortugaException
        """

        url = 'v1/updates/cluster'

        postdata = {}

        if updateReason:
            postdata['reason'] = updateReason

        try:
            self.sendSessionRequest(
                url, method='POST', data=json.dumps(postdata))
        except TortugaException:
            raise
        except Exception as ex:
            raise TortugaException(exception=ex)

    def getUpdateStatus(self):
        """Return cluster update status

            Returns:
                Boolean - True if cluster update is currently running
            Throws:
                TortugaException
        """

        url = 'v1/updates/cluster'

        try:
            _, responseDict = self.sendSessionRequest(url)

            return responseDict.get('running') == 'True'
        except TortugaException:
            raise
        except Exception as ex:
            raise TortugaException(exception=ex)

# (C) Copyright 2005-2006 Nuxeo SAS <http://nuxeo.com>
# Authors:
# M.-A. Darche <madarche@nuxeo.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as published
# by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA
# 02111-1307, USA.
#
# $Id$

from zLOG import LOG, INFO

from Products.GenericSetup import profile_registry
from Products.GenericSetup import EXTENSION

from Products.CPSCore.interfaces import ICPSSite

import RemoteControllerTool
import RemoteControllerClient

def initialize(registrar):
    from Products.CMFCore import utils
    utils.ToolInit(
        # XXX: Use 'CPS Tools' when and if possible
        'CPS  Remote Controller Tool',
        tools=(RemoteControllerTool.RemoteControllerTool,
               RemoteControllerClient.CPSRemoteControllerClient),
        icon='tool.png',
        ).initialize(registrar)


    try:
        utils.ToolInit(
            # XXX: Use 'CPS Tools' when and if possible
            'CPS  Remote Controller Client Tool',
            tools=(RemoteControllerTool.RemoteControllerTool,
                   RemoteControllerClient.CPSRemoteControllerClient),
            icon='tool.png',
            ).initialize(registrar)
    except 'TypeError':
        # BBB for CMF 1.4, remove this in CPS 3.4.0
        utils.ToolInit(
            # XXX: Use 'CPS Tools' when and if possible
            'CPS  Remote Controller Client Tool',
            tools=(RemoteControllerTool.RemoteControllerTool,
                   RemoteControllerClient.CPSRemoteControllerClient),
            product_name='CPSRemoteController', # BBB
            icon='tool.png',
            ).initialize(registrar)

    # Registering the default profile
    profile_registry.registerProfile(
        'default',
        'CPS RemoteController',
        "Remote control product for CPS.",
        'profiles/default',
        'CPSRemoteController',
        EXTENSION,
        for_=ICPSSite)



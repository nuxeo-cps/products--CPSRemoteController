# (C) Copyright 2005 Nuxeo SARL <http://nuxeo.com>
# Author:
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

import Products.CMFCore
import RemoteControllerTool
import RemoteControllerClient

def initialize(registrar):
    Products.CMFCore.utils.ToolInit(
        # XXX: Use 'CPS Tools' when and if possible
        'CPS  Remote Controller Tool',
        tools=(RemoteControllerTool.RemoteControllerTool,
               RemoteControllerClient.CPSRemoteControllerClient),
        icon='tool.png',
        ).initialize(registrar)


    Products.CMFCore.utils.ToolInit(
        # XXX: Use 'CPS Tools' when and if possible
        'CPS  Remote Controller Client Tool',
        tools=(RemoteControllerTool.RemoteControllerTool,
               RemoteControllerClient.CPSRemoteControllerClient),
        product_name='CPSRemoteController',
        icon='tool.png',
        ).initialize(registrar)


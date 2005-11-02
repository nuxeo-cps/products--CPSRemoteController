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

from zLOG import LOG, INFO, DEBUG

# XXX I think that as long as you don't run any CPSSpecific methods,
# this should still work under pure CMF. This needs to be tested though.
from Products.CPSInstaller.CPSInstaller import CPSInstaller

class Installer(CPSInstaller):
    pass

def install(self):

    installer = Installer(self, 'CPSRemoteController')


    installer.log("Starting CPSRemoteController install")

    installer.verifyTool('portal_remote_controller', 'CPSRemoteController',
                         'CPS Remote Controller Tool')
    installer.verifyTool('portal_remote_controller_client',
                         'CPSRemoteController',
                         'CPS Remote Controller Client Tool')

    installer.finalize()
    installer.log("End of specific CPSRemoteController install")
    return installer.logResult()

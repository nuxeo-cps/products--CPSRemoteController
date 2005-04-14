# (C) Copyright 2005 Nuxeo SARL <http://nuxeo.com>
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

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

import unittest
from Testing import ZopeTestCase
from Products.CPSDefault.tests import CPSDefaultTestCase
import CPSRemoteControllerTestCase

class ProductTestCase(CPSRemoteControllerTestCate.CPSRemoteControllerTestCase,
                      CPSDefaultTestCase.CPSDefaultTestCase):

    def afterSetUp(self):
        self.login_id = 'manager'
        self.login(self.login_id)
        self.portal.REQUEST.SESSION = {}
        self.portal.REQUEST['AUTHENTICATED_USER'] = self.login_id

        from Products.ExternalMethod.ExternalMethod import ExternalMethod
        installer = ExternalMethod('installRemoteController', '',
                                   'CPSRemoteController.install', 'install')
        self.portal._setObject('installRemoteController', installer)
        self.assert_('installRemoteController' in self.portal.objectIds())
        self.portal.installRemoteController()
        self.remote_controller_tool = self.portal.portal_remote_controller


    def beforeTearDown(self):
        self.logout()


    def test_listContent(self):
        pass


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ProductTestCase))
    return suite

if __name__ == '__main__':
    framework(descriptions=1, verbosity=2)


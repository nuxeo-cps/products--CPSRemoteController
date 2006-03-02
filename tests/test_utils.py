#!/usr/bin/python
# -*- encoding: iso-8859-15 -*-
# Copyright (c) 2005 Nuxeo SARL <http://nuxeo.com>
# Author : Tarek Ziadé <tz@nuxeo.com>
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
"""Make sure marshaling works over documents.
"""

import doctest
import os, sys
import os.path
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

import unittest
from Testing import ZopeTestCase
import CPSRemoteControllerTestCase
from Products.CPSDefault.tests.CPSTestCase import MANAGER_ID

from Products.CPSRemoteController.utils import marshallDocument, unMarshallDocument
from xmlrpclib import dumps

class UtilsTestCase(CPSRemoteControllerTestCase.CPSRemoteControllerTestCase):

    def afterSetUp(self):
        self.login_id = MANAGER_ID
        self.login(self.login_id)
        self.portal.REQUEST.SESSION = {}
        self.portal.REQUEST['AUTHENTICATED_USER'] = self.login_id

        self.tool = self.portal.portal_remote_controller

    def beforeTearDown(self):
        self.logout()

    def _test_marshalling(self, content):
        marshalled = marshallDocument(content)
        dumps((marshalled,))
        return unMarshallDocument(marshalled)

    def test_simple_marshalling(self):
        from DateTime import DateTime
        from xmlrpclib import DateTime as rpcDateTime
        content = ('Document', {'date': DateTime('01/01/1971')}, 'workspaces')
        unmarshalled = self._test_marshalling(content)
        self.assertEquals(unmarshalled[0], 'Document')
        self.assert_(isinstance(unmarshalled[1]['date'], DateTime))

    def test_preview(self):
        content = ('Flash Animation', {'file_text': '\n\n\n'}, 'workspaces')
        unmarshalled = self._test_marshalling(content)
        self.assertEquals(unmarshalled[0], 'Flash Animation')
        self.assertEquals(unmarshalled[1]['file_text'], '')

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(UtilsTestCase))
    suite.addTest(doctest.DocTestSuite('Products.CPSRemoteController.utils'))
    return suite

if __name__ == '__main__':
    framework(descriptions=1, verbosity=2)

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
import os.path
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

import unittest
from Testing import ZopeTestCase
import CPSRemoteControllerTestCase
from Products.CPSDefault.tests.CPSTestCase import MANAGER_ID
from xmlrpclib import Binary

class ProductTestCase(CPSRemoteControllerTestCase.CPSRemoteControllerTestCase):

    def afterSetUp(self):
        self.login_id = MANAGER_ID
        self.login(self.login_id)
        self.portal.REQUEST.SESSION = {}
        self.portal.REQUEST['AUTHENTICATED_USER'] = self.login_id

        from Products.ExternalMethod.ExternalMethod import ExternalMethod
        installer = ExternalMethod('installRemoteController', '',
                                   'CPSRemoteController.install', 'install')
        self.portal._setObject('installRemoteController', installer)
        self.assert_('installRemoteController' in self.portal.objectIds())
        self.portal.installRemoteController()
        self.tool = self.portal.portal_remote_controller


    def beforeTearDown(self):
        self.logout()


    def test_listContent(self):
        folder_rpath = 'workspaces'
        self.assert_(self.tool.listContent(folder_rpath))


    def test_createAndDeleteDocument(self):
        folder_rpath = 'workspaces'
        proxy_list1 = self.tool.listContent(folder_rpath)
        data_dict = {'Title': "The report from Monday meeting",
                     'Description': "Another boring report",
                     }
        doc_rpath = self.tool.createDocument('File', data_dict, folder_rpath, 0)
        proxy_list2 = self.tool.listContent(folder_rpath)
        self.assertEquals(len(proxy_list1) + 1, len(proxy_list2))
        self.assert_(doc_rpath in proxy_list2)

        self.tool.deleteDocument(doc_rpath)
        proxy_list3 = self.tool.listContent(folder_rpath)
        self.assertEquals(len(proxy_list1), len(proxy_list3))
        self.failIf(doc_rpath in proxy_list3)


    def test_lockDocument(self):
        folder_rpath = 'workspaces'
        proxy_list1 = self.tool.listContent(folder_rpath)
        data_dict = {'Title': "The report from Monday meeting",
                     'Description': "Another boring report",
                     }
        doc_id = self.tool.createDocument('File', data_dict, folder_rpath, 0)
        doc_rpath = folder_rpath + '/' + doc_id
        self.failIf(self.tool.isDocumentLocked(doc_rpath))
        lock_tocken = self.tool.lockDocument(doc_rpath)
        self.assert_(self.tool.isDocumentLocked(doc_rpath))
        self.tool.unlockDocument(doc_rpath, lock_tocken)
        self.failIf(self.tool.isDocumentLocked(doc_rpath))


    def test_editOrcreateDocument(self):
        folder_rpath = 'workspaces'
        proxy_list1 = self.tool.listContent(folder_rpath)
        data_dict = {'Title': "The report from Monday meeting",
                     'Description': "Another boring report",
                     }
        doc1_id = self.tool.createDocument('File', data_dict, folder_rpath, 0)
        doc1_rpath = folder_rpath + '/' + doc1_id
        proxy_list2 = self.tool.listContent(folder_rpath)
        self.assertEquals(len(proxy_list1) + 1, len(proxy_list2))

        doc2_id = self.tool.editOrCreateDocument(doc1_rpath, 'File', data_dict, 0)
        proxy_list3 = self.tool.listContent(folder_rpath)
        self.assertEquals(len(proxy_list2), len(proxy_list3))

        doc3_rpath = os.path.join(folder_rpath,
                                  'dummy-id-that-we-cannot-guess-before-doc-is-created')
        doc3_returned_rpath = self.tool.editOrCreateDocument(doc3_rpath, 'File', data_dict, 0)
        proxy_list4 = self.tool.listContent(folder_rpath)
        self.assertEquals(len(proxy_list3) + 1, len(proxy_list4))


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ProductTestCase))
    return suite

if __name__ == '__main__':
    framework(descriptions=1, verbosity=2)


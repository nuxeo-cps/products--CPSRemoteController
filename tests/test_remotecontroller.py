# -*- coding: ISO-8859-15 -*-
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
import types

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


    def testGetRoles(self):
        roles = self.tool.getRoles(MANAGER_ID)
        self.assertEquals(type(roles), types.ListType)


    def testGetLocalRoles(self):
        for folder_rpath in ('workspaces', 'sections'):
            roles = self.tool.getLocalRoles(MANAGER_ID, folder_rpath)
            self.assertEquals(type(roles), types.ListType)


    def testListContent(self):
        for folder_rpath in ('workspaces', 'sections'):
            self.assert_(self.tool.listContent(folder_rpath))


    def testCreateAndDeleteDocument(self):
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


    def testDocumentFields(self):
        folder_rpath = 'workspaces'
        proxy_list1 = self.tool.listContent(folder_rpath)

        title = "The report from Monday meeting"
        description = "Another boring report"
        language = 'en'
        data_dict = {'Title': title,
                     'Description': description,
                     'Language': language,
                     }
        doc_rpath = self.tool.createDocument('File', data_dict, folder_rpath, 0)
        doc_proxy = self.portal.restrictedTraverse(doc_rpath)
        doc = doc_proxy.getContent()
        self.assertEquals(doc.Title(), title)
        self.assertEquals(doc.Description(), description)
        self.assertEquals(doc.Language(), language)

        proxy_list2 = self.tool.listContent(folder_rpath)
        self.assertEquals(len(proxy_list1) + 1, len(proxy_list2))
        self.assert_(doc_rpath in proxy_list2)

        title = "Le rapport de la réunion de lundi matin"
        description = "Encore un rapport ennuyeux"
        language = 'fr'
        data_dict = {'Title': title,
                     'Description': description,
                     'Language': language,
                     }
        doc_rpath = self.tool.createDocument('File', data_dict, folder_rpath, 0)
        doc_proxy = self.portal.restrictedTraverse(doc_rpath)
        doc = doc_proxy.getContent()
        self.assertEquals(doc.Title(), title)
        self.assertEquals(doc.Description(), description)
        self.assertEquals(doc.Language(), language)

        proxy_list3 = self.tool.listContent(folder_rpath)
        self.assertEquals(len(proxy_list2) + 1, len(proxy_list3))
        self.assert_(doc_rpath in proxy_list3)


    def testLockDocument(self):
        folder_rpath = 'workspaces'
        proxy_list1 = self.tool.listContent(folder_rpath)
        data_dict = {'Title': "The report from Monday meeting",
                     'Description': "Another boring report",
                     }
        doc_rpath = self.tool.createDocument('File', data_dict, folder_rpath, 0)
        self.failIf(self.tool.isDocumentLocked(doc_rpath))
        lock_tocken = self.tool.lockDocument(doc_rpath)
        self.assert_(self.tool.isDocumentLocked(doc_rpath))
        self.tool.unlockDocument(doc_rpath, lock_tocken)
        self.failIf(self.tool.isDocumentLocked(doc_rpath))

        # Simulating that we have lost the lock_tokens for a document, for
        # example because the application crashed.
        lost_lock_tocken = self.tool.lockDocument(doc_rpath)
        self.tool.deleteDocumentLocks(doc_rpath)
        self.failIf(self.tool.isDocumentLocked(doc_rpath))


    def testEditOrcreateDocument(self):
        folder_rpath = 'workspaces'
        proxy_list1 = self.tool.listContent(folder_rpath)
        data_dict = {'Title': "The report from Monday meeting",
                     'Description': "Another boring report",
                     }
        doc1_rpath = self.tool.createDocument('File', data_dict, folder_rpath, 0)
        proxy_list2 = self.tool.listContent(folder_rpath)
        self.assertEquals(len(proxy_list1) + 1, len(proxy_list2))

        doc2_rpath = self.tool.editOrCreateDocument(doc1_rpath, 'File', data_dict, 0)
        proxy_list3 = self.tool.listContent(folder_rpath)
        self.assertEquals(len(proxy_list2), len(proxy_list3))

        doc3_rpath = os.path.join(folder_rpath,
                                  'dummy-id-that-we-cannot-guess-before-doc-is-created')
        doc3_returned_rpath = self.tool.editOrCreateDocument(doc3_rpath, 'File', data_dict, 0)
        proxy_list4 = self.tool.listContent(folder_rpath)
        self.assertEquals(len(proxy_list3) + 1, len(proxy_list4))


    def testPublishApproveUnpublishDocument(self):
        folder_rpath = 'workspaces'
        sections_rpath = 'sections'
        data_dict = {'Title': "The report from Monday meeting",
                     'Description': "Another boring report",
                     }
        doc1_rpath = self.tool.createDocument('File', data_dict, folder_rpath, 0)
        doc1_id = self.portal.restrictedTraverse(doc1_rpath).getId()
        data_dict = {'Title': "Climate warning!",
                     'Description': "Consumers should make the difference",
                     }
        doc2_rpath = self.tool.createDocument('File', data_dict, folder_rpath, 0)
        doc2_id = self.portal.restrictedTraverse(doc2_rpath).getId()

        proxy_list1 = self.tool.listContent(sections_rpath)
        #print "proxy_list1 = %s" % proxy_list1
        self.tool.publishDocument(doc1_rpath,
                                  {'sections': ''})
        proxy_list2 = self.tool.listContent(sections_rpath)
        #print "proxy_list2 = %s" % proxy_list2
        doc1_state = self.tool.getDocumentState(os.path.join(sections_rpath,
                                                             doc1_id))
        self.assertEquals(doc1_state, 'published')

        self.tool.publishDocument(doc2_rpath,
                                  {'sections': ''},
                                  wait_for_approval=True)
        proxy_list3 = self.tool.listContent(sections_rpath)
        #print "proxy_list3 = %s" % proxy_list3
        doc2_state = self.tool.getDocumentState(os.path.join(sections_rpath,
                                                             doc2_id))
        self.assertEquals(doc2_state, 'pending')
        self.tool.acceptDocument(os.path.join(sections_rpath,
                                              doc2_id))
        doc2_state = self.tool.getDocumentState(os.path.join(sections_rpath,
                                                             doc2_id))
        self.assertEquals(doc2_state, 'published')
        proxy_list4 = self.tool.listContent(sections_rpath)
        self.tool.unpublishDocument(os.path.join(sections_rpath,
                                                 doc2_id))
        proxy_list5 = self.tool.listContent(sections_rpath)
        self.assertEquals(len(proxy_list4) - 1, len(proxy_list5))


    def testGetDocumentArchivedRevisionsUrls(self):
        wftool = self.portal.portal_workflow
        folder_rpath = 'workspaces'
        sections_rpath = 'sections'
        data_dict = {'Title': "The report from Monday meeting",
                     'Description': "Another boring report",
                     }
        tool = self.tool
        doc_rpath = tool.createDocument('File', data_dict, folder_rpath, 0)
        proxy = self.portal.restrictedTraverse(doc_rpath)

        archived = [d for d in proxy.getArchivedInfos() if d['is_frozen']]
        self.assertEquals(len(archived), 0)

        folder = proxy.aq_inner.aq_parent
        comments = 'checkout'
        newid = wftool.findNewId(folder, proxy.getId())
        wftool.doActionFor(proxy, 'checkout_draft',
                           dest_container=folder,
                           initial_transition='checkout_draft_in',
                           comment=comments)

        draft = getattr(folder, newid)
        locked_ob = draft.getLockedObjectFromDraft()

        data_dict['Description'] = 'Revisions test'
        doc = draft.getContent()
        doc.edit(proxy=draft, **data_dict)

        newid = locked_ob.getId()
        comments = 'checkin'
        wftool.doActionFor(draft, 'checkin_draft',
                           dest_container=folder,
                           dest_objects=[locked_ob],
                           checkin_transition="unlock",
                           comment=comments)

        archived = [d for d in proxy.getArchivedInfos() if d['is_frozen']]
        self.assertEquals(len(archived), 1)

        self.assertEquals(proxy.getContent().Description(),
                          data_dict['Description'])



def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ProductTestCase))
    return suite

if __name__ == '__main__':
    framework(descriptions=1, verbosity=2)

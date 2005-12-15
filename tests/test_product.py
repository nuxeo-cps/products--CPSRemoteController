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

import os

from zLOG import LOG, TRACE, DEBUG, INFO, PROBLEM, ERROR

import unittest

from CPSRemoteControllerTestCase import CPSRemoteControllerTestCase
from Products.CPSDefault.tests.CPSTestCase import MANAGER_ID
from Products.CMFCore.utils import getToolByName
from AccessControl import Unauthorized


class ProductTestCase(CPSRemoteControllerTestCase):

    def setUp(self):
        CPSRemoteControllerTestCase.setUp(self)

        #self.printLogErrors(TRACE)
        #self.printLogErrors(INFO)
        #self.printLogErrors(ERROR)


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
        self.assert_(isinstance(roles, list))
        # check anonymous access
        self.logout()
        self.assertRaises(Unauthorized, self.tool.getRoles, MANAGER_ID)


    def testGetLocalRoles(self):
        for folder_rpath in ('workspaces', 'sections'):
            roles = self.tool.getLocalRoles(MANAGER_ID, folder_rpath)
            self.assert_(isinstance(roles, list))

        # try to get local roles for different member then ourselves
        self.assertRaises(Unauthorized,
                          self.tool.getLocalRoles, 'dummy', 'sections')

        # check anonymous access
        self.logout()
        self.assertRaises(Unauthorized,
                          self.tool.getLocalRoles, MANAGER_ID, 'sections')


    def testListContent(self):
        workspaces = self.portal.workspaces
        sections = self.portal.sections
        workspaces.invokeFactory('Workspace', 'ws1')
        workspaces.invokeFactory('Workspace', 'ws2')
        rpaths = self.tool.listContent('workspaces')
        self.assertEquals(rpaths,
                          ['workspaces/members',
                           'workspaces/ws1',
                           'workspaces/ws2',
                           ])


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


    def testUnlockDocument(self):
        folder_rpath = 'workspaces'
        proxy_list1 = self.tool.listContent(folder_rpath)
        data_dict = {'Title': "The report from Monday meeting",
                     'Description': "Another boring report",
                     }
        doc_rpath = self.tool.createDocument('File', data_dict,
                                             folder_rpath, 0)
        self.failIf(self.tool.isDocumentLocked(doc_rpath))
        lock_tocken = self.tool.lockDocument(doc_rpath)

        # lock_token is present
        self.tool.unlockDocument(doc_rpath, lock_tocken)
        self.failIf(self.tool.isDocumentLocked(doc_rpath))

        self.tool.lockDocument(doc_rpath)
        self.assert_(self.tool.isDocumentLocked(doc_rpath))

        # lock_token is missed
        self.tool.unlockDocument(doc_rpath)
        self.failIf(self.tool.isDocumentLocked(doc_rpath))


    def testEditOrCreateDocument(self):
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
        self.assert_(doc3_returned_rpath in proxy_list4, doc3_returned_rpath)
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


    def testUnpublishDocumentsInSection(self):
        portal = self.portal
        wftool = portal.portal_workflow
        rctool = self.tool
        folder_rpath = 'workspaces'
        sections_rpath = 'sections'
        data_dict = {'Title': "The report from Monday meeting",
                     'Description': "Another boring report",
                     }
        doc1_rpath = rctool.createDocument('File', data_dict, folder_rpath, 0)
        doc1 = portal.restrictedTraverse(doc1_rpath)

        data_dict = {'Title': "Climate warning!",
                     'Description': "Consumers should make the difference",
                     }
        doc2_rpath = rctool.createDocument('File', data_dict, folder_rpath, 0)
        doc2 = portal.restrictedTraverse(doc2_rpath)

        rctool.publishDocument(doc1_rpath, {'sections': ''})
        rctool.publishDocument(doc2_rpath, {'sections': ''})

        # check that method unpublishes documents only in Sections
        self.assertRaises(TypeError,
                          rctool.unpublishDocumentsInSection, 'workspaces')

        self.assertEqual(len(portal.sections.contentValues()), 2)

        # check that documents in workspaces get 'unpublish' action recorded
        # into their workflow history after we made call to unpublish all
        # documents from section
        for obj in doc1, doc2:
            wfevents = wftool.getFullHistoryOf(obj)
            unpublished = [event for event in wfevents
                           if event.get('action') == 'unpublish']
            self.failIf(unpublished)
        rctool.unpublishDocumentsInSection('sections')
        for obj in doc1, doc2:
            wfevents = wftool.getFullHistoryOf(obj)
            unpublished = [event for event in wfevents
                           if event.get('action') == 'unpublish']
            self.assert_(unpublished)

        self.assertEqual(len(portal.sections.contentValues()), 0)

    def testUnpublishDocumentsInSectionWithSubmittedDocument(self):
        portal = self.portal
        wftool = portal.portal_workflow
        rctool = self.tool
        folder_rpath = 'workspaces'
        sections_rpath = 'sections'
        data_dict = {'Title': 'doc1',
                     'Description': 'Another boring report',
                     }
        doc1_rpath = rctool.createDocument('File', data_dict, folder_rpath, 0)

        data_dict = {'Title': 'doc2',
                     'Description': 'Consumers should make the difference',
                     }
        doc2_rpath = rctool.createDocument('File', data_dict, folder_rpath, 0)
        doc2 = portal.restrictedTraverse(doc2_rpath)

        # publish
        rctool.publishDocument(doc1_rpath, {'sections': ''})
        # submit
        rctool.publishDocument(doc2_rpath, {'sections': ''},
                               wait_for_approval=True)
        doc1_sec = portal.restrictedTraverse('sections/doc1')
        doc2_sec = portal.restrictedTraverse('sections/doc2')

        self.assertEqual(len(portal.sections.contentValues()), 2)
        self.assertEqual(wftool.getInfoFor(doc1_sec, 'review_state', None),
                         'published')
        self.assertEqual(wftool.getInfoFor(doc2_sec, 'review_state', None),
                         'pending')
        rctool.unpublishDocumentsInSection('sections')
        self.assertEqual(len(portal.sections.contentValues()), 0)

        wfevents = wftool.getFullHistoryOf(doc2)
        reject_events = [event for event in wfevents
                         if event.get('action') == 'reject']
        comment = reject_events[0]['comments']
        self.assertEqual(comment, 'rejected due to section emptying')

    def testGetDocumentArchivedRevisionsInfo(self):
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

        revs_info = tool.getDocumentArchivedRevisionsInfo(doc_rpath)
        self.assertEquals(len(revs_info), 1)

        self.assertEquals(proxy.getContent().Description(),
                          data_dict['Description'])


    def testGetDocumentHistory(self):
        wftool = self.portal.portal_workflow
        folder_rpath = 'workspaces'
        sections_rpath = 'sections'
        data_dict = {'Title': "The report from Monday meeting",
                     'Description': "Another boring report",
                     }
        tool = self.tool
        doc_rpath = tool.createDocument('File', data_dict, folder_rpath, 0)
        proxy = self.portal.restrictedTraverse(doc_rpath)

        folder = proxy.aq_inner.aq_parent

        for i in range(4):
            comments = 'checkout' + str(i)
            newid = wftool.findNewId(folder, proxy.getId())
            wftool.doActionFor(proxy, 'checkout_draft',
                               dest_container=folder,
                               initial_transition='checkout_draft_in',
                               comment=comments)

            draft = getattr(folder, newid)
            locked_ob = draft.getLockedObjectFromDraft()

            newid = locked_ob.getId()
            comments = 'checkin' + str(i)
            wftool.doActionFor(draft, 'checkin_draft',
                               dest_container=folder,
                               dest_objects=[locked_ob],
                               checkin_transition="unlock",
                               comment=comments)

        # check the actions quantity:
        # 1 create + 1 modify + 4 checkout + 4 checkin
        history = tool.getDocumentHistory(doc_rpath)
        self.assertEquals(len(history), 10)

    def testAddAndDeleteMember(self):
        tool = self.tool
        mtool = getToolByName(tool, 'portal_membership')
        userid = 'randomuser001'
        passwd = '%s%s' % (userid, userid, )
        firstName = 'Random'
        lastName = 'User'
        email = '%s@somewhere.com' % userid
        tool.addMember(userid, passwd, email=email,
            firstName= firstName, lastName=lastName)
        user = mtool.getMemberById(userid)
        self.failIf((user is None))
        tool.deleteMembers(userid)
        user = mtool.getMemberById(userid)
        self.failUnless((user is None))

    def test_getProductVersion(self):
        from CPSUtil.integration import ProductError
        self.assert_(self.tool.getProductVersion('CPSUtil'))
        self.assert_(self.tool.getProductVersion('CPSRemoteController'))

    def testCreateAndDeleteDocumentUnicodeFeed(self):
        folder_rpath = u'workspaces'
        proxy_list1 = self.tool.listContent(folder_rpath)
        data_dict = {'Title': u"The report from Monday meeting",
                     'Description': u"Another boring report",
                     }
        doc_rpath = self.tool.createDocument('File', data_dict, folder_rpath, 0)
        proxy_list2 = self.tool.listContent(folder_rpath)
        self.assertEquals(len(proxy_list1) + 1, len(proxy_list2))
        self.assert_(doc_rpath in proxy_list2)

        self.tool.deleteDocument(doc_rpath)
        proxy_list3 = self.tool.listContent(folder_rpath)
        self.assertEquals(len(proxy_list1), len(proxy_list3))
        self.failIf(doc_rpath in proxy_list3)

    def testgetSectionsTree(self):
        tree = self.tool.getSectionsTree()
        self.assert_(len(tree), 1)
        self.assertEquals(tree[0]['id'], 'sections')

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ProductTestCase))
    return suite

if __name__ == '__main__':
    framework(descriptions=1, verbosity=2)

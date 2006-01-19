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
import unittest

from zLOG import LOG, TRACE, DEBUG, INFO, PROBLEM, ERROR
from CPSRemoteControllerTestCase import CPSRemoteControllerTestCase
from Products.CPSDefault.tests.CPSTestCase import MANAGER_ID
from Products.CMFCore.utils import getToolByName
from Products.CPSCore.EventServiceTool import getEventService
from Products.CPSRemoteController.RemoteControllerTool import \
     EVENT_CHANGE_DOCUMENT_POSITION
from OFS.Folder import Folder
from AccessControl import Unauthorized
from webdav.LockItem import LockItem

class DummySubscriber(Folder):
    def notify_event(self, event_type, obj, info):
        self.event_type = event_type
        self.obj = obj
        self.info = info


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
        self.assertEquals(rpaths, ['workspaces/ws1', 'workspaces/ws2',])


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


    def testEditOrCreateDocumentUnsupposedBehavior(self):
        # Check that if we want to create Document in workspace and pass as
        # 'rpath', for example, 'workspaces/test' path, document will be
        # created in one level up - i.e. in 'workspaces'
        # This may be considered as inconsistent behaviour and require changes
        # to 'editOrCreateDocument' method.
        portal = self.portal
        rctool = self.tool
        wftool = getToolByName(portal, 'portal_workflow')
        kw = {'Title': 'Title',
              'Description': 'Description',
              }
        wftool.invokeFactoryFor(portal.workspaces, 'Workspace', 'test', **kw)
        ws1 = getattr(portal.workspaces, 'test')

        # we want to create document under 'workspaces/test'.
        # to create it really there we need append bogus document id to rpath,
        # like 'workspaces/test/doc1', that will be never actually used, as id
        # will be generated from Title in doc_def.
        doc_def = {'Title': 'doctitle',
                   'Description': 'docdescription',
                   }
        rpath = rctool.editOrCreateDocument('workspaces/test',
                                            'Document', doc_def)

        # document was not created under 'workspaces/test'
        self.failIf(ws1.contentValues())

        # but under 'workspaces'
        self.assert_('doctitle' in portal.workspaces.objectIds())

        proxy = getattr(portal.workspaces, 'doctitle')
        doc = proxy.getContent()
        self.assertEqual(doc.Title(), doc_def['Title'])
        self.assertEqual(doc.Description(), doc_def['Description'])


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

    def testGetProductVersion(self):
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
        self.assertEquals(tree[0]['can_publish'], True)

    def testGetPublishedOrPendingDocuments(self):
        portal = self.portal
        rctool = self.tool
        wftool = getToolByName(portal, 'portal_workflow')
        utool = getToolByName(portal, 'portal_url')

        kw = {'Title': 'Title',
              'Description': 'Description',
              }
        wftool.invokeFactoryFor(portal.sections, 'Section', 'test', **kw)
        s1 = getattr(portal.sections, 'test')
        wftool.invokeFactoryFor(portal.sections, 'Section', 'test1', **kw)
        s2 = getattr(portal.sections, 'test1')

        section_rpath = utool.getRelativeUrl(portal.sections)
        s1_rpath = utool.getRelativeUrl(s1)
        s2_rpath = utool.getRelativeUrl(s2)

        wftool.invokeFactoryFor(portal.workspaces, 'Document', 'doc', **kw)
        ws_doc = getattr(portal.workspaces, 'doc')

        # publish to 'sections'
        wftool.doActionFor(ws_doc, 'copy_submit',
                           dest_container=section_rpath,
                           initial_transition='publish')
        # submit to 'sections/test'
        wftool.doActionFor(ws_doc, 'copy_submit',
                           dest_container=s1_rpath,
                           initial_transition='submit')
        # publish to 'sections/test1'
        wftool.doActionFor(ws_doc, 'copy_submit',
                           dest_container=s2_rpath,
                           initial_transition='publish')
        # unpublish 'sections/test1/doc'
        sec_doc = portal.restrictedTraverse('sections/test1/doc')
        wftool.doActionFor(sec_doc, 'unpublish')

        rpaths = rctool.getPublishedOrPendingDocuments('workspaces/doc')
        # check that we get only existing documents, and not all 'pending'
        # or 'published' items from workflow history
        self.assertEqual(len(rpaths), 2)
        results = (('sections/test/doc', 'pending'),
                   ('sections/doc', 'published'),
                   )
        for rpath, review_state in rpaths:
            self.assert_((rpath, review_state) in results)

    def testChangeDocumentPosition(self):
        portal = self.portal
        rctool = self.tool
        wftool = getToolByName(portal, 'portal_workflow')
        utool = getToolByName(portal, 'portal_url')

        kw = {'Title': 'Title',
              'Description': 'Description',
              }
        wftool.invokeFactoryFor(portal.sections, 'Section', 'test', **kw)
        s1 = getattr(portal.sections, 'test')

        section_rpath = utool.getRelativeUrl(portal.sections)
        s1_rpath = utool.getRelativeUrl(s1)

        wftool.invokeFactoryFor(portal.workspaces, 'Document', 'doc', **kw)
        ws_doc = getattr(portal.workspaces, 'doc')

        # publish to 'sections'
        wftool.doActionFor(ws_doc, 'copy_submit',
                           dest_container=section_rpath,
                           initial_transition='publish')
        # we have tree:
        # sections
        #     test
        #     doc
        sections = portal.sections
        old_test_pos = sections.getObjectPosition('test')
        old_doc_pos = sections.getObjectPosition('doc')
        step = 1

        # sections.objectIds()->['.cps_workflow_configuration', 'test', 'doc']
        # check that 'test' has first position and 'doc' is second
        self.assertEqual(old_test_pos, 1)
        self.assertEqual(old_doc_pos, 2)

        rctool.changeDocumentPosition('sections/test', step)

        new_test_pos = sections.getObjectPosition('test')
        new_doc_pos = sections.getObjectPosition('doc')
        self.failIf(new_test_pos == old_test_pos)
        self.assertEqual(new_test_pos, 2)
        self.failIf(new_doc_pos == old_doc_pos)
        self.assertEqual(new_doc_pos, 1)

    def testChangeDocumentPositionSendsEvent(self):
        portal = self.portal
        rctool = self.tool
        wftool = getToolByName(portal, 'portal_workflow')
        utool = getToolByName(portal, 'portal_url')
        evtool = getEventService(portal)

        kw = {'Title': 'Title',
              'Description': 'Description',
              }
        wftool.invokeFactoryFor(portal.sections, 'Section', 'test', **kw)
        s1 = getattr(portal.sections, 'test')

        section_rpath = utool.getRelativeUrl(portal.sections)
        s1_rpath = utool.getRelativeUrl(s1)

        wftool.invokeFactoryFor(portal.workspaces, 'Document', 'doc', **kw)
        ws_doc = getattr(portal.workspaces, 'doc')

        # publish to 'sections'
        wftool.doActionFor(ws_doc, 'copy_submit',
                           dest_container=section_rpath,
                           initial_transition='publish')
        # we have tree:
        # sections
        #     test
        #     doc
        sections = portal.sections
        old_test_pos = sections.getObjectPosition('test')
        step = 1

        subscriber = DummySubscriber('foo')
        portal._setObject(subscriber.getId(), subscriber)

        evtool.manage_addSubscriber(
            subscriber=subscriber.getId(),
            action='event',
            meta_type='*',
            event_type='*',
            notification_type='synchronous',
            activated=True,
            )

        rctool.changeDocumentPosition('sections/test', step)

        new_test_pos = sections.getObjectPosition('test')
        self.assertEqual(subscriber.event_type, EVENT_CHANGE_DOCUMENT_POSITION)
        self.assertEqual(subscriber.info['rpath'], 'sections/test')
        self.assertEqual(subscriber.info['position_from'], old_test_pos)
        self.assertEqual(subscriber.info['position_to'], new_test_pos)


    def testEditDocument(self):
        portal = self.portal
        workspaces = portal.workspaces
        wftool = getToolByName(portal, 'portal_workflow')
        utool = getToolByName(portal, 'portal_url')
        rctool = self.tool

        folder_rpath = 'workspaces'
        data_kw = {'Title': 'title',
                   'Description': 'description',
                   }
        wftool.invokeFactoryFor(workspaces, 'File', 'testfile', **data_kw)
        proxy = getattr(workspaces, 'testfile')
        doc = proxy.getContent()
        rpath = utool.getRelativeUrl(proxy)
        self.assertEqual(doc.Title(), data_kw['Title'])
        self.assertEqual(doc.Description(), data_kw['Description'])

        doc_def = {'Title': 'newtitle',
                   'Description': 'newdescription',
                   }
        rctool.editDocument(rpath, doc_def)

        self.assertEqual(doc.Title(), doc_def['Title'])
        self.assertEqual(doc.Description(), doc_def['Description'])


    def testGetPublishedDocuments(self):
        portal = self.portal
        rctool = self.tool
        wftool = getToolByName(portal, 'portal_workflow')
        utool = getToolByName(portal, 'portal_url')

        kw = {'Title': 'Title',
              'Description': 'Description',
              }
        wftool.invokeFactoryFor(portal.sections, 'Section', 'test', **kw)
        s1 = getattr(portal.sections, 'test')
        wftool.invokeFactoryFor(portal.sections, 'Section', 'test1', **kw)
        s2 = getattr(portal.sections, 'test1')

        section_rpath = utool.getRelativeUrl(portal.sections)
        s1_rpath = utool.getRelativeUrl(s1)
        s2_rpath = utool.getRelativeUrl(s2)

        wftool.invokeFactoryFor(portal.workspaces, 'Document', 'doc', **kw)
        ws_doc = getattr(portal.workspaces, 'doc')
        # publish to 'sections'
        wftool.doActionFor(ws_doc, 'copy_submit',
                           dest_container=section_rpath,
                           initial_transition='publish')
        # submit to 'sections/test'
        wftool.doActionFor(ws_doc, 'copy_submit',
                           dest_container=s1_rpath,
                           initial_transition='submit')
        # publish to 'sections/test1'
        wftool.doActionFor(ws_doc, 'copy_submit',
                           dest_container=s2_rpath,
                           initial_transition='publish')
        # unpublish 'sections/test1/doc'
        sec_doc = portal.restrictedTraverse('sections/test1/doc')
        wftool.doActionFor(sec_doc, 'unpublish')

        rpaths = rctool.getPublishedDocuments('workspaces/doc')

        # check that we get only existing documents, and not all 'published'
        # items from workflow history
        self.assertEqual(len(rpaths), 1)
        results = ['sections/doc']
        for rpath in rpaths:
            self.assert_(rpath in results)


    def testGetDocumentLocksInfo(self):
        portal = self.portal
        rctool = self.tool
        wftool = getToolByName(portal, 'portal_workflow')
        utool = getToolByName(portal, 'portal_url')
        mtool = getToolByName(portal, 'portal_membership')

        kw = {'Title': 'Title',
              'Description': 'Description',
              }
        wftool.invokeFactoryFor(portal.workspaces, 'Document', 'doc', **kw)
        ws_doc = getattr(portal.workspaces, 'doc')
        ws_doc_rpath = utool.getRelativeUrl(ws_doc)

        member = portal.portal_membership.getAuthenticatedMember()
        user = member.getUser()

        lock_timeout = 'Seconds-120'

        lock1 = LockItem(user, user, timeout=lock_timeout)
        lock_token1 = lock1.getLockToken()
        ws_doc.wl_setLock(lock_token1, lock1)

        lock2 = LockItem(user, user, timeout=lock_timeout)
        lock_token2 = lock2.getLockToken()
        ws_doc.wl_setLock(lock_token2, lock2)

        locks_info = rctool.getDocumentLocksInfo(ws_doc_rpath)
        self.assertEqual(len(locks_info), 2)

        results = [(lock1.getOwner(), lock_token1),
                   (lock2.getOwner(), lock_token2),
                   ]
        for lock_owner, lock_token in locks_info:
            self.assert_((lock_owner, lock_token) in results)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ProductTestCase))
    return suite

if __name__ == '__main__':
    framework(descriptions=1, verbosity=2)

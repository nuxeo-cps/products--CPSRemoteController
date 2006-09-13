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

import doctest
import os, sys
import os.path
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

import unittest
from Testing import ZopeTestCase
import CPSRemoteControllerTestCase
from Products.CPSDefault.tests.CPSTestCase import MANAGER_ID

from Products.CPSRemoteController.RemoteControllerClient import \
    RequestDispatcher, RemoteControllerClient, CPSRemoteControllerClient
from Products.CPSRemoteController.RemoteControllerTool import toLatin9

def randomText(max_len=10):
    import random
    return ''.join(
        [chr(random.randint(32, 128)) for i in range(0, max_len)])

BaseClass = CPSRemoteControllerTestCase.CPSRemoteControllerTestCase

class RemoteControllerClientTC(CPSRemoteControllerTestCase.CPSRemoteControllerTestCase):

    def afterSetUp(self):
        self.login_id = MANAGER_ID
        self.login(self.login_id)
        self.portal.REQUEST.SESSION = {}
        self.portal.REQUEST['AUTHENTICATED_USER'] = self.login_id

        try:
            self.ws = self.portal.workspaces
        except AttributeError:
            self.ws = self.portal
        self.document_schemas = self.portal.getDocumentSchemas()
        self.document_types = self.portal.getDocumentTypes()
        self.tool = self.portal.portal_remote_controller

    def beforeTearDown(self):
        self.logout()

    def test_RequestDispatcher(self):
        rd = RequestDispatcher('http://server', 'method')

        # make sure RequestDispatcher calls the server
        from socket import gaierror
        self.assertRaises(gaierror, rd, 'arg1', 'arg2')

    def test_RemoteControllerClient(self):
        servers = {'1': 'http://1', '2': 'http://2'}
        rc = RemoteControllerClient(servers)

        from socket import error
        self.assertRaises(error, rc.server_method, 'arg1', 'arg2')

    def test_CPSRemoteControllerClient(self):
        rc = CPSRemoteControllerClient()
        rc.addServer('1', 'http://1')

        try:
            rc.server_method('arg1', 'arg2')
        except AttributeError:
            pass
        except:
            raise
        else:
            self.assert_(False)

        from socket import error
        try:
            rc.deleteDocument('arg1', 'arg2')
        except error:
            pass
        except:
            raise
        else:
            self.assert_(False)

    def test_SSL(self):
        rc = CPSRemoteControllerClient()
        rc.addServer('1', 'https://1')

        try:
            rc.server_method('arg1', 'arg2')
        except AttributeError:
            pass
        except:
            raise
        else:
            self.assert_(False)

        from socket import error
        try:
            rc.deleteDocument('arg1', 'arg2')
        except error:
            pass
        except:
            raise
        else:
            self.assert_(False)

    def test_RequestDispatcherSSL(self):
        rd = RequestDispatcher('https://server', 'method')

        # make sure RequestDispatcher calls the server
        from socket import gaierror
        self.assertRaises(gaierror, rd, 'arg1', 'arg2')

        # make sure the connector is doing ssl
        from httplib import HTTPS
        self.assert_(isinstance(rd._transport._getConnector('host'), HTTPS))

    def _restrictedTraverse(self, path):
        path = toLatin9(path)
        portal = self.portal
        return portal.restrictedTraverse(path)

    def _document_send(self, doc_def, portal_type):
        from Products.CPSUtil.xmlrpc import marshallDocument
        doc_def = marshallDocument(doc_def)
        # now calling RemoteController with the given def
        folder_rpath = '/portal/workspaces'
        path = self.tool.createDocument(portal_type, doc_def, folder_rpath,
                                        clean_files=False)
        # checking how the rpc-ed file looks
        return self._restrictedTraverse(path)

    def test_file_sending(self):
        from StringIO import StringIO
        from ZPublisher.HTTPRequest import FileUpload

        # creating doc
        self.ws.invokeFactory('File', 'file1')
        proxy = self.ws.file1

        # adding a file
        try:
            doc = proxy.getEditableContent()
        except AttributeError:
            doc = proxy

        class FieldStorage:
            def __init__(self, **kw):
                for k, v in kw.items():
                    setattr(self, k, v)

        text = randomText()
        file = StringIO(text)
        fs = FieldStorage(file=file, headers={"Content-Type": "text/html"},
            filename="filename")
        fileupload = FileUpload(fs)
        doc = proxy.getContent()
        doc_def = proxy.getTypeInfo().getDataModel(ob=doc)
        doc_def = doc_def.data
        doc_def['file'] = fileupload

        # sending and checking how the rpc-ed file looks
        rpced_doc = self._document_send(doc_def, proxy.portal_type)
        file = rpced_doc['file']
        self.assertEquals(file.read(), text)

    def test_link(self):
        self.ws.invokeFactory('Link', 'link1')
        proxy = self.ws.link1
        doc = proxy.getContent()
        doc_def = proxy.getTypeInfo().getDataModel(ob=doc)
        doc_def = doc_def.data
        doc_def['Relation'] = 'http://gooogooole.com'
        rpced_doc = self._document_send(doc_def, proxy.portal_type)
        doc_def = rpced_doc.getTypeInfo().getDataModel(ob=doc)
        doc_def = doc_def.data

    def test_document(self):
        self.ws.invokeFactory('Document', 'doc1')
        proxy = self.ws.doc1
        doc = proxy.getContent()
        doc_def = proxy.getTypeInfo().getDataModel(ob=doc)
        doc_def = doc_def.data
        value = "This is a new description"
        doc_def['Description'] = value
        rpced_doc = self._document_send(doc_def, proxy.portal_type)
        self.assertEquals(rpced_doc.getContent().Description(), value)

    def test_flexibleLayout(self):
        self.ws.invokeFactory('Link', 'link1')
        proxy = self.ws.link1
        self.assertEquals(self.tool._flexibleLayout(proxy), None)

        self.ws.invokeFactory('News Item', 'news1')
        proxy = self.ws.news1
        self.assertEquals(self.tool._flexibleLayout(proxy),
                          'newsitem_flexible')

    def test_flexibles(self):
        from DateTime import DateTime

        attached_file_and_link = {'Title': 'ok', 'photo': None, 'Source': '',
                                  'Language': 'en', 'attachedFile_f2': None,
                                  'Format': 'text/html',
                                  'ExpirationDate': None, 'Coverage': '',
                                  'ModificationDate':
                                   DateTime('2005/11/29 19:44:00 GMT+1'),
                                   'preview': None, 'attachedFile_f0':
                                   '', 'attachedFile_f1': '',
                                   'EffectiveDate': None, 'Rights': '',
                                   'photo_position': '', 'photo_subtitle': '',
                                   'photo_original': None, 'link_href_f0':
                                   'http://www.google.com', 'Description': '',
                                   'Contributors': [u'Manager CPS manager'],
                                   'link_description_f0': 'Google',
                                   'link_title_f0': 'Google',
                                   'Creator': 'manager', 'allow_discussion': 0,
                                   'Relation': '', 'CreationDate':
                                   DateTime('2005/11/29 19:40:34 GMT+1'),
                                   'Subject': []}

        rpced_doc = self._document_send(attached_file_and_link,
                                        'Flexible')
        self.assertEquals(rpced_doc.getContent().link_href_f0,
                          'http://www.google.com')


    def test_newsitems(self):
        from DateTime import DateTime

        news_with_links = {'link_title_1_f0': 'Google', 'Title': 'dd',
                           'photo': '', 'Source': '', 'EffectiveDate':
                            DateTime('2005/11/29 22:08:00 GMT+1'), 'Format':
                            'text/html', 'link_href_1_f0':
                            'http://www.google.com', 'content': 'gaphor',
                            'content_format': 'html', 'ExpirationDate': None,
                            'Coverage': '', 'ModificationDate':
                            DateTime('2005/11/29 22:14:41 GMT+1'), 'preview':
                            '', 'content_position': 'normal', 'Language':
                            'en', 'Rights': '', 'photo_position': 'left',
                            'photo_subtitle': '', 'photo_original': '',
                            'link_href_f0': 'http://www.google.com',
                            'Description': '', 'link_description_1_f0': '',
                            'Contributors': [u'admin'], 'link_description_f0':
                            '', 'link_title_f0': 'Google', 'Creator':
                            'admin', 'allow_discussion': 0, 'Relation': '',
                            'CreationDate': DateTime('2005/11/29 22:08:33 GMT+1'),
                            'Subject': [u'Arts']}

        rpced_doc = self._document_send(news_with_links, 'News Item')
        self.assertEquals(rpced_doc.getContent().link_href_f0,
                          'http://www.google.com')


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(RemoteControllerClientTC))
    suite.addTest(doctest.DocTestSuite('Products.CPSRemoteController.RemoteControllerClient'))
    return suite

if __name__ == '__main__':
    framework(descriptions=1, verbosity=2)

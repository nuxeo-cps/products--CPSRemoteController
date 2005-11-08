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
# $Id$
import doctest
import os
import unittest
from httplib import HTTP, HTTPS

from Products.CPSRemoteController.XMLRPCAuth import BasicAuthTransport, \
                                                    EncodedParser, \
                                                    EncodedUnmarshaller

if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))


class XMLRPCAuthTestCase(unittest.TestCase):

    def test_SSL_or_NOT(self):
        auth = BasicAuthTransport('john', 'doe', False)
        self.assert_(isinstance(auth._getConnector('host'), HTTP))

        auth = BasicAuthTransport('john', 'doe', True)
        self.assert_(isinstance(auth._getConnector('host'), HTTPS))


    def test_encoding_issues(self):
        # simulating a xml-rpc session
        unmarshaller = EncodedUnmarshaller()
        parser = EncodedParser(unmarshaller)

        feed = ("<?xml version='1.0'?>"
                "<methodResponse>"
                "<params>"
                "<param>"
                "<value><array><data>"
                "<value><string>ééééééééééé</string></value>"
                "<value><string>èèèèèèàççççç</string></value>"
                "</data></array></value>"
                "</param>"
                "</params>"
                "</methodResponse>")

        parser.feed(feed)
        import pdb;pdb.set_trace()
        result = unmarshaller.close()
        self.assertEquals(result, (['ééééééééééé', 'èèèèèèàççççç'],))


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(XMLRPCAuthTestCase))
    suite.addTest(doctest.DocTestSuite('Products.CPSRemoteController.XMLRPCAuth'))
    return suite

if __name__ == '__main__':
    framework(descriptions=1, verbosity=2)

#!/usr/bin/python
# -*- encoding: iso-8859-15 -*-
# Copyright (c) 2005 Nuxeo SARL <http://nuxeo.com>
# Authors : Thierry Delprat <td@nuxeo.com>
#           Tarek Ziadé <tz@nuxeo.com>
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
""" Add Basic Auth to XML-RPC transport

    Typical usage :

    >>> from xmlrpclib import ServerProxy
    >>> BAtransport = BasicAuthTransport('user', 'password')
    >>> Proxy = ServerProxy('http://url', transport=BAtransport)

"""
from xmlrpclib import SlowParser, Transport, ProtocolError, Unmarshaller, Fault
import string
from httplib import HTTP
from base64 import encodestring

# XXX need to use lxml here instead of old expat and marshall things
try:
    from xml.parsers import expat
    if not hasattr(expat, "ParserCreate"):
        raise ImportError

    class EncodedParser:
        def __init__(self, target, encoding="iso-8859-15"):
            self._parser = parser = expat.ParserCreate(encoding=encoding)
            self._target = target
            parser.StartElementHandler = target.start
            parser.EndElementHandler = target.end
            parser.CharacterDataHandler = target.data
            target.xml(encoding, None)
            self.encoding = encoding

        def feed(self, data):
            self._parser.Parse(data, 0)

        def close(self):
            self._parser.Parse('', 1)
            del self._target, self._parser

except ImportError:
    EncodedParser = SlowParser


class EncodedUnmarshaller(Unmarshaller):
    def __init__(self, encoding="iso-8859-15"):
        Unmarshaller.__init__(self)
        self._encoding = encoding

    def end_string(self, data):
        """ string mode """
        self.append(data)
        self._value = 0

    def close(self):
        def _encode(element):
            if isinstance(element, list):
                return map(_encode, element)
            if isinstance(element, unicode):
                return element.encode(self._encoding)
            else:
                return element

        if self._type is None or self._marks:
            raise ResponseError()

        if self._type == "fault":
            raise Fault(**self._stack[0])

        elements = map(_encode, self._stack)
        return tuple(elements)

    Unmarshaller.dispatch["string"] = end_string
    Unmarshaller.dispatch["name"] = end_string

class BasicAuthTransport(Transport):

    def __init__(self, username=None, password=None, is_ssl=False):
        self.username=username
        self.password=password
        self.verbose = 0
        self.is_ssl = is_ssl

    def _getConnector(self, host):
        if self.is_ssl:
            from httplib import HTTPS
            return HTTPS(host)
        else:
            return HTTP(host)

    def request(self, host, handler, request_body, verbose=0):
        """ issue XML-RPC request """
        self.verbose = verbose

        h = self._getConnector(host)
        h.putrequest("POST", handler)

        # required by HTTP/1.1
        h.putheader("Host", host)

        # required by XML-RPC
        h.putheader("User-Agent", self.user_agent)
        h.putheader("Content-Type", "text/xml; charset=iso-8859-15")
        h.putheader("Content-Length", str(len(request_body)))

        # basic auth
        if self.username is not None and self.password is not None:
            h.putheader("AUTHORIZATION", "Basic %s" % string.replace(
                    encodestring("%s:%s" % (self.username, self.password)),
                    "\012", ""))
        h.endheaders()
        if request_body:
            h.send(request_body)

        errcode, errmsg, headers = h.getreply()

        if errcode != 200:
            raise ProtocolError(
                host + handler,
                errcode, errmsg,
                headers
                )

        return self.parse_response(h.getfile())

    def getparser(self):
        unmarshaller = EncodedUnmarshaller()
        return EncodedParser(target=unmarshaller), unmarshaller

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
"""  Stateless Zope client for CPSRemoteController

    makes CPSRemoteController act as a server *and* a client

    This is similar to a regular XMLRPC client but it adds a
    mapping so you can call within CPS another CPS.

    In this example, we create a News item on 'server'
    .>> p = context.portal_remote_controller_client
    .>> p.add_server('server1',
        ... 'http://server:8080/cps/portal_remote_controller')
    .>> defs = {'Title': "The report from Monday meeting",
    ... 'Description': "Another report"}
    .>>  p.createDocument('News Item', defs, 'workspaces')

    TODO: add xmlrpc instrospection APIs to CPSRemoteController
    to avoid doing the mapping with the code
"""
__author__ =  "Tarek Ziadé <tz@nuxeo.com>"

from RemoteControllerTool import RemoteControllerTool
from XMLRPCAuth import BasicAuthTransport
from xmlrpclib import ServerProxy, Fault, ProtocolError
import socket
import re

class RequestDispatcher(object):
    """ this encapsulates a xmlrpc call """
    def __init__(self, server, method):
        self._user, self._password, self._server, self._ssl = \
            self._extractElements(server)
        self._method = method

        LOG('RemoteControllerCLient.dispatching init', DEBUG,
             'user: %s' % (self._user))
        LOG('RemoteControllerCLient.dispatching init', DEBUG,
             'server: %s' % (self._server))
        LOG('RemoteControllerCLient.dispatching init', DEBUG,
             'method: %s' % (self._method))

        self._transport = BasicAuthTransport(self._user, self._password,
                                             self._ssl)
        self._connector = ServerProxy(self._server, allow_none=True,
                                      transport=self._transport)

    def _extractElements(self, url):
        """ extracts from url user and password,

        >>> dp = RequestDispatcher('http://XX', 'XX')
        >>> dp._extractElements('http://manager:xxxxx@myserver.net:808/cps')
        ('manager', 'xxxxx', 'http://myserver.net:808/cps', False)
        >>> dp._extractElements('http://myserver.net:808/cps')
        (None, None, 'http://myserver.net:808/cps', False)
        >>> dp._extractElements('myserver.net:808/cps')
        (None, None, 'myserver.net:808/cps', False)
        >>> dp._extractElements('manager:xxxxx@myserver.net:808/cps')
        ('manager', 'xxxxx', 'myserver.net:808/cps', False)
        >>> dp = RequestDispatcher('https://XX', 'XX')
        >>> dp._extractElements('https://manager:xxxxx@myserver.net:808/cps')
        ('manager', 'xxxxx', 'https://myserver.net:808/cps', True)
        """
        pattern = r'(http://|https://)?(.*:.*@)?(.*)'
        groups = re.findall(pattern, url)
        groups = list(groups[0])
        header = groups[0]
        credentials = groups[1]
        if credentials == '':
            user, password = None, None
        else:
            user, password = groups[1][:-1].split(':')
        url = groups[2]
        is_ssl = groups[0] == 'https://'

        return user, password, '%s%s' % (header, url), is_ssl

    def __call__(self, *args):
        """ makes the call """
        return getattr(self._connector, self._method)(*args)

class RemoteControllerClient(object):

    def __init__(self, server_proxies={}):
        """ RemoteControllerClient can handle several servers
            _server_proxies is a dictionnary that contains
            n servers that can be called

        >>> servers = {
        ...   'server1': 'http://manager:xxxxx@myserver.net:8080/cps',
        ...   'server2': 'http://manager:xxxxx@myserver2.net:8080/cps'
        ... }
        >>> client = RemoteControllerClient(servers)
        """
        self._server_proxies = server_proxies
        self._current_server = None

    def setActiveServer(self, name):
        """ before a call is made, the client has to decide
        wich server it uses

        >>> client = RemoteControllerClient({'1': 'http://xxx'})
        >>> client.setActiveServer('1')
        >>> client._current_server
        '1'
        """
        # make sure it's in the list
        # XXX (using .keys() for PersistentMapping compatibility)
        if name in self._server_proxies.keys():
            self._current_server = name
        else:
            raise AttributeError('%s: no such server' % name)

    def getActiveServer(self, force=False):
        """ before a call is made, the client has to decide
        wich server it uses

        >>> client = RemoteControllerClient({'1': 'http://xxx'})

        force helps initializes active server state
        >>> client.getActiveServer(force=True)
        '1'

        or.. can be done manually
        >>> client.setActiveServer('1')
        >>> client.getActiveServer()
        '1'
        """
        if self._current_server is None and force:
            if len(self._server_proxies) > 0:
                self._current_server = self._server_proxies.keys()[0]
        return self._current_server

    def addServer(self, name, value):
        """ add a server

        >>> client = RemoteControllerClient({'1': 'http://xxx'})
        >>> client.addServer('2', 'http://xxx')
        >>> client.setActiveServer('2')
        >>> client.getActiveServer()
        '2'
        """
        self._server_proxies[name] = value

    def delServer(self, name):
        """ delete a server

        >>> client = RemoteControllerClient({'1': 'http://xxx'})
        >>> client.addServer('2', 'http://xxx')
        >>> client.setActiveServer('2')
        >>> client.getActiveServer()
        '2'
        >>> client.delServer('2')
        >>> client.setActiveServer('1')
        >>> client.getActiveServer()
        '1'
        >>> client._server_proxies
        {'1': 'http://xxx'}
        """
        # XXX (using .keys() for PersistentMapping compatibility)
        if name in self._server_proxies.keys():
            del self._server_proxies[name]
        if self._current_server == name:
            self._current_server = None

    def listServers(self):
        """ list all servers

        >>> client = RemoteControllerClient({'1': 'http://xxx'})
        >>> client.addServer('2', 'http://xxx')

        the list is sorted..
        >>> client.listServers()
        [('1', 'http://xxx'), ('2', 'http://xxx')]
        """
        servers = self._server_proxies.items()
        servers.sort()
        return servers

    def __getattr__(self, name):
        """ overrides the mapping to catch methods that can be
            called into the server
        """
        if name not in self.__dict__ and not name.startswith('_'):
            if self._current_server is None:
                self._current_server = self._server_proxies.keys()[0]
            url = self._server_proxies[self._current_server]
            LOG('RemoteControllerCLient.dispatching', DEBUG,
                'calling %s/%s' % (url, name))
            return RequestDispatcher(url, name)

        if name in self.__dict__:
            return self.__dict__[name]
        else:
            raise AttributeError(name)

# XXX starts zope specific code (might want to create another module)
import thread
from Products.CMFCore.utils import UniqueObject
from Globals import InitializeClass
from AccessControl import ClassSecurityInfo
from Products.CMFCore.permissions import View, ManagePortal
from OFS.Folder import Folder
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from ZODB.PersistentMapping import PersistentMapping
from zLOG import LOG, DEBUG

_lock = thread.allocate_lock()

class CPSRemoteControllerClient(UniqueObject, Folder):
    """ This is specialized to constraint calls to
        methods that exists in RemoteControllerTool
    """
    id = 'portal_remote_controller_client'
    meta_type = 'CPS Remote Controller Client Tool'
    security = ClassSecurityInfo()

    def __init__(self):
        """ uses RemoteControllerClient with a ZODB backend """
        self._rclient = RemoteControllerClient(PersistentMapping())

    #
    #  ZMI apis
    #
    security.declareProtected(ManagePortal, 'manage_listServers')
    manage_listServers = PageTemplateFile('www/list_servers.pt', globals())

    manage_options = (
            Folder.manage_options[:1] + (
            {'label': 'Distant servers managment', 'action':'manage_listServers'},) +
            Folder.manage_options[1:])

    security.declareProtected(ManagePortal, 'manage_addServer')
    def manage_addServer(self, name, value, REQUEST=None):
        """ add a server """
        name = name.strip()
        value = value.strip()
        if not value.endswith('portal_remote_controller'):
            if not value.endswith('/'):
                value = value + '/'
            value = value + 'portal_remote_controller'
        self.addServer(name, value)
        if REQUEST is not None:
            REQUEST.response.redirect('manage_listServers')

    security.declareProtected(ManagePortal, 'manage_delServer')
    def manage_delServer(self, name, REQUEST=None):
        """ add a server """
        self.delServer(name)
        if REQUEST is not None:
            REQUEST.response.redirect('manage_listServers')

    security.declareProtected(ManagePortal, 'manage_pingServer')
    def manage_pingServer(self, name, REQUEST=None):
        """ tests a server """
        LOG('RemoteControllerCLient.manage_pingServer', DEBUG,
            'pinging %s' % name)
        self.setActiveServer(name)
        try:
            psm = '%s says: CPSRemoteController v.%s | STATUS OK' % \
                (name, self._rclient.getVersion())
        except (socket.gaierror, socket.error), e:
            psm = '%s says: %s' % (name, str(e))
        except IOError, e:
            psm = '%s says: %s' % (name, str(e))
        except Fault:
            psm = '%s says: Zope error on my side' % name
        except ProtocolError:
            psm = '%s says: Protocol error' % name

        LOG('RemoteControllerCLient.manage_pingServer', DEBUG,
            'pinging result: %s' % psm)

        if REQUEST is not None:
            REQUEST.response.redirect('manage_listServers?psm=%s' % psm)
        else:
            return psm

    #
    #  apis
    #
    security.declareProtected(View, 'setActiveServer')
    def setActiveServer(self, name):
        """ before a call is made, the client has to decide
        wich server it uses
        """
        _lock.acquire()
        try:
            self._rclient.setActiveServer(name)
        finally:
            _lock.release()

    security.declareProtected(View, 'addServer')
    def addServer(self, name, value):
        """ add a server """
        _lock.acquire()
        try:
            self._rclient.addServer(name, value)
        finally:
            _lock.release()


    security.declareProtected(View, 'delServer')
    def delServer(self, name):
        """ delete a server """
        _lock.acquire()
        try:
            self._rclient.delServer(name)
        finally:
            _lock.release()

    security.declareProtected(View, 'listServers')
    def listServers(self):
        """ delete a server """
        return self._rclient.listServers()

    security.declareProtected(View, 'getActiveServer')
    def getActiveServer(self, force=False):
        """ returns the active server """
        return self._rclient.getActiveServer(force)

    def __getattr__(self, name):
        """ overrides the mapping to catch methods that can be
            called into the server.
        """
        if name not in self.__dict__  and not name.startswith('_'):
            if name in RemoteControllerTool.__dict__:
                rclient = self._rclient
                if rclient._current_server is None:
                    rclient._current_server = \
                        rclient._server_proxies.keys()[0]

                url = rclient._server_proxies[rclient._current_server]
                return RequestDispatcher(url, name)
            else:
                raise AttributeError('no xmlrpc method %s' % name)

        if name in self.__dict__:
            return self.__dict__[name]
        else:
            raise AttributeError()

    def callMethod(self, server_name, method_name, *args,**kw):
        """ sets the current server to server_name and call
        the method method_name, with the given args.
        This is made thread-safe to prevent a thread to change
        the current server, while another one is making a call
        """
        _lock.acquire()
        try:
            LOG('RemoteControllerCLient.callMethod', DEBUG,
                'method: %s, parameters args:%s kw:%s' % \
                 (method_name, str(args), str(kw)))
            self._rclient.setActiveServer(server_name)
            url = self._rclient._server_proxies[server_name]
            dispatcher = RequestDispatcher(url, method_name)
            return dispatcher(*args, **kw)
        finally:
            _lock.release()

InitializeClass(CPSRemoteControllerClient)

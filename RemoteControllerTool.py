# (C) Copyright 2005 Nuxeo SARL <http://nuxeo.com>
# Author:
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
"""
"""

from Globals import InitializeClass
from AccessControl import ClassSecurityInfo
from Products.CMFCore.permissions import ManagePortal, ChangePermissions, \
     AddPortalContent, ModifyPortalContent, View
from Products.CMFCore.utils import UniqueObject
from OFS.Folder import Folder

from zLOG import LOG, DEBUG


log_key = 'RemoteControllerTool'


class RemoteControllerTool(UniqueObject, Folder):
    """A tool providing an high-level API for manipulating documents.

    This tool is particularly useful for application which may use XML-RPC to
    communicate with CPS.

    To use those methods trough XML-RPC:
    $ python
    >>> from xmlrpclib import ServerProxy
    >>> p = ServerProxy('http://manager:xxxxx@myserver.net:8080/cps/portal_remote_controller')
    >>> p.listContent('workspaces/folder1')
    ['cps/workspaces/folder1', 'cps/workspaces/folder1/folder11', 'cps/workspaces/folder1/other_file']
    >>>
    """

    id = 'portal_remote_controller'
    meta_type = 'CPS Remote Controller Tool'
    security = ClassSecurityInfo()


    security.declareProtected(ChangePermissions, 'checkRoles')
    def getRoles(self, username):
        """Return the roles of the given user.
        """
        membersDirectory = self.portal_directories.members
        entry = membersDirectory.getEntry(username)
        roles = entry['roles']
        return roles


    security.declareProtected(ChangePermissions, 'getLocalRoles')
    def getLocalRoles(self, username, rpath):
        """Return the roles of the given user local to the specified context.
        """
        proxy = self.restrictedTraverse(rpath)
        local_roles_struct = proxy.getCPSLocalRoles()
        LOG(log_key, DEBUG, "local_roles = %s" % str(local_roles_struct[0]))
        user_local_roles = local_roles_struct[0]
        user_key = 'user:%s' % username
        if user_local_roles.get(user_key):
            return user_local_roles[user_key][0]['roles']
        else:
            return []


    security.declareProtected(ChangePermissions, 'checkPermission')
    def checkPermission(self, rpath, permission):
        """Check the given permission for the current user on the given context.
        """
        proxy = self.restrictedTraverse(rpath)
        # checkPermission returns True if allowed and None otherwise, which is
        # not consistent.
        allowed = self.portal_membership.checkPermission(permission, proxy)
        return allowed == True


    security.declareProtected(View, 'listContent')
    def listContent(self, rpath):
        """Return the list of document contained in the document specified by
        the given relative path.

        rpath is of the form "workspaces" or "workspaces/folder1".

        Examples:
        from xmlrpclib import ServerProxy
        p = ServerProxy('http://manager:xxxxx@myserver.net:8080/cps/portal_remote_controller')
        p.listContent('workspaces')
        p.listContent('workspaces/folder1')
        """
        proxy = self.restrictedTraverse(rpath)
        portal = self.portal_url.getPortalObject()
        brains = portal.search(query={'cps_filter_sets': 'searchable'},
                               folder_prefix=rpath)
        objects_paths = [x.getPath()[len(portal.getBaseUrl()):]
                         for x in brains]
        return objects_paths


    security.declareProtected(View, 'getDocumentState')
    def getDocumentState(self, rpath):
        """Return the workflow state of the document specified by the given
        relative path.

        rpath is of the form "workspaces/doc1" or "sections/doc2".
        """
        proxy = self.restrictedTraverse(rpath)
        state = proxy.getContentInfo(proxy=proxy, level=0)['review_state']
        return state


    security.declareProtected(View, 'getDocumentHistory')
    def getDocumentHistory(self, rpath):
        """Return the document history.
        """
        proxy = self.restrictedTraverse(rpath)
        history = proxy.getContentInfo(proxy=proxy, level=3)['history']
        LOG(log_key, DEBUG, "history = %s" % history)
        # A simplified value of the history so that it can be transported over
        # XML-RPC.
        history_simplified = {}
        for event in history:
            history_simplified[event['action']] = event['time_str']
        LOG(log_key, DEBUG, "history_simplified = %s" % history_simplified)
        return history_simplified


    security.declareProtected(View, 'getDocumentState')
    def getDocumentState(self, rpath):
        """Return the workflow state of the document specified by the given
        relative path.

        rpath is of the form "workspaces/doc1" or "sections/doc2".
        """
        proxy = self.restrictedTraverse(rpath)
        state = proxy.getContentInfo(proxy=proxy, level=0)['review_state']
        return state


    security.declareProtected(View, 'isDocumentLocked')
    def isDocumentLocked(self, rpath):
        """Return whether the document is locked (in the WebDAV sense) or not.
        """
        proxy = self.restrictedTraverse(rpath)
        return proxy.wl_isLocked()


##     security.declareProtected(ModifyPortalContent, 'lockDocument')
##     def lockDocument(self, rpath):
##         """Lock the document and return the associated lock token or False if
##         some problem arose.
##         """
##         proxy = self.restrictedTraverse(rpath)
##         if proxy.wl_isLocked():
##             return False
##         lock = proxy.wl_getLock(token)


##     security.declareProtected(ModifyPortalContent, 'unLockDocument')
##     def unLockDocument(self, rpath, lock):
##         """Un-lock the document.
##         """
##         proxy = self.restrictedTraverse(rpath)
##         if proxy.wl_isLocked():
##             return False
##         lock = self.wl_getLock(token)


    security.declareProtected(ModifyPortalContent, 'publishDocument')
    def publishDocument(self, document_rpath, section_rpath):
        """Publish the document specified by the given relative path.

        document_rpath is of the form "workspaces/doc1" or "workspaces/folder/doc2".
        section_rpath is of the form "sections/doc1" or "sections/folder/doc2".
        """
        wftool = self.portal_workflow
        proxy = self.restrictedTraverse(document_rpath)
        context = proxy
        workflow_action = 'copy_submit'
        transition = 'publish'
        comments = "Publishing done through the Remote Controller"
        allowed_transitions = wftool.getAllowedPublishingTransitions(context)
        LOG(log_key, DEBUG, "allowed_transitions = %s" % str(allowed_transitions))
        wftool.doActionFor(context, workflow_action,
                           dest_container=section_rpath,
                           initial_transition=transition,
                           comment=comments)


    security.declareProtected(ModifyPortalContent, 'unpublishDocument')
    def unpublishDocument(self, rpath):
        """Unpublish the document specified by the given relative path.

        rpath is of the form "sections/doc1" or "sections/folder/doc2".
        """
        wftool = self.portal_workflow
        proxy = self.restrictedTraverse(rpath)
        context = proxy
        workflow_action = 'unpublish'
        comments = "Un-publishing done through the Remote Controller"
        allowed_transitions = wftool.getAllowedPublishingTransitions(context)
        LOG(log_key, DEBUG, "allowed_transitions = %s" % str(allowed_transitions))
        wftool.doActionFor(context, workflow_action, comment=comments)


    security.declareProtected(ModifyPortalContent, 'changeDocumentOrder')
    def changeDocumentPosition(self, rpath, step):
        """Change the document position in its current folder.
        """
        proxy = self.restrictedTraverse(rpath)
        id = proxy.getId()
        context = proxy.aq_parent
        newpos = context.get_object_position(id) + step
        context.move_object_to_position(id, newpos)


    security.declareProtected(AddPortalContent, 'createDocument')
    def createDocument(self, portal_type, data_dict, folder_rpath, position=-1):
        """Create document with the given portal_type with data from the given
        data dictionary.

        Optional parameter position can be any value >= 0.

        Examples:
        from xmlrpclib import ServerProxy
        p = ServerProxy('http://manager:xxxxx@myserver.net:8080/cps/portal_remote_controller')

        p.createDocument('File',
        {'Title': "The report from Monday meeting", 'Description': "Another boring report"},
        'workspaces')
        p.createDocument('News Item',
        {'Title': "The company hires", 'Description': "The company goes well and
        hires"},
        'workspaces')

        p.createDocument('File',
        {'Title': "The report from Monday meeting", 'Description': "Another boring report"},
        'workspaces')
        p.createDocument('News Item',
        {'Title': "The company hires", 'Description': "The company goes well and
        hires"},
        'workspaces', 0)
        """
        # If no Title is given, the portal_type is used as a fallback title
        document_title = data_dict.get('Title', portal_type)
        folder_proxy = self.restrictedTraverse(folder_rpath)
        id = folder_proxy.computeId(compute_from=document_title)
        folder_proxy.invokeFactory(portal_type, id)
        doc_proxy = getattr(folder_proxy, id)
        doc = doc_proxy.getEditableContent()
        file = data_dict.get('file', None)
        if file is not None:
            LOG(log_key, DEBUG, "file = %s" % file)
            LOG(log_key, DEBUG, "file = %s" % str(file))
            LOG(log_key, DEBUG, "file.data = %s" % file.data)
            LOG(log_key, DEBUG, "file.data = %s" % str(file.data))
            #arg = xmlrpclib.Binary()
            #arg.decode(content)
        doc.edit(data_dict)
        if position >= 0:
            context = doc_proxy.aq_parent
            context.move_object_to_position(id, position)



    security.declareProtected(ModifyPortalContent, 'editDocument')
    def editDocument(self, rpath, data_dict={}):
        """Modify the specified document with data from the given
        data dictionary.
        """
        proxy = self.restrictedTraverse(rpath)
        doc = proxy.getEditableContent()
        doc.edit(data_dict)


InitializeClass(RemoteControllerTool)

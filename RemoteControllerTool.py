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

import types
import os.path
from Globals import InitializeClass
from AccessControl import ClassSecurityInfo
from Products.CMFCore.permissions import ManagePortal, ChangePermissions, \
     AddPortalContent, ModifyPortalContent, DeleteObjects, View
from Products.CMFCore.utils import UniqueObject, getToolByName
from OFS.Folder import Folder
from Acquisition import aq_parent, aq_inner
from OFS.Image import File
from xmlrpclib import Binary
from webdav.LockItem import LockItem
from Products.CPSUtil.id import generateId
from zLOG import LOG, DEBUG, ERROR, PROBLEM


glog_key = 'RemoteControllerTool'


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
        members_directory = self.portal_directories.members
        entry = members_directory.getEntry(username)
        roles = entry['roles']
        return roles


    security.declareProtected(ChangePermissions, 'getLocalRoles')
    def getLocalRoles(self, username, rpath):
        """Return the roles of the given user local to the specified context.
        """
        proxy = self.restrictedTraverse(rpath)
        local_roles_struct = proxy.getCPSLocalRoles()
        LOG(glog_key, DEBUG, "local_roles = %s" % str(local_roles_struct[0]))
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
        wtool = getToolByName(self, 'portal_workflow')
        state = wtool.getInfoFor(proxy, 'review_state', None)
        return state


    security.declareProtected(View, 'getDocumentHistory')
    def getDocumentHistory(self, rpath):
        """Return the document history.
        """
        proxy = self.restrictedTraverse(rpath)
        history = proxy.getContentInfo(proxy=proxy, level=3)['history']
        LOG(glog_key, DEBUG, "history = %s" % history)
        # A simplified value of the history so that it can be transported over
        # XML-RPC.
        history_simplified = {}
        for event in history:
            history_simplified[event['action']] = event['time_str']
        LOG(glog_key, DEBUG, "history_simplified = %s" % history_simplified)
        return history_simplified


    security.declareProtected(View, 'isDocumentLocked')
    def isDocumentLocked(self, rpath):
        """Return whether the document is locked (in the WebDAV sense) or not.
        """
        proxy = self.restrictedTraverse(rpath)
        return proxy.wl_isLocked()


    security.declareProtected(ModifyPortalContent, 'lockDocument')
    def lockDocument(self, rpath):
        """Lock the document and return the associated lock token or False if
        some problem arose.

        Example:
        >>> p.isDocumentLocked('workspaces/pr1')
        0
        >>> lock = p.lockDocument('workspaces/pr1')
        >>> p.isDocumentLocked('workspaces/pr1')
        1
        >>> p.unlockDocument('workspaces/pr1', lock)
        True
        >>> p.isDocumentLocked('workspaces/pr1')
        0
        """
        log_key = glog_key + ' lockDocument()'
        proxy = self.restrictedTraverse(rpath)
        if proxy.wl_isLocked():
            LOG(log_key, DEBUG, "document is already locked")
            return False
        member = self.portal_membership.getAuthenticatedMember()
        user = member.getUser()
        lock = LockItem(user, user)
        lock_token = lock.getLockToken()
        proxy.wl_setLock(lock_token, lock)
        if not proxy.wl_isLocked():
            LOG(log_key, ERROR,
                "setLock failed because document is currently not locked.")
            return False
        return lock_token


    security.declareProtected(ModifyPortalContent, 'unlockDocument')
    def unlockDocument(self, rpath, lock_token):
        """Un-lock the document and return True or False depending of the
        success of the operation.
        """
        proxy = self.restrictedTraverse(rpath)
        if not proxy.wl_isLocked():
            return False
        proxy.wl_delLock(lock_token)
        return True


    security.declareProtected(ModifyPortalContent, 'deleteDocumentLocks')
    def deleteDocumentLocks(self, rpath):
        """Delete all the locks owned by a user on the specified document.

        Calling this method should be avoided but might be useful when a client
        application crashes and loses all the user locks.
        """
        proxy = self.restrictedTraverse(rpath)
        if not proxy.wl_isLocked():
            return False
        member = self.portal_membership.getAuthenticatedMember()
        user = member.getUser()
        lock_mapping = proxy.wl_lockmapping(killinvalids=1)
        for lock_token, lock in proxy.wl_lockItems():
            if lock.getOwner() == user:
                del lock_mapping[lock_token]


    security.declareProtected(ModifyPortalContent, 'approveDocument')
    def acceptDocument(self, rpath, comments=""):
        """Approve the document specified by the given relative path.

        rpath is of the form "sections/doc1" or "sections/folder/doc2".
        """
        wftool = self.portal_workflow
        proxy = self.restrictedTraverse(rpath)
        context = proxy
        workflow_action = 'accept'
        allowed_transitions = wftool.getAllowedPublishingTransitions(context)
        LOG(glog_key, DEBUG, "allowed_transitions = %s" % str(allowed_transitions))
        wftool.doActionFor(context, workflow_action, comment=comments)


    security.declareProtected(ModifyPortalContent, 'publishDocument')
    def publishDocument(self, document_rpath, rpaths_to_publish,
                        wait_for_approval=False, comments=""):
        """Publish the document specified by the given relative path.

        document_rpath is of the form "workspaces/doc1" or "workspaces/folder/doc2".

        rpaths_to_publish is a dictionary. The dictionary keys are the rpath
        of where to publish the document. The rpath can be the rpath of a
        section or the rpath of a document. The dictionary values are either the
        empty string, "before", "after" or "replace".

        "replace" is to be used so that the published document really replaces
        another document, be it folder or document. The targeted document is
        deleted and the document to published is inserted at the position of the
        now deleted targeted document.
        """
        portal = self.portal_url.getPortalObject()
        portal_ppath = portal.getPhysicalPath()
        wftool = self.portal_workflow
        proxy = self.restrictedTraverse(document_rpath)
        document_id = proxy.getId()
        context = proxy
        workflow_action = 'copy_submit'
        if wait_for_approval:
            transition = 'submit'
        else:
            transition = 'publish'
        allowed_transitions = wftool.getAllowedPublishingTransitions(context)
        LOG(glog_key, DEBUG, "allowed_transitions = %s" % str(allowed_transitions))

        for target_rpath, placement in rpaths_to_publish.items():
            LOG(glog_key, DEBUG, "target_rpath / placement = %s / %s"
                % (target_rpath, placement))
            target_document = None
            try:
                object = portal.restrictedTraverse(target_rpath)
            except KeyError:
                LOG(glog_key, DEBUG, 'publishDocument no object with rpath = %s'
                    % target_rpath)
                continue
            if object.portal_type == 'Section':
                LOG(glog_key, DEBUG, "Target document is a section")
                section_rpath = target_rpath
                section = object
            else:
                LOG(glog_key, DEBUG,
                    "Target document is a document (not section)")
                try:
                    target_document = portal.restrictedTraverse(target_rpath)
                    target_document_ppath = target_document.getPhysicalPath()
                    rppath = target_document_ppath[len(portal_ppath):]
                    object = portal.restrictedTraverse(rppath[:-1])
                except KeyError:
                    LOG(glog_key, DEBUG, 'publishDocument no object with rpath = %s'
                        % target_rpath)
                    continue
                if object.portal_type == 'Section':
                    section_rpath = '/'.join(object.getPhysicalPath()[len(portal_ppath):])
                    section = object
                else:
                    LOG(glog_key, DEBUG, 'publishDocument no section with rpath = %s'
                        % target_rpath)
                    continue
            LOG(glog_key, DEBUG, "section_rpath = %s" % section_rpath)
            wftool.doActionFor(context, workflow_action,
                               dest_container=section_rpath,
                               initial_transition=transition,
                               comment=comments)
            # If the rpath provided was the one of a document then we will
            # consider the placement value to optionally move the document or
            # make it replace another one.
            if target_document is not None:
                target_id = target_document.getId()
                target_pos = section.getObjectPosition(target_id)
                newpos = None
                if placement == 'before':
                    newpos = target_pos
                elif placement == 'after':
                    newpos = target_pos + 1
                elif placement == 'replace':
                    newpos = target_pos
                    context = target_document
                    wftool.doActionFor(context, 'unpublish', comment=comments)
                LOG(glog_key, DEBUG, "publishDocument newpos = %s" % newpos)
                if newpos is not None:
                    section.moveObjectToPosition(document_id, newpos)


    security.declareProtected(ModifyPortalContent, 'unpublishDocument')
    def unpublishDocument(self, rpath, comments=""):
        """Unpublish the document specified by the given relative path.

        rpath is of the form "sections/doc1" or "sections/folder/doc2".
        """
        wftool = self.portal_workflow
        proxy = self.restrictedTraverse(rpath)
        context = proxy
        workflow_action = 'unpublish'
        allowed_transitions = wftool.getAllowedPublishingTransitions(context)
        LOG(glog_key, DEBUG, "allowed_transitions = %s" % str(allowed_transitions))
        wftool.doActionFor(context, workflow_action, comment=comments)


    security.declareProtected(ModifyPortalContent, 'changeDocumentOrder')
    def changeDocumentPosition(self, rpath, step):
        """Change the document position in its current folder.
        """
        proxy = self.restrictedTraverse(rpath)
        id = proxy.getId()
        context = aq_parent(aq_inner(proxy))
        newpos = context.getObjectPosition(id) + step
        context.moveObjectToPosition(id, newpos)


    security.declareProtected(AddPortalContent, 'createDocument')
    def createDocument(self, portal_type, doc_def, folder_rpath, position=-1):
        """Create document with the given portal_type with data from the given
        data dictionary.

        The method returns the rpath of the created document.

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

        from xmlrpclib import ServerProxy, Binary
        f = open('MyImage.png', 'r')
        binary = Binary(f.read())
        p.createDocument('File',
        {'Title': "The report from Monday meeting",
         'Description': "Another boring report"},
         'file_name': "MyImage.png",
         'file': binary,
         },
        'workspaces')
        p.createDocument('News Item',
        {'Title': "The company hires", 'Description': "The company goes well and
        hires"},
        'workspaces', 2)
        """
        LOG(glog_key, DEBUG, "editOrCreateDocument doc_def = %s" % str(doc_def))
        doc_def = toLatin9(doc_def)
        # If no Title is given, the portal_type is used as a fallback title
        document_title = doc_def.get('Title', portal_type)
        folder_proxy = self.restrictedTraverse(folder_rpath)
        id = folder_proxy.computeId(compute_from=document_title)
        folder_proxy.invokeFactory(portal_type, id)
        doc_proxy = getattr(folder_proxy, id)
        doc_rpath = os.path.join(folder_rpath, id)

        self._editDocument(doc_proxy, doc_def)

        if position >= 0:
            context = aq_parent(aq_inner(doc_proxy))
            context.moveObjectToPosition(id, position)

        return doc_rpath


    security.declareProtected(ModifyPortalContent, 'editDocument')
    def editDocument(self, rpath, doc_def={}):
        """Modify the specified document with data from the given
        data dictionary.
        """
        LOG(glog_key, DEBUG, "editDocument doc_def = %s" % str(doc_def))
        doc_def = toLatin9(doc_def)
        doc_proxy = self.restrictedTraverse(rpath)
        self._editDocument(doc_proxy, doc_def)


    security.declareProtected(AddPortalContent, 'editOrCreateDocument')
    def editOrCreateDocument(self, rpath, portal_type, doc_def, position=-1):
        """Create or edit a document with the given portal_type with data from
        the given data dictionary.

        The method returns the rpath of the created or edited document.

        Optional parameter position can be any value >= 0.
        """
        LOG(glog_key, DEBUG, "editOrCreateDocument doc_def = %s" % str(doc_def))
        doc_def = toLatin9(doc_def)
        try:
            proxy = self.restrictedTraverse(rpath)
            LOG(glog_key, DEBUG, "editOrCreateDocument document DOES exist")
        except KeyError:
            proxy = None
            LOG(glog_key, DEBUG, "editOrCreateDocument document does NOT exist")
        if proxy is not None and proxy.portal_type == portal_type:
            self._editDocument(proxy, doc_def)
            id = proxy.getId()
            utool = getToolByName(self, 'portal_url')
            doc_rpath = utool.getRelativeUrl(proxy)
        else:
            folder_rpath = '/'.join(rpath.split('/')[:-1])
            LOG(glog_key, DEBUG,
                "editOrCreateDocument folder_rpath = %s"% folder_rpath)
            id = self.createDocument(portal_type, doc_def, folder_rpath,
                                     position)
            doc_rpath = os.path.join(folder_rpath, id)
        return doc_rpath


    security.declarePrivate('_editDocument')
    def _editDocument(self, doc_proxy, doc_def):
        """Modify the document given its proxy.

        This method holds the special logic used to retrieve a potential file
        upload.
        """
        doc = doc_proxy.getEditableContent()

        doc_def = toLatin9(doc_def)

        # Getting and processing a potential file
        file = doc_def.get('file', None)
        DEFAULT_FILE_NAME = "Uploaded file"
        file_name = doc_def.get('file_name', DEFAULT_FILE_NAME)
        if file is not None:
            file = doc_def.get('file', None)
            binary = doc_def['file']
            if isinstance(binary, Binary):
                file_id = generateId(file_name, lower=True)
                doc_def['file'] = File(file_id, file_name, binary.data)
            else:
                # We don't know how to handle this case so we discard this item
                del doc_def['file']
        if file_name != DEFAULT_FILE_NAME:
            # We don't need this key anymore and we don't want the document to
            # be modified by it.
            del doc_def['file_name']

        doc.edit(doc_def)


    security.declareProtected(DeleteObjects, 'deleteDocument')
    def deleteDocument(self, rpath):
        """Delete the document with the given rpath.
        """
        proxy = self.restrictedTraverse(rpath)
        context = aq_parent(aq_inner(proxy))
        context.manage_delObjects([proxy.getId()])


    security.declareProtected(DeleteObjects, 'deleteDocuments')
    def deleteDocuments(self, rpaths):
        """Delete the documents corresponding to the given rpaths.
        """
        for rpath in rpaths:
            self.deleteDocument(rpath)


    security.declareProtected(View, 'getOriginalDocument')
    def getOriginalDocument(self, rpath):
        """Return the rpath original document that has been used to publish the
        document specified by the given path.

        rpath is of the form "sections/doc1".
        """
        return self._getOriginalOrPublishedDocuments(rpath, False)


    security.declareProtected(View, 'getOriginalDocument')
    def getPublishedDocuments(self, rpath):
        """Return a list of rpaths of documents which are publications of the
        document specified by the given path.

        rpath is of the form "workspaces/doc1".
        """
        return self._getOriginalOrPublishedDocuments(rpath)


    security.declarePrivate('_editDocument')
    def _getOriginalOrPublishedDocuments(self, rpath, published_documents=True):
        """Return rpaths of the documents, published or not, through the history
        of the document specified by the given path.
        """
        portal = self.portal_url.getPortalObject()
        portal_ppath = portal.getPhysicalPath()
        proxy = self.restrictedTraverse(rpath)
        states_info = proxy.getContentInfo(proxy=proxy, level=2)['states']
        LOG(glog_key, DEBUG, "states info = %s" % states_info)
        published_documents_rpaths = []
        for state_info in states_info:
            state = state_info['review_state']
            if (published_documents and state == 'published'
                or not published_documents and state != 'published'):
                published_proxy = state_info['proxy']
                published_proxy_path = '/'.join(
                    published_proxy.getPhysicalPath()[len(portal_ppath):])
                published_documents_rpaths.append(published_proxy_path)
        return published_documents_rpaths


InitializeClass(RemoteControllerTool)


def toLatin9(obj):
    if type(obj) == types.DictType:
        for k, v in obj.items():
            if type(v) == types.UnicodeType:
                v = _stringToLatin9(v)
                obj[k] = v
    elif type(obj) == types.UnicodeType:
        obj = _stringToLatin9(obj)
    return obj


def _stringToLatin9(s):
    if s is None:
        return None
    else:
        # Replace RIGHT SINGLE QUOTATION MARK (unicode only)
        # by the APOSTROPHE (ascii and latin1).
        # cf. http://www.cl.cam.ac.uk/~mgk25/ucs/quotes.html
        s = s.replace(u'\u2019', u'\u0027')
        #&#8217;
        return s.encode('iso-8859-15', 'ignore')


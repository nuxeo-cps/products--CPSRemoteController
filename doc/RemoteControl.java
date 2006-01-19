/*
 * (C) Copyright 2002-2006 Nuxeo SAS <http://nuxeo.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License version 2 as published
 * by the Free Software Foundation.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA
 * 02111-1307, USA.
 *
 * $Id$
 */

import java.io.IOException;
import java.net.MalformedURLException;
import java.net.URL;

import java.util.List;
import java.util.HashMap;
import java.util.Vector;

import org.apache.xmlrpc.XmlRpc;
import org.apache.xmlrpc.XmlRpcClient;
import org.apache.xmlrpc.XmlRpcException;

public class RemoteControl {

	private XmlRpcClient client;

	static {
		XmlRpc.setEncoding("UTF-8");
	}

	public RemoteControl(String url) throws MalformedURLException {
		this(new URL(url));
	}

	public RemoteControl(URL url) {
		client = new XmlRpcClient(url);
		client.setBasicAuthentication("manager", "xxx");
	}

	// ------------------- XMLRPC API -------------------

	public List listContent(String docRelativePath)
        throws XmlRpcException, IOException {
	    Vector params = new Vector();
	    params.addElement(docRelativePath);
        System.out.println("Executing RPC method listContent() " + params);
        return (List) client.execute("listContent", params);
	}

    public Object getDocumentState(String docRelativePath)
        throws XmlRpcException, IOException {
        Vector params = new Vector();
        params.addElement(docRelativePath);
        System.out.println("getDocumentState() " + params);
        return client.execute("getDocumentState", params);
    }

    public String createDocument(String type, String folderRelPath,
                                 Object docMap, int position)
        throws XmlRpcException, IOException {
        Vector params = new Vector();
        params.addElement(type);
        params.addElement(docMap);
        params.addElement(folderRelPath);
        params.addElement(new Integer(position));
        System.out.println("createDocument() " + params);
        return (String) client.execute("createDocument", params);
    }

	// --------------------------------------------------

    /**
     * The method in charge of analyzing the parameters given to the program and
     * executing the corresponding actions.
     */
    public static void main(String[] args) {
        try {
            String remoteControllerAddr =
                "http://myserver.net:8080/cps/portal_remote_controller";
            RemoteControl ctrl = new RemoteControl(remoteControllerAddr);

            List list = ctrl.listContent("workspaces");
            System.out.println("\nWorkspaces content: " + list);

            Object res;
            HashMap metadata = new HashMap();
            metadata.put("Title", "Test Document");
            metadata.put("Description", "Test Document Description");
            metadata.put("file", "Bla bla ...".getBytes());
            metadata.put("file_name", "test.txt");
            res = ctrl.createDocument("File", "workspaces", metadata, 0);
            System.out.println("\nDocument created: " + res);

            res = ctrl.getDocumentState("workspaces/test-document");
            System.out.println("\nDocument state: " + res);

        } catch (Exception ex) {
            System.out.println("main() " + ex);
            ex.printStackTrace();
        }
    }

}

#
#Copyright (C) 2011 by Bruno Harbulot
#
#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in
#all copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#THE SOFTWARE.
#-----------------------------------------------------------------------------
#
# Note that this is a simple web service built for demo purposes w.r.t.
# SlickGrid. Don't necessarily take it as an example of good practice for
# web/sql development.
#
# This may require Python 2.6 or above.


import BaseHTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler
import shutil
import urlparse
import sqlite3
import uuid
import json
import random
import string
from cStringIO import StringIO



db_conn = sqlite3.connect(":memory:")


class DynamicHttpRequestHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/dynamic"):
            self.process_dynamic_content(response_with_body=True)
        else:
            SimpleHTTPRequestHandler.do_GET(self)
    
    def do_HEAD(self):
        if self.path.startswith("/dynamic"):
            self.process_dynamic_content(response_with_body=False)
        else:
            SimpleHTTPRequestHandler.do_HEAD(self)
    
    def process_dynamic_content(self, response_with_body=True):
        if self.command in [ "GET", "HEAD" ]:
            parsed_url = urlparse.urlparse(self.path)
            query_dict = urlparse.parse_qs(parsed_url.query)
            
            try:
                count = int(query_dict.get('count',[''])[0])
            except ValueError:
                count = None
            try:
                offset = int(query_dict.get('start',[''])[0])
            except ValueError:
                offset = None
            
            order_by = ""
            
            sortcol = query_dict.get("sortcol",[""])[0]
            if sortcol in ["name", "colour"]:
                sortdir = query_dict.get("sortdir",[""])[0]
                sortdir = sortdir.upper()
                if not sortdir in ["ASC", "DESC"]:
                    sortdir = ""
                order_by = " ORDER BY %s %s " % (sortcol, sortdir)
            else:
                order_by = ""
            
            
            
            buffer = StringIO()
            cursor = db_conn.cursor()
            
            cursor.execute("BEGIN")
            cursor.execute("SELECT COUNT(id) FROM item")
            total_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT id, name, colour FROM item %s LIMIT ? OFFSET ?" % (order_by,), [ count, offset ])
            items = []
            for row in cursor:
                items.append({
                    "id": row[0],
                    "name": row[1] or '',
                    "colour": row[2] or ''
                })
            cursor.close()
            db_conn.commit()
            
            jsonp_callback = query_dict.get('callback',[None])[0]
            if jsonp_callback:
                response = "%s(%s)" % (jsonp_callback, json.dumps({'items': items, 'offset': offset, 'count': len(items), 'total': total_count}))
            else:
                response = json.dumps({'items': data, 'offset': offset, 'count': len(data), 'total': total_count})
            buffer.write(response)
            
            content_type = "text/plain"
            content_length = buffer.tell()
        else:
            buffer = None
        
        response_status = 200
        if buffer == None:
            content_type = "text/plain"
            buffer = StringIO()
            buffer.write("Not Found...\n")
            content_length = buffer.tell()
            response_status = 404
            
        self.send_response(response_status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(content_length))
        self.send_header("Cache-Control", 'no-cache')
        self.send_header("Expires", 'Fri, 01 Jan 1990 00:00:00 GMT')
        self.end_headers()
        if response_with_body:
            buffer.seek(0)
            shutil.copyfileobj(buffer, self.wfile)
        buffer.close()





if __name__ == '__main__':
    cursor = db_conn.cursor()
    cursor.execute("""CREATE TABLE item(
        id TEXT PRIMARY KEY,
        name TEXT,
        colour TEXT
    )""")
    query = "INSERT INTO item(id, name, colour) VALUES(?,?,?)"
    for _ in range(5000):
        cursor.execute(query, [ uuid.uuid4().hex,
                                ''.join(random.choice(string.ascii_uppercase) for _ in range(8)),
                                random.choice(["Red","Blue","Green","Yellow"]) ])

    cursor.close()
    db_conn.commit()
    BaseHTTPServer.test(DynamicHttpRequestHandler, BaseHTTPServer.HTTPServer)